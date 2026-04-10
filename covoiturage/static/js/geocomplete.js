/**
 * Simple autocomplete for location fields using Nominatim geocoding
 * Usage: new GeoComplete('id_field_name', '/geo/forward/')
 */
class GeoComplete {
  constructor(fieldId, geoForwardUrl = '/geo/forward/') {
    this.input = document.getElementById(fieldId);
    this.geoUrl = geoForwardUrl;
    this.dropdown = null;
    this.debounceTimer = null;
    this.selectedIndex = -1;
    
    if (!this.input) return;
    
    this.setupDropdown();
    this.attachEvents();
  }

  setupDropdown() {
    this.dropdown = document.createElement('div');
    this.dropdown.className = 'geo-dropdown';
    this.dropdown.style.display = 'none';
    this.input.parentNode.insertBefore(this.dropdown, this.input.nextSibling);
    
    const style = document.createElement('style');
    if (!document.getElementById('geo-style')) {
      style.id = 'geo-style';
      style.textContent = `
        .geo-dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          background: white;
          border: 2px solid #EBE5D9;
          border-top: none;
          border-radius: 0 0 8px 8px;
          max-height: 200px;
          overflow-y: auto;
          z-index: 1000;
          box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .geo-item {
          padding: 12px 15px;
          cursor: pointer;
          border-bottom: 1px solid #f0f0f0;
          font-size: 14px;
          transition: background 0.2s;
        }
        .geo-item:last-child {
          border-bottom: none;
        }
        .geo-item:hover,
        .geo-item.selected {
          background-color: #f5f0eb;
          color: #D95D39;
        }
        .geo-loading {
          padding: 12px 15px;
          color: #999;
          font-size: 13px;
        }
        .geo-error {
          padding: 12px 15px;
          color: #d32f2f;
          font-size: 13px;
        }
      `;
      document.head.appendChild(style);
    }
  }

  attachEvents() {
    this.input.addEventListener('input', () => this.onInput());
    this.input.addEventListener('keydown', (e) => this.onKeyDown(e));
    this.input.addEventListener('blur', () => setTimeout(() => this.hideDropdown(), 200));
    this.input.addEventListener('focus', () => {
      if (this.dropdown.innerHTML && this.input.value) this.dropdown.style.display = 'block';
    });
  }

  onInput() {
    const query = this.input.value.trim();
    clearTimeout(this.debounceTimer);
    
    if (query.length < 2) {
      this.hideDropdown();
      return;
    }

    this.debounceTimer = setTimeout(() => this.fetch(query), 300);
  }

  onKeyDown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.selectedIndex++;
      this.updateSelection();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.selectedIndex--;
      this.updateSelection();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const selected = this.dropdown.querySelector('.geo-item.selected');
      if (selected) {
        this.selectItem(selected);
      }
    } else if (e.key === 'Escape') {
      this.hideDropdown();
    }
  }

  updateSelection() {
    const items = this.dropdown.querySelectorAll('.geo-item');
    items.forEach((item, idx) => {
      item.classList.toggle('selected', idx === this.selectedIndex);
    });
  }

  async fetch(query) {
    this.dropdown.innerHTML = '<div class="geo-loading">⏳ Recherche...</div>';
    this.dropdown.style.display = 'block';

    try {
      const response = await fetch(`${this.geoUrl}?q=${encodeURIComponent(query)}`);
      const data = await response.json();

      if (data.error) {
        this.dropdown.innerHTML = '<div class="geo-error">Erreur de géocodage</div>';
        return;
      }

      if (!data.results || data.results.length === 0) {
        this.dropdown.innerHTML = '<div class="geo-loading">Aucun résultat</div>';
        return;
      }

      this.selectedIndex = -1;
      this.dropdown.innerHTML = data.results
        .map((loc, idx) => `
          <div class="geo-item" data-idx="${idx}" data-name="${this.escapeHtml(loc.display_name)}" data-lat="${loc.lat}" data-lon="${loc.lon}">
            ${this.escapeHtml(loc.display_name)}
          </div>
        `)
        .join('');

      this.dropdown.querySelectorAll('.geo-item').forEach(item => {
        item.addEventListener('click', () => this.selectItem(item));
        item.addEventListener('mouseover', () => {
          this.dropdown.querySelectorAll('.geo-item').forEach(i => i.classList.remove('selected'));
          item.classList.add('selected');
        });
      });
    } catch (err) {
      this.dropdown.innerHTML = '<div class="geo-error">Erreur réseau</div>';
    }
  }

  selectItem(item) {
    const name = item.dataset.name;
    this.input.value = name;
    this.hideDropdown();
    
    // Trigger change event for form handlers
    this.input.dispatchEvent(new Event('change', { bubbles: true }));
  }

  hideDropdown() {
    this.dropdown.style.display = 'none';
    this.selectedIndex = -1;
  }

  escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
  }
}

// Auto-init on specific fields when page loads
document.addEventListener('DOMContentLoaded', () => {
  const fields = ['id_ville_depart', 'id_lieu_ramassage', 'id_ville_arrivee'];
  fields.forEach(fieldId => {
    if (document.getElementById(fieldId)) {
      new GeoComplete(fieldId);
    }
  });
});

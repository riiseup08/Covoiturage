import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, Radius } from '../theme';

let RNDateTimePicker = null;
if (Platform.OS !== 'web') {
  try { RNDateTimePicker = require('@react-native-community/datetimepicker').default; } catch {}
}

/**
 * @param {object} props
 * @param {string} [props.label] - Label text above the picker
 * @param {string} [props.value] - ISO date string (or datetime-local string)
 * @param {(value: string) => void} props.onChange - Called with ISO date/datetime string
 * @param {'date'|'datetime'} [props.mode='datetime'] - Picker mode
 * @param {string} [props.placeholder] - Placeholder text when no date selected
 */
export default function DatePicker({ label, value, onChange, mode = 'datetime', placeholder }) {
  const [show, setShow] = useState(false);
  const [tempDate, setTempDate] = useState(value ? new Date(value) : new Date());

  const formatDisplay = (dateStr) => {
    if (!dateStr) return placeholder || '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    if (mode === 'date') {
      return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
    }
    return d.toLocaleDateString('fr-FR', {
      day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  };

  const toISOValue = (d) => {
    if (mode === 'date') {
      return d.toISOString().split('T')[0];
    }
    return d.toISOString().slice(0, 19);
  };

  // Web: use native HTML input
  if (Platform.OS === 'web') {
    const inputType = mode === 'date' ? 'date' : 'datetime-local';
    return (
      <View style={styles.wrapper}>
        {label ? <Text style={styles.label}>{label}</Text> : null}
        <input
          type={inputType}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          style={{
            borderWidth: 1.5,
            borderColor: Colors.border,
            borderRadius: Radius.md,
            padding: '12px 16px',
            fontSize: 15,
            color: Colors.text,
            backgroundColor: Colors.bgCard,
            minHeight: 48,
            width: '100%',
            boxSizing: 'border-box',
            borderStyle: 'solid',
          }}
        />
      </View>
    );
  }

  // Native: no picker library available, fall back to a formatted text input
  if (!RNDateTimePicker) {
    return (
      <View style={styles.wrapper}>
        {label ? <Text style={styles.label}>{label}</Text> : null}
        <TouchableOpacity style={styles.input}>
          <Text style={value ? styles.inputText : styles.placeholder}>
            {value ? formatDisplay(value) : placeholder || ''}
          </Text>
          <Ionicons name="calendar-outline" size={18} color={Colors.textMuted} />
        </TouchableOpacity>
      </View>
    );
  }

  // Native with picker
  const handleChange = (event, selectedDate) => {
    if (Platform.OS === 'android') {
      setShow(false);
      if (event.type === 'set' && selectedDate) {
        onChange(toISOValue(selectedDate));
      }
      return;
    }
    // iOS: picker stays open
    if (selectedDate) {
      setTempDate(selectedDate);
    }
  };

  const confirmIOS = () => {
    onChange(toISOValue(tempDate));
    setShow(false);
  };

  return (
    <View style={styles.wrapper}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <TouchableOpacity style={styles.input} onPress={() => setShow(true)} activeOpacity={0.7}>
        <Text style={value ? styles.inputText : styles.placeholder}>
          {value ? formatDisplay(value) : placeholder || ''}
        </Text>
        <Ionicons name="calendar-outline" size={18} color={Colors.textMuted} />
      </TouchableOpacity>

      {Platform.OS === 'android' && show && (
        <RNDateTimePicker
          value={value ? new Date(value) : new Date()}
          mode={mode === 'datetime' ? 'date' : mode}
          onChange={handleChange}
        />
      )}

      {Platform.OS === 'ios' && show && (
        <Modal transparent animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <TouchableOpacity onPress={() => setShow(false)}>
                  <Text style={styles.modalCancel}>Annuler</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={confirmIOS}>
                  <Text style={styles.modalDone}>OK</Text>
                </TouchableOpacity>
              </View>
              <RNDateTimePicker
                value={tempDate}
                mode={mode === 'datetime' ? 'datetime' : mode}
                display="spinner"
                onChange={handleChange}
              />
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { marginBottom: Spacing.md },
  label: { fontSize: 14, fontWeight: '600', color: Colors.text, marginBottom: Spacing.xs },
  input: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.md - 4,
    backgroundColor: Colors.bgCard,
    minHeight: 48,
  },
  inputText: { fontSize: 15, color: Colors.text },
  placeholder: { fontSize: 15, color: Colors.textMuted },
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  modalContent: {
    backgroundColor: Colors.bgCard,
    borderTopLeftRadius: Radius.xl,
    borderTopRightRadius: Radius.xl,
    paddingBottom: 30,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  modalCancel: { fontSize: 16, color: Colors.textMuted },
  modalDone: { fontSize: 16, fontWeight: '600', color: Colors.earth },
});

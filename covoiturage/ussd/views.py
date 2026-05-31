"""USSD webhook (Africa's Talking style) for feature-phone access.

The provider POSTs ``sessionId``, ``phoneNumber`` and ``text`` (the full chain of
user inputs joined by ``*``). We respond with plain text prefixed ``CON`` (more
input expected) or ``END`` (session over). All trip logic is delegated to the
shared ``services`` layer so behaviour matches web/API exactly.
"""

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from covoiturage.services import trips


def _con(text):
    return HttpResponse(f"CON {text}", content_type="text/plain")


def _end(text):
    return HttpResponse(f"END {text}", content_type="text/plain")


def _user_for_phone(phone):
    """Identify or lazily create a user keyed by phone (mirrors phone-auth flow)."""
    username = f"ussd_{phone.lstrip('+')}"
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    profile = user.profile
    if profile.phone != phone:
        profile.phone = phone
        profile.save(update_fields=["phone"])
    return user


def _parse_date(token):
    """Accept YYYY-MM-DD, DD/MM/YYYY, or 'demain'/'aujourd'hui'."""
    token = (token or "").strip().lower()
    if token in ("aujourd'hui", "aujourdhui", "1"):
        return timezone.now().date()
    if token in ("demain", "2"):
        return timezone.now().date() + timedelta(days=1)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m"):
        try:
            d = datetime.strptime(token, fmt).date()
            if fmt == "%d/%m":
                d = d.replace(year=timezone.now().year)
            return d
        except ValueError:
            continue
    return None


@csrf_exempt
def ussd_callback(request):
    if not getattr(settings, "USSD_ENABLED", False):
        return HttpResponseNotFound()
    if request.method != "POST":
        return _end("Méthode non supportée.")

    phone = (request.POST.get("phoneNumber") or "").strip()
    text = (request.POST.get("text") or "").strip()
    if not phone:
        return _end("Numéro manquant.")

    parts = text.split("*") if text else []

    # Main menu
    if not parts or parts == [""]:
        return _con(
            "Covoit.Africa\n"
            "1. Publier un trajet (conducteur)\n"
            "2. Chercher un trajet (passager)"
        )

    choice = parts[0]

    if choice == "1":
        return _handle_publish(phone, parts[1:])
    if choice == "2":
        return _handle_search(parts[1:])
    return _end("Choix invalide.")


def _handle_publish(phone, args):
    # args: [ville_depart, ville_arrivee, date, prix]
    prompts = [
        "Ville de départ:",
        "Ville d'arrivée:",
        "Date (JJ/MM/AAAA, 'demain'):",
        "Prix par place (FCFA):",
    ]
    if len(args) < len(prompts):
        return _con(prompts[len(args)])

    ville_depart, ville_arrivee, date_token, prix_token = args[:4]
    date = _parse_date(date_token)
    if date is None:
        return _end("Date invalide. Réessayez.")
    try:
        prix = int(prix_token)
    except ValueError:
        return _end("Prix invalide. Réessayez.")

    depart_dt = timezone.make_aware(datetime.combine(date, datetime.min.time()))
    user = _user_for_phone(phone)
    with transaction.atomic():
        trips.publish_voyage(
            user,
            ville_depart=ville_depart.strip(),
            ville_arrivee=ville_arrivee.strip(),
            date_depart=depart_dt,
            date_arrivee=depart_dt + timedelta(hours=4),
            prix_par_place=prix,
        )
    return _end(
        f"Trajet {ville_depart} -> {ville_arrivee} publié. "
        "Vous recevrez un SMS dès qu'un passager correspond."
    )


def _handle_search(args):
    # args: [ville_depart, ville_arrivee]
    prompts = ["Ville de départ:", "Ville d'arrivée:"]
    if len(args) < len(prompts):
        return _con(prompts[len(args)])

    ville_depart, ville_arrivee = args[:2]
    results = trips.search_voyages(
        {"ville_depart": ville_depart.strip(), "ville_arrivee": ville_arrivee.strip()}
    )[:5]
    if not results:
        return _end("Aucun trajet trouvé. Réessayez plus tard.")

    lines = ["Trajets trouvés:"]
    for v in results:
        lines.append(
            f"- {v.date_depart.strftime('%d/%m %H:%M')} {int(v.prix_par_place)}F "
            f"{v.conducteur.username}"
        )
    return _end("\n".join(lines))

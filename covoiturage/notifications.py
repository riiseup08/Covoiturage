"""
Notification helper functions for the Covoiturage app.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Notification, Voyage, Correspondance, Avis


def create_notification(user, notification_type, title, message, related_voyage=None, related_correspondance=None, related_avis=None, send_email=True):
    """
    Create a notification for a user and optionally send an email.
    
    Args:
        user: The User to notify
        notification_type: One of 'match', 'match_validated', 'match_refused', 'review', 'trip_reminder', 'trip_completed', 'message'
        title: Short title for the notification
        message: Detailed message
        related_voyage: Optional related Voyage object
        related_correspondance: Optional related Correspondance object
        related_avis: Optional related Avis object
        send_email: Whether to send an email notification (default True)
    
    Returns:
        The created Notification object
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_voyage=related_voyage,
        related_correspondance=related_correspondance,
        related_avis=related_avis,
    )
    
    if send_email and user.email:
        send_notification_email(user, notification)
    
    return notification


def send_notification_email(user, notification):
    """Send an email notification to the user."""
    subject = f"[Covoit.Africa] {notification.title}"
    email_message = f"""
Bonjour {user.username},

{notification.message}

Connectez-vous à votre compte pour plus de détails : {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'}

Cordialement,
L'équipe Covoit.Africa
"""
    try:
        send_mail(
            subject,
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception:
        # Silently fail if email can't be sent
        pass


def notify_new_match(correspondance):
    """Notify both driver and passenger when a new match is found."""
    # Notify driver
    create_notification(
        user=correspondance.voyage.conducteur,
        notification_type='match',
        title='Nouveau match trouvé !',
        message=f"Un passager souhaite rejoindre votre trajet {correspondance.voyage.ville_depart} → {correspondance.voyage.ville_arrivee}.",
        related_voyage=correspondance.voyage,
        related_correspondance=correspondance,
    )
    
    # Notify passenger
    create_notification(
        user=correspondance.demande.passager,
        notification_type='match',
        title='Nouveau match trouvé !',
        message=f"Un trajet correspond à votre demande {correspondance.demande.ville_depart} → {correspondance.demande.ville_arrivee}.",
        related_voyage=correspondance.voyage,
        related_correspondance=correspondance,
    )


def notify_match_validated(correspondance):
    """Notify both parties when a match is validated."""
    # Notify passenger that driver validated
    create_notification(
        user=correspondance.demande.passager,
        notification_type='match_validated',
        title='Match validé !',
        message=f"Le conducteur a validé votre participation au trajet {correspondance.voyage.ville_depart} → {correspondance.voyage.ville_arrivee}.",
        related_voyage=correspondance.voyage,
        related_correspondance=correspondance,
    )
    
    # Notify driver that validation is complete
    create_notification(
        user=correspondance.voyage.conducteur,
        notification_type='match_validated',
        title='Match confirmé',
        message=f"Vous avez validé la participation de {correspondance.demande.passager.username} pour votre trajet.",
        related_voyage=correspondance.voyage,
        related_correspondance=correspondance,
    )


def notify_match_refused(correspondance, refused_by_driver=True):
    """Notify when a match is refused."""
    if refused_by_driver:
        # Notify passenger
        create_notification(
            user=correspondance.demande.passager,
            notification_type='match_refused',
            title='Match refusé',
            message=f"Le conducteur a refusé votre demande pour le trajet {correspondance.voyage.ville_depart} → {correspondance.voyage.ville_arrivee}.",
            related_voyage=correspondance.voyage,
            related_correspondance=correspondance,
        )
    else:
        # Notify driver
        create_notification(
            user=correspondance.voyage.conducteur,
            notification_type='match_refused',
            title='Match annulé',
            message=f"Le passager {correspondance.demande.passager.username} a annulé son intérêt pour votre trajet.",
            related_voyage=correspondance.voyage,
            related_correspondance=correspondance,
        )


def notify_new_review(avis):
    """Notify user when they receive a new review."""
    create_notification(
        user=avis.utilisateur_note,
        notification_type='review',
        title='Nouvel avis reçu',
        message=f"{avis.auteur.username} vous a donné {avis.note}/5 étoiles. \"{avis.commentaire[:50]}...\"" if avis.commentaire else f"{avis.auteur.username} vous a donné {avis.note}/5 étoiles.",
        related_avis=avis,
        related_voyage=avis.voyage,
    )


def notify_trip_reminder(voyage, hours_before=24):
    """Send a reminder before a trip."""
    create_notification(
        user=voyage.conducteur,
        notification_type='trip_reminder',
        title='Rappel : Trajet à venir',
        message=f"Votre trajet {voyage.ville_depart} → {voyage.ville_arrivee} est prévu pour le {voyage.date_depart.strftime('%d/%m/%Y à %H:%M')}.",
        related_voyage=voyage,
        send_email=True,
    )
    
    # Also notify all matched passengers
    correspondances = voyage.correspondance_set.filter(is_validated=True)
    for c in correspondances:
        create_notification(
            user=c.demande.passager,
            notification_type='trip_reminder',
            title='Rappel : Trajet à venir',
            message=f"Votre trajet avec {voyage.conducteur.username} ({voyage.ville_depart} → {voyage.ville_arrivee}) est prévu pour le {voyage.date_depart.strftime('%d/%m/%Y à %H:%M')}.",
            related_voyage=voyage,
            send_email=True,
        )


def notify_trip_completed(voyage):
    """Notify when a trip is marked as completed."""
    # Notify driver
    create_notification(
        user=voyage.conducteur,
        notification_type='trip_completed',
        title='Trajet terminé',
        message=f"Votre trajet {voyage.ville_depart} → {voyage.ville_arrivee} a été marqué comme terminé. N'oubliez pas de laisser un avis !",
        related_voyage=voyage,
    )
    
    # Notify passengers
    correspondances = voyage.correspondance_set.filter(is_validated=True)
    for c in correspondances:
        create_notification(
            user=c.demande.passager,
            notification_type='trip_completed',
            title='Trajet terminé',
            message=f"Votre trajet avec {voyage.conducteur.username} ({voyage.ville_depart} → {voyage.ville_arrivee}) est terminé. N'oubliez pas de laisser un avis !",
            related_voyage=voyage,
        )


def get_unread_count(user):
    """Get the number of unread notifications for a user."""
    return Notification.objects.filter(user=user, is_read=False).count()


def mark_all_read(user):
    """Mark all notifications as read for a user."""
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
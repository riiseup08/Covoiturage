"""Review eligibility — single source of truth for who may rate whom.

Shared by the web view (``add_avis_view``) and the REST API (``AvisViewSet``) so
the participation rules can't drift apart. Reviews drive ``trust_score``, which
now gates escrow payouts, so this guard is security-relevant.
"""

from covoiturage.models import Correspondance, Avis


def can_review(author, voyage, target):
    """Return ``(ok, reason)`` for whether ``author`` may review ``target`` on ``voyage``.

    Rules:
      - cannot review yourself;
      - the trip must be terminated;
      - author and target must have shared the trip via a validated, non-refused
        correspondance (one as driver, the other as passenger);
      - no existing review by this author for this target on this trip.
    """
    if author.id == target.id:
        return False, "Vous ne pouvez pas vous noter vous-même."
    if not voyage.est_termine:
        return False, "Le trajet n'est pas encore terminé."

    base = Correspondance.objects.filter(
        voyage=voyage, is_validated=True, refus_conducteur=False, refus_passager=False
    )
    if voyage.conducteur_id == author.id:
        shared = base.filter(demande__passager=target).exists()
    elif voyage.conducteur_id == target.id:
        shared = base.filter(demande__passager=author).exists()
    else:
        shared = False
    if not shared:
        return False, "Vous ne pouvez pas noter cette personne pour ce trajet."

    if Avis.objects.filter(voyage=voyage, auteur=author, utilisateur_note=target).exists():
        return False, "Vous avez déjà laissé un avis pour cette personne sur ce trajet."

    return True, ""

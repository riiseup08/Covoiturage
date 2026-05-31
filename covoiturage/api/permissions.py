from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, "conducteur"):
            return obj.conducteur == request.user
        if hasattr(obj, "passager"):
            return obj.passager == request.user
        if hasattr(obj, "auteur"):
            return obj.auteur == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user

        return obj == request.user


class IsParticipantOfConversation(permissions.BasePermission):
    """
    Only participants of a conversation can access it.
    """

    def has_object_permission(self, request, view, obj):
        correspondance = obj.correspondance
        user = request.user
        return (
            correspondance.voyage.conducteur == user
            or correspondance.demande.passager == user
        )

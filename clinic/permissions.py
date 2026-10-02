from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import Profile


def get_role(user):
    """Role of the authenticated user; staff and superusers act as receptionists."""
    if user.is_staff or user.is_superuser:
        return Profile.Role.RECEPTIONIST
    profile = getattr(user, 'profile', None)
    return profile.role if profile else Profile.Role.PATIENT


class IsReceptionist(BasePermission):
    """Full access for receptionists (and staff) only."""

    def has_permission(self, request, view):
        return get_role(request.user) == Profile.Role.RECEPTIONIST


class IsReceptionistOrReadOnly(BasePermission):
    """Anyone authenticated may read; only receptionists may write."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return get_role(request.user) == Profile.Role.RECEPTIONIST

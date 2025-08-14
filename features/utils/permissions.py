from rest_framework import permissions
from features.users.models import User

class HasRole(permissions.BasePermission):
    """
    Permission check for user with a specific role in their Firebase custom claims
    """
    def __init__(self, role):
        self.required_role = role
    
    def has_permission(self, request, view):
        # request.auth is the decoded token from FirebaseAuthentication
        if not request.auth:
            return False
        user_roles = request.auth.get('roles', [])

        if not user_roles:
            user_roles = User.objects.get(firebase_uid=request.auth.get('uid')).role

        return self.required_role in user_roles

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return HasRole('ADMIN').has_permission(request, view)
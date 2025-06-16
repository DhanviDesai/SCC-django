from rest_framework import permissions

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
        print(request.auth)

        return self.required_role in user_roles

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return HasRole('ADMIN').has_permission(request, view)
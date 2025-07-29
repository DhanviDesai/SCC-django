from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth
from features.users.models import User


class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise AuthenticationFailed("No token provided") # No token provided

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            # Invalid token header
            raise AuthenticationFailed("Invalid token header")

        id_token = parts[1]

        try:
            # Use the Firebase Admin SDK to verify the token
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            # This could be an expired token, invalid token, etc.
            raise AuthenticationFailed(f'Invalid Firebase ID token: {e}')

        if not decoded_token:
            raise AuthenticationFailed('Token verification failed')

        # The 'uid' is Firebase's unique ID for the user
        uid = decoded_token.get('uid')

        # --- This is where you link to your local user model ---
        # This follows the "Just-In-Time Provisioning" we discussed before.
        try:
            user = User.objects.get(firebase_uid=uid)
        except User.DoesNotExist:
            # Create a new user in your local database
            # You can pull more info from decoded_token if needed (e.g., email)
            raise AuthenticationFailed('User does not exist')

        # The authenticate method must return a (user, auth) tuple
        return (user, decoded_token)

class FirebaseTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise AuthenticationFailed("No token provided") # No token provided

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            # Invalid token header
            raise AuthenticationFailed("Invalid token header")

        id_token = parts[1]

        try:
            # Use the Firebase Admin SDK to verify the token
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            # This could be an expired token, invalid token, etc.
            raise AuthenticationFailed(f'Invalid Firebase ID token: {e}')

        if not decoded_token:
            raise AuthenticationFailed('Token verification failed')

        # The 'uid' is Firebase's unique ID for the user
        return (None, decoded_token)
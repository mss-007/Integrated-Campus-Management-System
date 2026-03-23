from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        # We always strip accidental spaces for everyone
        clean_username = username.strip()
        
        try:
            # 1. Find the user ignoring case first
            user = User.objects.get(username__iexact=clean_username)
            
            # 2. Check their role
            is_student = hasattr(user, 'student')
            
            # 3. 🔥 THE FIX: If they are NOT a student (i.e., Faculty or Admin), 
            # the typed username must match the database exactly!
            if not is_student:
                if user.username != clean_username:
                    return None # Reject the login if the case is wrong
                    
            # 4. If they passed the username check, verify the password
            if user.check_password(password):
                return user
                
        except User.DoesNotExist:
            return None
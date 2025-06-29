from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication that doesn't enforce CSRF checks.
    This is useful for API endpoints that need session authentication
    but are accessed programmatically.
    """
    
    def enforce_csrf(self, request):
        """
        Override to not enforce CSRF checks.
        """
        return  # Do nothing, effectively disabling CSRF checks
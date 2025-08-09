class AuthenticationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class MissingTokenError(AuthenticationError):
    def __init__(self):
        super().__init__("Not Signed In", 400)

class TokenVerificationError(AuthenticationError):
    def __init__(self):
        super().__init__("Token verification failed", 403)

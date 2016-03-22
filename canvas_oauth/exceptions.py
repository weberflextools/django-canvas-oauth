class CanvasOAuthError(Exception): pass

class MissingTokenError(CanvasOAuthError): pass

class InvalidTokenError(CanvasOAuthError): pass

class InvalidOAuthStateError(CanvasOAuthError): pass

class InvalidOAuthReturnError(CanvasOAuthError): pass

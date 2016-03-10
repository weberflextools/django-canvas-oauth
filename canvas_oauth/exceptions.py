class CanvasOauthError(Exception): pass

class MissingTokenError(CanvasOauthError): pass

class InvalidTokenError(CanvasOauthError): pass

class BadLTIConfigError(CanvasOauthError): pass

class InvalidOAuthStateError(CanvasOauthError): pass

class InvalidOAuthReturnError(CanvasOauthError): pass

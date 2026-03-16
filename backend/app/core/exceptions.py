"""Domain exceptions for MMAi V2.

Services raise these instead of HTTPException, keeping business logic
decoupled from the HTTP layer. Routes catch them and map to HTTP responses.
"""


class DomainError(Exception):
    """Base for all domain exceptions."""

    def __init__(self, detail: str = "An error occurred"):
        self.detail = detail
        super().__init__(detail)


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist or is not accessible."""

    def __init__(self, entity: str = "Resource", detail: str | None = None):
        self.entity = entity
        super().__init__(detail or f"{entity} not found")


class ConflictError(DomainError):
    """Raised when an operation conflicts with existing state (e.g. duplicate email)."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail)


class ValidationError(DomainError):
    """Raised when business-rule validation fails (not schema validation)."""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail)


class AuthenticationError(DomainError):
    """Raised when credentials are invalid or missing."""

    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail)


class QuotaExceededError(DomainError):
    """Raised when a user exceeds their usage quota."""

    def __init__(self, detail: str = "Daily message limit reached"):
        super().__init__(detail)

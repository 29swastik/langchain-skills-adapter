class SkillError(Exception):
    """Base exception for skill-related errors."""

    pass


class SkillNotFoundError(SkillError):
    """Raised when a skill cannot be found."""

    pass


class SkillValidationError(SkillError):
    """Raised when skill validation fails."""

    pass


class SkillLoadError(SkillError):
    """Raised when a skill cannot be loaded."""

    pass

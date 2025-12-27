"""
Centralized version information for Mergen.
This is the single source of truth for version numbers.
"""

__version__ = "0.9.3"
__version_info__ = (0, 9, 3)

# Release information
RELEASE_NAME = "Universal"
RELEASE_DATE = "2025-12-27"


def get_version_string():
    """Returns formatted version string."""
    return f"Mergen {__version__} ({RELEASE_NAME})"

"""
Centralized version information for Mergen.
This is the single source of truth for version numbers.
"""

__version__ = "0.9.5"
__version_info__ = (0, 9, 5)

# Release information
RELEASE_NAME = "Performance Edition"
RELEASE_DATE = "2025-12-28"


def get_version_string():
    """Returns formatted version string."""
    return f"{__version__}"

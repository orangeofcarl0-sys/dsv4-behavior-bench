"""datapipe - device telemetry pipeline (v2.4 spec)."""
from .errors import DataError
from .version import VERSION

__all__ = ["DataError", "VERSION", "__version__"]
__version__ = VERSION

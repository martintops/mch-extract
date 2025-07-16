"""
mch-extract: A Python package for extracting meteorological data from MeteoSwiss.

This package provides both a command-line interface and a programmatic API
for downloading weather data from the MeteoSwiss OpenData API.

Example usage:
    >>> from mchextract import get_data
    >>> from datetime import date
    >>>
    >>> # Simple one-off data extraction
    >>> data = get_data(
    ...     stations=['PAY', 'VIT'],
    ...     variables=['temperature', 'precipitation'],
    ...     start_date=date(2023, 1, 1),
    ...     end_date=date(2023, 1, 31),
    ...     timescale='daily'
    ... )
    >>>
    >>> # For more complex usage
    >>> from mchextract import MchExtract
    >>> extractor = MchExtract(verbose=True)
    >>> stations = extractor.get_available_stations()
    >>> data = extractor.get_data(...)
"""

from .api import MchExtract, get_data
from .models import TimeScale

__all__ = ["MchExtract", "get_data", "TimeScale"]

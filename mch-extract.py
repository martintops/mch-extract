#!/usr/bin/env python3
"""
Command-line script for mch-extract.

This script provides a command-line interface for extracting meteorological data
from MeteoSwiss. It uses the mchextract package API internally.
"""

import sys

from mchextract.cli import main

if __name__ == "__main__":
    sys.exit(main())

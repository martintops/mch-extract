"""
Clean API for mch-extract package.

This module provides a simple interface to extract meteorological data
from MeteoSwiss in polars DataFrame format.
"""

import logging
from datetime import date, timedelta
from typing import Literal

import polars as pl
from more_itertools import flatten

from mchextract.downloader import CachedDownloader

from .data_downloader import DataAvailabilityChecker, DataDownloader
from .dwhconverter import convert_common_name_to_dwh
from .metadata_loader import MetaDataLoader
from .models import MeteoData, Parameter, Station, TimeScale


class MchExtract:
    """
    Main API class for extracting MeteoSwiss data.

    Example usage:
        extractor = MchExtract()
        data = extractor.get_data(
            stations=['PAY', 'VIT'],
            variables=['temperature', 'precipitation'],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            timescale='daily'
        )
    """

    def __init__(
        self,
        verbose: bool = False,
        use_cache: bool = True,
        _metadata: MeteoData | None = None,
    ):
        """
        Initialize the MchExtract API.

        Args:
            verbose: Enable verbose logging if True
        """
        self._logger = logging.getLogger(__name__)
        if verbose:
            logging.basicConfig(level=logging.DEBUG)

        self._downloader = CachedDownloader(cache_enabled=use_cache)
        self._metadata: MeteoData = _metadata or self._load_metadata()

    def _load_metadata(self) -> MeteoData:
        """Ensure metadata is loaded, download if necessary."""
        self._logger.debug("Loading metadata...")
        loader = MetaDataLoader(self._downloader)
        metadata = loader.load_all()
        self._logger.debug("Metadata loaded successfully")
        return metadata

    def get_available_stations(self) -> list[str]:
        """
        Get list of available station codes.

        Returns:
            list of station abbreviations (3-letter codes)
        """
        return list(self._metadata.stations.keys())

    def get_available_variables(self) -> list[str]:
        """
        Get list of available common variable names.

        Returns:
            list of variable names that can be used in get_data()
        """
        from .dwhconverter import DWH_CONVERTERS

        return list(DWH_CONVERTERS.keys())

    def get_station_info(self, station: str) -> dict | None:
        """
        Get detailed information about a station.

        Args:
            station: Station abbreviation (3-letter code)

        Returns:
            dictionary with station information or None if not found
        """
        if station not in self._metadata.stations:
            return None

        station_obj = self._metadata.stations[station]
        return {
            "abbr": station_obj.abbr,
            "name": station_obj.name,
            "canton": station_obj.canton,
            "coordinates_lat": station_obj.coordinates_wgs84_lat,
            "coordinates_lon": station_obj.coordinates_wgs84_lon,
            "height_masl": station_obj.height_masl,
            "data_since": station_obj.data_since,
            "available_parameters": [
                param.parameter_shortname for param in station_obj.available_parameters
            ],
        }

    def get_data(
        self,
        stations: str | list[str],
        variables: str | list[str] | None,
        start_date: date,
        end_date: date,
        timescale: Literal["daily", "hourly", "monthly", "10min"]
        | TimeScale = TimeScale.DAILY,
        dwh_parameters: list[str] | None = None,
        short: bool = True,
    ) -> pl.DataFrame:
        """
        Extract meteorological data from MeteoSwiss.

        Args:
            stations: Station code(s) (3-letter codes like 'PAY', 'VIT')
            variables: Variable name(s) (common names like 'temperature', 'precipitation'). If None, all available variables will be used.
            start_date: Start date for data extraction
            end_date: End date for data extraction
            timescale: Time resolution ('daily', 'hourly', 'monthly', '10min' or TimeScale enum)
            dwh_parameters: Additional DWH parameter codes to include
            short: If True, use short parameter names in the output DataFrame

        Returns:
            Polars DataFrame with the extracted data

        Raises:
            ValueError: If invalid parameters are provided
            RuntimeError: If data extraction fails
        """
        # Normalize inputs
        if isinstance(stations, str):
            stations = [stations]
        if isinstance(variables, str):
            variables = [variables]
        if variables is None:
            variables = []
        if dwh_parameters is None:
            dwh_parameters = []

        # Convert timescale string to enum
        if isinstance(timescale, str):
            timescale_map = {
                "daily": TimeScale.DAILY,
                "hourly": TimeScale.HOURLY,
                "monthly": TimeScale.MONTHLY,
                "yearly": TimeScale.YEARLY,
                "10min": TimeScale.TEN_MINUTES,
            }
            if timescale not in timescale_map:
                raise ValueError(
                    f"Invalid timescale: {timescale}. Must be one of {list(timescale_map.keys())}"
                )
            timescale = timescale_map[timescale]

        self._logger.debug(
            f"Extracting {timescale.to_readable_name()} data from {start_date} to {end_date} "
            f"for stations {stations} with variables {variables}."
        )

        # Validate stations
        requested_stations = set(stations)
        available_stations = set(self._metadata.stations.keys())
        valid_stations = [
            self._metadata.stations[station]
            for station in available_stations.intersection(requested_stations)
        ]

        if not requested_stations.issubset(available_stations):
            missing_stations = requested_stations - available_stations
            self._logger.warning(
                f"The following requested stations are not available: {missing_stations}"
            )

        if not valid_stations:
            raise ValueError(
                "No valid stations available for the requested data extraction."
            )

        # Validate and convert variables to parameters
        parameters: dict[str, Parameter] = {}
        if variables or dwh_parameters:
            parameters = self._convert_variables(
                variables,
                timescale,
                dwh_parameters,
                valid_stations,
                start_date,
                end_date,
            )

            if not parameters:
                raise ValueError(
                    "No valid parameters available for the requested data extraction."
                )

        # Validate date range
        if start_date > end_date:
            raise ValueError(
                f"Start date {start_date} cannot be after end date {end_date}."
            )
        # if end_date is the same month as today and timescale is monthly, raise an error
        if (
            timescale == TimeScale.MONTHLY
            and end_date.year == date.today().year
            and end_date.month == date.today().month
        ):
            suggestion = end_date.replace(day=1) - timedelta(days=1)
            raise ValueError(
                f"Cannot extract monthly data for the current month. Please specify an earlier end date (e.g.: {suggestion})"
            )

        # Check data availability
        is_available, error_message = DataAvailabilityChecker.check_data_availability(
            start_date, end_date, timescale
        )
        if not is_available:
            raise RuntimeError(f"Data not available: {error_message}")

        # Download the data
        downloader = DataDownloader(self._downloader)
        station_data = downloader.download_multiple_stations(
            stations=valid_stations,
            parameters=list(parameters.values()),
            start_date=start_date,
            end_date=end_date,
            timescale=timescale,
        )

        if not station_data:
            raise RuntimeError(
                "No data could be downloaded for the requested parameters and date range."
            )

        # Combine all station data into a single DataFrame
        combined_data = list(station_data.values())
        combined_df = pl.concat(combined_data, how="diagonal")

        # Sort by datetime and station for consistent output
        if "datetime_temp" in combined_df.columns:
            combined_df = combined_df.sort(["datetime_temp", "station_abbr"])
            # Drop the temporary datetime column since we have reference_timestamp
            combined_df = combined_df.drop("datetime_temp")

        # Rename parameter columns to their full names
        if not short:
            for col in combined_df.columns:
                # Find parameter with matching shortname
                if col in parameters:
                    combined_df = combined_df.rename(
                        {col: self._metadata.parameters[col].full_name}
                    )

        return combined_df

    def _convert_variables(
        self,
        variables: list[str],
        timescale: TimeScale,
        dwh_parameters: list[str],
        valid_stations: list[Station],
        start_date: date,
        end_date: date,
    ) -> dict[str, Parameter]:
        requested_variables = set(
            flatten([convert_common_name_to_dwh(v, timescale) for v in variables])
        ).union(set(dwh_parameters))
        parameters: dict[str, Parameter] = {}

        for station in valid_stations:
            param_dict = {
                param.parameter_shortname: param
                for param in station.available_parameters
            }
            available_variables = set(param_dict.keys())
            if not requested_variables.issubset(available_variables):
                missing_vars = requested_variables - available_variables
                self._logger.warning(
                    f"The following requested variables are not available for station {station.abbr}: {[self._metadata.parameters[var].full_name for var in missing_vars]}"
                )

            available: set[Parameter] = {
                self._metadata.parameters[param.parameter_shortname]
                for param in station.available_parameters
                if param.parameter_shortname in requested_variables
            }

            # Check start and end dates for each parameter, warnings only
            for param in available:
                # we are guaranteed that param is in param_dict
                param_since = param_dict[param.shortname].data_since
                param_till = param_dict[param.shortname].data_till
                if param_since and start_date < param_since.date():
                    self._logger.warning(
                        f"Parameter {param.full_name} at station {station.abbr} has data since {param_since}, "
                        f"but requested start date is {start_date}."
                    )

                if param_till and end_date > param_till.date():
                    self._logger.warning(
                        f"Parameter {param.full_name} at station {station.abbr} has data until {param_till}, "
                        f"but requested end date is {end_date}."
                    )

                parameters[param.shortname] = param

        return parameters


# Convenience function for simple usage
def get_data(
    stations: str | list[str],
    variables: str | list[str] | None,
    start_date: date,
    end_date: date,
    timescale: Literal["daily", "hourly", "monthly", "10min"]
    | TimeScale = TimeScale.DAILY,
    dwh_parameters: list[str] | None = None,
    verbose: bool = False,
    short: bool = True,
) -> pl.DataFrame:
    """
    Convenience function to extract meteorological data from MeteoSwiss.

    This is a simple wrapper around the MchExtract class for one-off data extractions.

    Args:
        stations: Station code(s) (3-letter codes like 'PAY', 'VIT')
        variables: Variable name(s) (common names like 'temperature', 'precipitation'). If None, all available variables will be used.
        start_date: Start date for data extraction
        end_date: End date for data extraction
        timescale: Time resolution ('daily', 'hourly', 'monthly', '10min' or TimeScale enum)
        dwh_parameters: Additional DWH parameter codes to include
        verbose: Enable verbose logging if True

    Returns:
        Polars DataFrame with the extracted data

    Example:
        >>> from mchextract import get_data
        >>> from datetime import date
        >>> data = get_data(
        ...     stations=['PAY', 'VIT'],
        ...     variables=['temperature', 'precipitation'],
        ...     start_date=date(2023, 1, 1),
        ...     end_date=date(2023, 1, 31),
        ...     timescale='daily'
        ... )
    """
    extractor = MchExtract(verbose=verbose)
    return extractor.get_data(
        stations=stations,
        variables=variables,
        start_date=start_date,
        end_date=end_date,
        timescale=timescale,
        dwh_parameters=dwh_parameters,
        short=short,
    )

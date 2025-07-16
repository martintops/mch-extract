import logging
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path

import polars as pl
import requests

from .consts import DATA_SOURCES, DataSource
from .models import Parameter, Station, TimeScale


class UpdateFrequency(Enum):
    """Update frequency types for MeteoSwiss data files."""

    HISTORICAL = "historical"  # From start until Dec 31 of last year
    RECENT = "recent"  # From Jan 1 of this year until yesterday
    NOW = "now"  # Recent realtime data, only for h and t granularity


AVAILABLE_UPDATE_FREQ = {
    UpdateFrequency.HISTORICAL: ["m", "d", "h", "t"],
    UpdateFrequency.RECENT: ["m", "d", "h", "t"],
    UpdateFrequency.NOW: ["h", "t"],
}


class DataAvailabilityChecker:
    """Checks data availability based on MeteoSwiss file structure."""

    # Mapping of data types and their availability

    @classmethod
    def check_data_availability(
        cls, start_date: date, end_date: date, timescale: TimeScale
    ) -> tuple[bool, str]:
        """
        Check if data is available for the requested date range and timescale.
        Returns (is_available, error_message).
        """
        current_year = datetime.now().year
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Convert timescale to granularity
        granularity = timescale.to_granularity()

        # For yearly data, no type concept applies
        if timescale == TimeScale.YEARLY:
            return True, ""

        # Define date boundaries
        historical_end = date(current_year - 1, 12, 31)
        recent_start = date(current_year, 1, 1)

        # Check if the requested range is entirely in historical period
        if end_date <= historical_end:
            if granularity in AVAILABLE_UPDATE_FREQ[UpdateFrequency.HISTORICAL]:
                return True, ""
            else:
                return (
                    False,
                    f"Historical data not available for {timescale.to_readable_name()} granularity",
                )

        # Check if the requested range is entirely in recent period
        if start_date >= recent_start and end_date <= yesterday:
            if granularity in AVAILABLE_UPDATE_FREQ[UpdateFrequency.RECENT]:
                return True, ""
            else:
                return (
                    False,
                    f"Recent data not available for {timescale.to_readable_name()} granularity",
                )

        # Check if the requested range includes current period (now)
        if end_date >= today:
            if granularity in AVAILABLE_UPDATE_FREQ[UpdateFrequency.NOW]:
                return True, ""
            else:
                return (
                    False,
                    f"Real-time data is only available for hourly and 10-minute granularities, not {timescale.to_readable_name()}",
                )

        # Check if the requested range spans multiple periods
        spans_historical = start_date <= historical_end
        spans_recent = start_date <= yesterday and end_date >= recent_start
        spans_now = (
            end_date >= yesterday
            and granularity in AVAILABLE_UPDATE_FREQ[UpdateFrequency.NOW]
        )

        if spans_historical or spans_recent or spans_now:
            return True, ""

        # If we get here, the date range is not covered by any available data type
        return (
            False,
            f"No data available for the requested date range {start_date} to {end_date} with {timescale.to_readable_name()} granularity",
        )


class DataDownloader:
    """Downloads MeteoSwiss data from their open data portal."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self._logger = logging.getLogger(__name__)
        # Cache data sources by name for quick lookup
        self._data_sources = {source.name: source for source in DATA_SOURCES}

    def _get_data_source_for_station(self, station: Station) -> DataSource:
        """Get the data source configuration for a station."""
        return self._data_sources[station.data_source]

    def _determine_files_needed(
        self, start_date: date, end_date: date, timescale: TimeScale
    ) -> list[tuple[UpdateFrequency, tuple[int, int] | None]]:
        """Determine which file types (historical/recent/now) are needed for the date range.

        Returns list of tuples: (frequency, decade_range) where decade_range is (start_year, end_year) for historical files.
        """
        current_year = datetime.now().year
        today = date.today()

        files_needed: list[tuple[UpdateFrequency, tuple[int, int] | None]] = []

        # Historical data: from start of measurement until Dec 31 of last year
        historical_end = date(current_year - 1, 12, 31)
        if start_date <= historical_end:
            # For hourly and 10-minute data, we need to determine which 10-year periods to download
            if timescale in [TimeScale.HOURLY, TimeScale.TEN_MINUTE]:
                # Find the 10-year periods that overlap with our date range
                start_decade = (start_date.year // 10) * 10
                end_decade = min(
                    (end_date.year // 10) * 10, (historical_end.year // 10) * 10
                )

                for decade_start in range(start_decade, end_decade + 1, 10):
                    decade_end = decade_start + 9
                    # Only include decades that actually overlap with our date range
                    if decade_start <= end_date.year and decade_end >= start_date.year:
                        files_needed.append(
                            (UpdateFrequency.HISTORICAL, (decade_start, decade_end))
                        )
            else:
                # For daily and monthly data, use single historical file
                files_needed.append((UpdateFrequency.HISTORICAL, None))

        # Recent data: from Jan 1 of this year until yesterday
        recent_start = date(current_year, 1, 1)
        yesterday = today - timedelta(days=1)
        if start_date <= yesterday and end_date >= recent_start:
            files_needed.append((UpdateFrequency.RECENT, None))

        # Now data: from yesterday 12UTC to now (only for hourly and 10-minute)
        if (
            timescale in [TimeScale.HOURLY, TimeScale.TEN_MINUTE]
            and end_date >= yesterday
        ):
            files_needed.append((UpdateFrequency.NOW, None))

        # If no files determined and dates are in current year, default to recent
        if not files_needed and start_date >= recent_start:
            files_needed.append((UpdateFrequency.RECENT, None))

        return files_needed

    def _build_url(
        self,
        station: Station,
        timescale: TimeScale,
        frequency: UpdateFrequency,
        decade_range: tuple[int, int] | None = None,
    ) -> str:
        """Build the download URL for a specific station, timescale, and frequency."""
        data_source = self._get_data_source_for_station(station)
        granularity = timescale.to_granularity()

        if frequency == UpdateFrequency.NOW:
            # Format: {prefix}_{station}_{granularity}_now.csv
            filename = f"{data_source.file_prefix}_{station.abbr.lower()}_{granularity}_now.csv"
        elif granularity == "m":
            # Monthly data has a special format: {prefix}_{station}_m.csv (no frequency suffix)
            filename = f"{data_source.file_prefix}_{station.abbr.lower()}_m.csv"
        elif frequency == UpdateFrequency.HISTORICAL and decade_range is not None:
            # Historical data with decade range: {prefix}_{station}_{granularity}_historical_{start}-{end}.csv
            start_year, end_year = decade_range
            filename = f"{data_source.file_prefix}_{station.abbr.lower()}_{granularity}_historical_{start_year}-{end_year}.csv"
        else:
            # Format: {prefix}_{station}_{granularity}_{frequency}.csv
            filename = f"{data_source.file_prefix}_{station.abbr.lower()}_{granularity}_{frequency.value}.csv"

        return f"{data_source.data_url}/{station.abbr.lower()}/{filename}"

    def _download_file(self, url: str) -> pl.DataFrame | None:
        """Download a single CSV file and return as polars DataFrame."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Read CSV with polars - MeteoSwiss uses semicolon as separator
            # Use infer_schema_length=0 to infer types from entire file
            # and ignore_errors=True to handle mixed data types
            from io import BytesIO

            df = pl.read_csv(
                BytesIO(response.content),
                separator=";",
                infer_schema_length=0,
                ignore_errors=True,
            )
            return df

        except requests.exceptions.RequestException as e:
            self._logger.error(f"Failed to download {url}: {e}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to parse CSV from {url}: {e}")
            return None

    def _filter_by_date_range(
        self, df: pl.DataFrame, start_date: date, end_date: date
    ) -> pl.DataFrame:
        """Filter DataFrame by date range."""
        # Convert reference_timestamp to datetime for filtering and sorting
        # MeteoSwiss uses 'reference_timestamp' column in DD.MM.YYYY HH:MM format
        if "reference_timestamp" in df.columns:
            # Convert DD.MM.YYYY HH:MM to datetime
            df = df.with_columns(
                [
                    pl.col("reference_timestamp")
                    .str.strptime(pl.Datetime, "%d.%m.%Y %H:%M")
                    .alias("datetime_temp")
                ]
            )

            # Filter by date range using the datetime column
            df = df.filter(
                (pl.col("datetime_temp").dt.date() >= start_date)
                & (pl.col("datetime_temp").dt.date() <= end_date)
            )

        return df

    def _filter_by_parameters(
        self, df: pl.DataFrame, parameters: list[Parameter]
    ) -> pl.DataFrame:
        """Filter DataFrame to only include requested parameters."""
        # Keep 'station_abbr', 'reference_timestamp', 'datetime_temp' and requested parameter columns
        keep_columns = ["station_abbr", "reference_timestamp"]
        if "datetime_temp" in df.columns:
            keep_columns.append("datetime_temp")

        # Add parameter columns that exist in the dataframe
        parameter_names = {param.shortname for param in parameters}
        for col in df.columns:
            if col in parameter_names:
                keep_columns.append(col)

        return df.select(keep_columns)

    def download_station_data(
        self,
        station: Station,
        parameters: list[Parameter],
        start_date: date,
        end_date: date,
        timescale: TimeScale,
    ) -> pl.DataFrame | None:
        """Download data for a single station."""
        files_needed = self._determine_files_needed(start_date, end_date, timescale)

        dataframes: list[pl.DataFrame] = []

        for frequency, decade_range in files_needed:
            url = self._build_url(station, timescale, frequency, decade_range)

            if decade_range:
                start_year, end_year = decade_range
                self._logger.debug(
                    f"Downloading {frequency.value} data ({start_year}-{end_year}) for station {station.abbr}: {url}"
                )
            else:
                self._logger.debug(
                    f"Downloading {frequency.value} data for station {station.abbr}: {url}"
                )

            df = self._download_file(url)
            if df is not None:
                # Filter by date range and parameters
                df = self._filter_by_date_range(df, start_date, end_date)
                if parameters:
                    df = self._filter_by_parameters(df, parameters)

                if len(df) > 0:
                    dataframes.append(df)

        if not dataframes:
            self._logger.warning(f"No data downloaded for station {station.abbr}")
            return None

        # Combine all dataframes and remove duplicates
        combined_df = pl.concat(dataframes)
        combined_df = combined_df.sort("datetime_temp").unique()

        return combined_df

    def download_multiple_stations(
        self,
        stations: list[Station],
        parameters: list[Parameter],
        start_date: date,
        end_date: date,
        timescale: TimeScale,
    ) -> dict[str, pl.DataFrame]:
        """Download data for multiple stations."""
        results = {}

        for station in stations:
            df = self.download_station_data(
                station, parameters, start_date, end_date, timescale
            )
            if df is not None:
                results[station.abbr] = df

        return results

    def save_data(
        self, data: dict[str, pl.DataFrame], output_path: str, format: str = "csv"
    ) -> None:
        """Save downloaded data to a single combined file."""
        output_file = Path(output_path)

        if len(data) == 0:
            self._logger.warning("No data to save")
            return

        # Combine all stations into a single file (station_abbr column already identifies the station)
        combined_data = list(data.values())

        # Combine all dataframes
        combined_df = pl.concat(combined_data, how="diagonal")

        # Sort by datetime_temp and station_abbr for consistent output
        combined_df = combined_df.sort(["datetime_temp", "station_abbr"])
        # Drop the temporary datetime column since we have reference_timestamp
        combined_df = combined_df.drop("datetime_temp")

        # Save combined data
        if format.lower() == "csv":
            combined_df.write_csv(output_file)
        elif format.lower() == "parquet":
            combined_df.write_parquet(output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")

        station_count = len(data)
        total_rows = len(combined_df)
        self._logger.debug(
            f"Combined data for {station_count} station(s) with {total_rows} total rows saved to {output_file}"
        )

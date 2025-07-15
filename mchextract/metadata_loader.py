from pathlib import Path

import polars as pl

from mchextract.consts import DATA_SOURCES, DEFAULT_CACHE_DIR, DataSource
from mchextract.models import DataAvailability, MeteoData, Parameter, Station


class MetaDataLoader:
    """Loads MeteoSwiss metadata from CSV files and creates structured data models."""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR):
        self._cache_dir = cache_dir

    def _get_data_source_file_path(
        self, data_source: DataSource, file_type: str
    ) -> Path:
        """Get the file path for a specific data source and file type."""
        filename = data_source.meta_files[file_type]
        return self._cache_dir / filename

    def load_parameters(self) -> dict[str, Parameter]:
        """Load parameter definitions from CSV files from all data sources."""
        parameters = {}

        for data_source in DATA_SOURCES:
            csv_file = self._get_data_source_file_path(data_source, "PARAMETERS")

            if not csv_file.exists():
                continue

            df = pl.read_csv(
                csv_file,
                separator=";",
                encoding="utf8",
                schema_overrides={
                    "parameter_decimals": pl.Int32,
                },
            )

            for row in df.iter_rows(named=True):
                parameter = Parameter(
                    shortname=row["parameter_shortname"],
                    description_de=row["parameter_description_de"].strip('"'),
                    description_fr=row["parameter_description_fr"].strip('"'),
                    description_it=row["parameter_description_it"].strip('"'),
                    description_en=row["parameter_description_en"].strip('"'),
                    group_de=row["parameter_group_de"],
                    group_fr=row["parameter_group_fr"],
                    group_it=row["parameter_group_it"],
                    group_en=row["parameter_group_en"],
                    granularity=row["parameter_granularity"],
                    decimals=row["parameter_decimals"],
                    datatype=row["parameter_datatype"],
                    unit=row["parameter_unit"],
                )
                parameters[parameter.shortname] = parameter

        return parameters

    def load_data_inventory(self) -> dict[str, list[DataAvailability]]:
        """Load data availability information from CSV files, grouped by station."""
        inventory: dict[str, list[DataAvailability]] = {}

        for data_source in DATA_SOURCES:
            csv_file = self._get_data_source_file_path(data_source, "DATA_INVENTORY")

            if not csv_file.exists():
                continue

            df = pl.read_csv(
                csv_file,
                separator=";",
                encoding="utf8",
                schema_overrides={
                    "meas_cat_nr": pl.Int32,
                },
            ).with_columns(
                [
                    pl.col("data_since").str.strptime(
                        pl.Datetime, "%d.%m.%Y %H:%M", strict=False
                    ),
                    pl.col("data_till").str.strptime(
                        pl.Datetime, "%d.%m.%Y %H:%M", strict=False
                    ),
                ]
            )

            for row in df.iter_rows(named=True):
                station_abbr = row["station_abbr"]

                availability = DataAvailability(
                    parameter_shortname=row["parameter_shortname"],
                    meas_cat_nr=row["meas_cat_nr"],
                    data_since=row["data_since"],
                    data_till=row["data_till"],
                    owner=row["owner"],
                )

                if station_abbr not in inventory:
                    inventory[station_abbr] = []
                inventory[station_abbr].append(availability)

        return inventory

    def load_stations(
        self, data_inventory: dict[str, list[DataAvailability]]
    ) -> dict[str, Station]:
        """Load station metadata from CSV files and join with data inventory."""
        stations = {}

        for data_source in DATA_SOURCES:
            csv_file = self._get_data_source_file_path(data_source, "STATIONS")

            if not csv_file.exists():
                continue

            df = pl.read_csv(
                csv_file,
                separator=";",
                encoding="utf8",
                schema_overrides={
                    "station_height_masl": pl.Float64,
                    "station_height_barometer_masl": pl.Float64,
                    "station_coordinates_lv95_east": pl.Float64,
                    "station_coordinates_lv95_north": pl.Float64,
                    "station_coordinates_wgs84_lat": pl.Float64,
                    "station_coordinates_wgs84_lon": pl.Float64,
                },
            ).with_columns(
                [
                    pl.col("station_data_since").str.strptime(
                        pl.Datetime, "%d.%m.%Y %H:%M", strict=False
                    ),
                ]
            )

            for row in df.iter_rows(named=True):
                station_abbr = row["station_abbr"]

                station = Station(
                    abbr=station_abbr,
                    name=row["station_name"],
                    canton=row["station_canton"],
                    wigos_id=row["station_wigos_id"],
                    type_de=row["station_type_de"],
                    type_fr=row["station_type_fr"],
                    type_it=row["station_type_it"],
                    type_en=row["station_type_en"],
                    dataowner=row["station_dataowner"],
                    data_since=row["station_data_since"],
                    height_masl=row["station_height_masl"],
                    height_barometer_masl=row["station_height_barometer_masl"],
                    coordinates_lv95_east=row["station_coordinates_lv95_east"],
                    coordinates_lv95_north=row["station_coordinates_lv95_north"],
                    coordinates_wgs84_lat=row["station_coordinates_wgs84_lat"],
                    coordinates_wgs84_lon=row["station_coordinates_wgs84_lon"],
                    exposition_de=row["station_exposition_de"],
                    exposition_fr=row["station_exposition_fr"],
                    exposition_it=row["station_exposition_it"],
                    exposition_en=row["station_exposition_en"],
                    url_de=row["station_url_de"],
                    url_fr=row["station_url_fr"],
                    url_it=row["station_url_it"],
                    url_en=row["station_url_en"],
                    # Join with data inventory
                    available_parameters=data_inventory.get(station_abbr, []),
                    # Track which data source this station belongs to
                    data_source=data_source.name,
                )

                stations[station_abbr] = station

        return stations

    def load_all(self) -> MeteoData:
        """Load all metadata and return structured MeteoData object."""
        parameters = self.load_parameters()
        data_inventory = self.load_data_inventory()
        stations = self.load_stations(data_inventory)

        return MeteoData(stations=stations, parameters=parameters)

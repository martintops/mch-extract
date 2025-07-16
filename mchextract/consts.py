from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DEFAULT_CACHE_DIR = Path(__file__).parent / ".cache"


@dataclass
class DataSource:
    """Represents a MeteoSwiss data source configuration."""

    name: str
    collection_url: str
    data_url: str
    file_prefix: str

    @property
    def meta_files(self) -> dict[str, str]:
        """Return metadata file mappings for this data source."""
        return {
            "DATA_INVENTORY": f"{self.file_prefix}_meta_datainventory.csv",
            "PARAMETERS": f"{self.file_prefix}_meta_parameters.csv",
            "STATIONS": f"{self.file_prefix}_meta_stations.csv",
        }


# Define data sources
SMN_SOURCE = DataSource(
    name="smn",
    collection_url="https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn",
    data_url="https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn",
    file_prefix="ogd-smn",
)

PRECIP_SOURCE = DataSource(
    name="smn-precip",
    collection_url="https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn-precip",
    data_url="https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn-precip",
    file_prefix="ogd-smn-precip",
)

TOWER_SOURCE = DataSource(
    name="smn-tower",
    collection_url="https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn-tower",
    data_url="https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn-tower",
    file_prefix="ogd-smn-tower",
)

# All available data sources
DATA_SOURCES = [SMN_SOURCE, PRECIP_SOURCE, TOWER_SOURCE]


class MetaDataFiles(Enum):
    """Enum for metadata files used in the MeteoSwiss OGD SMN API."""

    DATA_INVENTORY = "ogd-smn_meta_datainventory.csv"
    PARAMETERS = "ogd-smn_meta_parameters.csv"
    STATIONS = "ogd-smn_meta_stations.csv"

    @property
    def filename(self) -> str:
        """Return the file name associated with the enum member."""
        return self.value

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class TimeScale(Enum):
    DAILY = "D"
    HOURLY = "H"
    MONTHLY = "M"
    YEARLY = "Y"
    TEN_MINUTE = "T"

    def to_granularity(self) -> str:
        """Convert TimeScale to granularity string."""
        return self.value.lower()

    def to_readable_name(self) -> str:
        """Convert TimeScale to a human-readable name."""
        return {
            TimeScale.DAILY: "daily",
            TimeScale.HOURLY: "hourly",
            TimeScale.MONTHLY: "monthly",
            TimeScale.YEARLY: "yearly",
            TimeScale.TEN_MINUTE: "ten-minute",
        }[self]


@dataclass
class MchExtractArgs:
    start_date: date
    end_date: date
    stations: list[str]
    variables: list[str]
    parameters: list[str]
    timescale: TimeScale
    output: str | None
    verbose: bool = False


@dataclass
class Parameter:
    """Represents a MeteoSwiss parameter definition."""

    shortname: str
    description_de: str
    description_fr: str
    description_it: str
    description_en: str
    group_de: str
    group_fr: str
    group_it: str
    group_en: str
    granularity: str  # D=Daily, H=Hourly, M=Monthly, Y=Yearly, T=Ten-minute
    decimals: int
    datatype: str  # Integer, Float
    unit: str

    def __hash__(self) -> int:
        return hash(self.shortname)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Parameter):
            return NotImplemented
        return self.shortname == other.shortname


@dataclass
class DataAvailability:
    """Represents data availability for a parameter at a station."""

    parameter_shortname: str
    meas_cat_nr: int
    data_since: datetime | None
    data_till: datetime | None
    owner: str


@dataclass
class Station:
    """Represents a MeteoSwiss weather station with data availability."""

    abbr: str
    name: str
    canton: str
    wigos_id: str
    type_de: str
    type_fr: str
    type_it: str
    type_en: str
    dataowner: str
    data_since: datetime | None
    height_masl: float | None
    height_barometer_masl: float | None
    coordinates_lv95_east: float | None
    coordinates_lv95_north: float | None
    coordinates_wgs84_lat: float | None
    coordinates_wgs84_lon: float | None
    exposition_de: str
    exposition_fr: str
    exposition_it: str
    exposition_en: str
    url_de: str
    url_fr: str
    url_it: str
    url_en: str
    # Data availability for this station
    available_parameters: list[DataAvailability]
    # Data source this station belongs to
    data_source: str


@dataclass
class MeteoData:
    """Container for all MeteoSwiss metadata."""

    stations: dict[str, Station]  # keyed by station abbreviation
    parameters: dict[str, Parameter]  # keyed by parameter shortname

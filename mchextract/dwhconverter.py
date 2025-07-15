from collections.abc import Callable

from mchextract.models import TimeScale


def convert_common_name_to_dwh(common_name: str, timescale: TimeScale) -> list[str]:
    """Convert a common name to a list of DWH parameter shortnames."""
    if common_name not in DWH_CONVERTERS:
        raise ValueError(f"Unsupported common name: {common_name}")
    return DWH_CONVERTERS[common_name](timescale)


def _convert_temperature(timescale: TimeScale) -> list[str]:
    """Convert temperature to DWH parameter shortname based on timescale."""
    match timescale:
        case TimeScale.YEARLY:
            return ["tre200y0"]
        case TimeScale.MONTHLY:
            return ["tre200m0"]
        case TimeScale.DAILY:
            return ["tre200d0"]
        case TimeScale.HOURLY:
            return ["tre200h0"]
        case TimeScale.TEN_MINUTE:
            return ["tre200s0"]
        case _:
            raise ValueError(f"Unsupported timescale for temperature: {timescale}")


def _convert_precipitation(timescale: TimeScale) -> list[str]:
    """Convert precipitation to DWH parameter shortname based on timescale."""
    match timescale:
        case TimeScale.YEARLY:
            return ["rre150y0"]
        case TimeScale.MONTHLY:
            return ["rre150m0"]
        case TimeScale.DAILY:
            # rre150d0 is 6 UTC - 6UTC next day, rka150d0 is 0 UTC - 0 UTC next day
            return ["rre150d0", "rka150d0"]
        case TimeScale.HOURLY:
            return ["rre150h0"]
        case TimeScale.TEN_MINUTE:
            return ["rre150z0"]
        case _:
            raise ValueError(f"Unsupported timescale for precipitation: {timescale}")


def _convert_pressure(timescale: TimeScale) -> list[str]:
    """Convert pressure to DWH parameter shortname based on timescale."""
    match timescale:
        case TimeScale.YEARLY:
            return ["prestay0"]
        case TimeScale.MONTHLY:
            return ["prestam0"]
        case TimeScale.DAILY:
            return ["prestad0"]
        case TimeScale.HOURLY:
            return ["prestah0"]
        case TimeScale.TEN_MINUTE:
            return ["prestas0"]
        case _:
            raise ValueError(f"Unsupported timescale for pressure: {timescale}")


def _convert_humidity(timescale: TimeScale) -> list[str]:
    """Convert humidity to DWH parameter shortname based on timescale."""
    match timescale:
        case TimeScale.YEARLY:
            return ["ure200y0"]
        case TimeScale.MONTHLY:
            return ["ure200m0"]
        case TimeScale.DAILY:
            return ["ure200d0"]
        case TimeScale.HOURLY:
            return ["ure200h0"]
        case TimeScale.TEN_MINUTE:
            return ["ure200s0"]
        case _:
            raise ValueError(f"Unsupported timescale for humidity: {timescale}")


def _convert_sunshine(timescale: TimeScale) -> list[str]:
    """Convert sunshine to DWH parameter shortname based on timescale."""
    match timescale:
        case TimeScale.YEARLY:
            return ["sre000y0"]
        case TimeScale.MONTHLY:
            return ["sre000m0"]
        case TimeScale.DAILY:
            return ["sre000d0"]
        case TimeScale.HOURLY:
            return ["sre000h0"]
        case TimeScale.TEN_MINUTE:
            return ["sre000z0"]
        case _:
            raise ValueError(f"Unsupported timescale for sunshine: {timescale}")


def _convert_evaporation(timescale: TimeScale) -> list[str]:
    match timescale:
        case TimeScale.YEARLY:
            return ["erefaoy0"]
        case TimeScale.MONTHLY:
            return ["erefaom0"]
        case TimeScale.DAILY:
            return ["erefaod0"]
        case TimeScale.HOURLY:
            return ["erefaoh0"]
        case _:
            # Ten-minute evaporation data is not available
            raise ValueError(f"Unsupported timescale for evaporation: {timescale}")


DWH_CONVERTERS: dict[str, Callable[[TimeScale], list[str]]] = {
    "evaporation": _convert_evaporation,
    "humidity": _convert_humidity,
    "precipitation": _convert_precipitation,
    "pressure": _convert_pressure,
    "sunshine": _convert_sunshine,
    "temperature": _convert_temperature,
}

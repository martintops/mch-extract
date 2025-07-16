import argparse
from datetime import date, datetime, timedelta

from mchextract.dwhconverter import DWH_CONVERTERS
from mchextract.models import MchExtractArgs, MeteoData, TimeScale


def parse_args(metadata: MeteoData) -> MchExtractArgs:
    parser = argparse.ArgumentParser(
        description="mch-extract: A wrapper tool for extracting data from the MeteoSwiss OpenData API."
    )

    # example usage:
    # mch-extract --from 2023-01-01 --to 2023-01-31 --stations PAY --variables temperature --daily --output output.csv
    parser.add_argument(
        "--from",
        dest="start_date",
        required=True,
        help="Start date for data extraction in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--to",
        dest="end_date",
        required=False,
        help="End date for data extraction in YYYY-MM-DD format. Defaults to today if not provided.",
    )
    parser.add_argument(
        "--stations",
        required=True,
        help="3 letters target station code, space separated. E.g.: PAY VIT ROM",
        nargs="+",
    )
    parser.add_argument(
        "--variables",
        required=False,
        help="Target variables to extract. E.g.: temperature, precipitation",
        choices=DWH_CONVERTERS.keys(),
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--dwh",
        required=False,
        help="Additional parameters to be included. Must be DWH shortnames like 'dkl010h0'.",
        nargs="+",
        default=[],
    )
    parser.add_argument("--monthly", action="store_true", help="Extract monthly data.")
    parser.add_argument("--daily", action="store_true", help="Extract daily data.")
    parser.add_argument("--hourly", action="store_true", help="Extract hourly data.")
    parser.add_argument(
        "--ten-minute",
        action="store_true",
        help="Extract ten-minute data.",
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Output file path. Supported formats: CSV, parquet, JSON. Format is determined by the file extension (e.g., .csv, .parquet).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (debug output).",
    )

    args = parser.parse_args()
    # Ensure that at least one of --monthly, --daily, or --hourly is specified
    if not (args.monthly or args.daily or args.hourly or args.ten_minute):
        parser.error(
            "At least one of --monthly, --daily, --hourly, or --ten-minute must be specified."
        )

    # Convert boolean flags to timescale
    if args.monthly:
        args.timescale = TimeScale.MONTHLY
    elif args.daily:
        args.timescale = TimeScale.DAILY
    elif args.hourly:
        args.timescale = TimeScale.HOURLY
    elif args.ten_minute:
        args.timescale = TimeScale.TEN_MINUTE

    # Validate date format
    try:
        args.start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        if args.end_date:
            args.end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    except ValueError:
        parser.error("Date must be in YYYY-MM-DD format.")

    if not args.stations:
        parser.error("At least one station must be specified.")

    # Auto-adjust end-date if not provided
    if not args.end_date:
        today = date.today()
        if args.timescale in [TimeScale.HOURLY, TimeScale.TEN_MINUTE]:
            # End end is today if hourly or ten-minute data is requested
            args.end_date = today
        else:
            if args.timescale == TimeScale.MONTHLY:
                args.end_date = date(today.year, today.month, 1) - timedelta(days=1)
            elif args.timescale == TimeScale.DAILY:
                args.end_date = today - timedelta(days=1)

            if args.end_date < args.start_date:
                parser.error(
                    f"There are no valid dates for the requested timescale. Try starting earlier than {args.end_date}."
                )

    # Sanity check
    if args.start_date > args.end_date:
        parser.error(
            f"Start date must be before end date. Got start: {args.start_date}, end: {args.end_date}."
        )

    # Validate stations
    available_stations = {station.abbr for station in metadata.stations.values()}
    requested_stations = set(args.stations)
    if not requested_stations.issubset(available_stations):
        missing_stations = requested_stations - available_stations
        parser.error(
            f"The following requested stations are not available: {missing_stations}\n\n"
            + f"Available stations: {', '.join(sorted(available_stations))}"
        )

    return MchExtractArgs(
        start_date=args.start_date,
        end_date=args.end_date,
        stations=args.stations,
        variables=args.variables,
        parameters=args.dwh,
        timescale=args.timescale,
        output=args.output,
        verbose=args.verbose,
    )

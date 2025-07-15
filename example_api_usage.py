#!/usr/bin/env python3
"""
Example script demonstrating how to use mch-extract as a Python API.

This script shows different ways to extract meteorological data from MeteoSwiss
using the mchextract package programmatically.
"""

from datetime import date

import polars as pl

from mchextract import MchExtract, get_data


def simple_example():
    """Demonstrate simple one-off data extraction."""
    print("=== Simple Example ===")

    # Extract daily temperature and precipitation data for two stations
    data = get_data(
        stations=["PAY", "VIT"],  # Payerne and Visp stations
        variables=["temperature", "precipitation"],
        start_date=date(2023, 6, 1),
        end_date=date(2023, 6, 7),
        timescale="daily",
    )

    print(f"Downloaded {len(data)} rows of data")
    print("Data schema:")
    print(data.schema)
    print("\nFirst few rows:")
    print(data.head())

    return data


def advanced_example():
    """Demonstrate more advanced usage with the MchExtract class."""
    print("\n=== Advanced Example ===")

    # Create an extractor instance with verbose logging
    extractor = MchExtract(verbose=True)

    # Get available stations
    stations = extractor.get_available_stations()
    print(f"Available stations: {len(stations)} total")
    print(f"First 10 stations: {stations[:10]}")

    # Get station information
    station_info = extractor.get_station_info("PAY")
    if station_info:
        print("\nPayerne station info:")
        print(f"Name: {station_info['name']}")
        print(f"Canton: {station_info['canton']}")
        print(
            f"Coordinates: {station_info['coordinates_lat']:.4f}, {station_info['coordinates_lon']:.4f}"
        )
        print(f"Height: {station_info['height_masl']} m")
    else:
        print("\nStation 'PAY' not found")

    # Get available variables
    variables = extractor.get_available_variables()
    print(f"\nAvailable variables: {variables}")

    # Extract hourly data for a specific station
    data = extractor.get_data(
        stations="PAY",
        variables="temperature",
        start_date=date(2023, 6, 1),
        end_date=date(2023, 6, 2),
        timescale="hourly",
    )

    print("\nHourly data for Payerne:")
    print(f"Downloaded {len(data)} rows")
    print(data.head(10))

    return data


def data_analysis_example(data: pl.DataFrame):
    """Demonstrate basic data analysis with the extracted data."""
    print("\n=== Data Analysis Example ===")

    # Basic statistics
    print("Data summary:")
    print(data.describe())

    # Filter for specific station
    payerne_data = data.filter(pl.col("station_abbr") == "PAY")
    print(f"\nPayerne data: {len(payerne_data)} rows")

    # Calculate daily averages if we have sub-daily data
    if "tre200h0" in data.columns:  # Temperature column
        daily_avg = (
            payerne_data.with_columns(
                pl.col("reference_timestamp")
                .str.strptime(pl.Date, "%d.%m.%Y %H:%M")
                .alias("date")
            )
            .group_by("date")
            .agg(pl.col("tre200h0").mean().alias("avg_temperature"))
            .sort("date")
        )

        print("\nDaily average temperatures:")
        print(daily_avg)


def save_example(data: pl.DataFrame):
    """Demonstrate saving data in different formats."""
    print("\n=== Save Example ===")

    # Save as CSV
    data.write_csv("example_output.csv")
    print("Data saved as CSV: example_output.csv")

    # Save as Parquet (more efficient for large datasets)
    data.write_parquet("example_output.parquet")
    print("Data saved as Parquet: example_output.parquet")


def main():
    """Run all examples."""
    print("mch-extract API Examples")
    print("=" * 40)

    try:
        # Simple example
        data = simple_example()

        # Advanced example
        hourly_data = advanced_example()

        # Data analysis
        data_analysis_example(hourly_data)

        # Save examples
        save_example(data)

        print("\n=== All examples completed successfully! ===")

    except Exception as e:
        print(f"Error: {e}")
        print(
            "Make sure you have internet connection and the MeteoSwiss API is accessible."
        )


if __name__ == "__main__":
    main()

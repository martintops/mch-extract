# MCH-Extract: MeteoSwiss OpenData Extraction Tool

> **⚠️ DISCLAIMER**: This tool is **NOT official** and is **NOT affiliated** with MeteoSwiss. It is an independent project that provides convenient access to publicly available MeteoSwiss measurement data through the Open Government Data initiative.

A simple Python tool for downloading weather data from Switzerland's automatic ground-based weather stations. Designed for scientists and researchers who need easy access to publicly available [MeteoSwiss data](https://opendatadocs.meteoswiss.ch/) without dealing with the complexities of the FSDI REST API.

## What Does This Tool Do?

- **Download weather data** from Swiss weather stations with simple commands
- **Get data in different time intervals**: daily, hourly, monthly, or 10-minute measurements
- **Save data** in Excel-friendly CSV or efficient Parquet formats
- **Access data programmatically** in Python for analysis using [Polars](https://docs.pola.rs/) or Pandas
- **Handle data validation** automatically - just specify what you want

## Installation (pip)

Install using pip (requires Python 3.10 or newer). Note that using a [virtual environment](https://docs.python.org/3/library/venv.html) is recommended to avoid conflicts with other packages.

```bash
pip install mch-extract
```

Verify the tool is installed and working:

```bash
mch-extract --help
```

## Quick Run (using `uv`)

Run in a separate environment using [uv](https://github.com/astral-sh/uv):

```bash
uvx mch-extract -h
```

## Quick Examples

### Command Line (Terminal)

Get daily temperature and precipitation data for two stations:

```bash
mch-extract --from 2024-06-01 --to 2024-06-07 --stations PAY VIT --variables temperature precipitation --daily --output my_weather_data.csv
```

**📖 For more command-line examples and detailed usage, see [COMMANDS.md](COMMANDS.md)**

### In Python Scripts

```python
from datetime import date
from mchextract import get_data

# Download weather data as a Polars DataFrame
data = get_data(
    stations=['PAY', 'VIT'],  # Payerne and Villars-Tiercelin stations
    variables=['temperature', 'precipitation'],
    start_date=date(2024, 6, 1),
    end_date=date(2024, 6, 7),
    timescale='daily'
)

# If you prefer working with Pandas, you can convert the Polars DataFrame:
# data = data.to_pandas()
# (requires `pandas` and `pyarrow` packages to be installed separately)

print(f"Downloaded {len(data)} rows of data")
print(data.head())

# Save to file
data.write_csv("my_data.csv")
```

## How to Use

### Command Line Quick Reference

**Required:**

- `--from DATE`: Start date (YYYY-MM-DD format, e.g., 2024-06-01)
- `--stations CODES`: Weather station codes (e.g., PAY VIT ROM)
- **Time resolution**: Choose one of `--monthly`, `--daily`, `--hourly`, or `--10min`

**Optional:**

- `--to DATE`: End date (defaults to most recent valid date)
- `--variables VARS`: What to measure (e.g., temperature precipitation). If not set, will return all available parameters for the stations
- `--dwh PARAMS`: Additional MeteoSwiss DWH parameter short names to include. See below on how to find them.
- `--output FILE`: Where to save data. Supported formats are: `.csv`, `.json`, `.parquet`. If not set, will print CSV data to STDOUT
- `--verbose`: Show detailed progress information
- `--no-cache`: Disable caching (useful for testing or debugging)

**📖 For complete command-line reference and examples, see [COMMANDS.md](COMMANDS.md)**

### Available Weather Variables

As a convenience, some "easy to use" variables are provided. These will be automatically converted to DWH parameters for you.

- `temperature`: Air temperature
- `precipitation`: Rainfall and snow
- `pressure`: Atmospheric pressure
- `humidity`: Relative humidity
- `sunshine`: Sunshine duration
- `evaporation`: Evaporation measurements

### Time Intervals

- `--monthly`: Monthly averages
- `--daily`: One measurement per day
- `--hourly`: One measurement per hour
- `--10min`: Real-time measurements every 10 minutes

### Station Codes

Weather stations use 3-letter codes:

- `PAY`: Payerne
- `VIT`: Villars-Tiercelin
- `KLO`: Zurich/Kloten
- `GVE`: Geneva
- And many more...

If you use an invalid code, the tool will show you all available stations.

### References

[STAC browser](https://data.geo.admin.ch/browser/index.html#/collections/ch.meteoschweiz.ogd-smn?.language=en)

For the list of available stations and parameters, consult the following CSV files:

- List of regular stations (SMN): [ogd-smn_meta_stations.csv](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv)
- List of precipitation stations (SMN Precip): [ogd-smn-precip_meta_stations.csv](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn-precip/ogd-smn-precip_meta_stations.csv)

- List of regular parameters (SMN): [ogd-smn_meta_parameters.csv](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_parameters.csv)
- List of precipitation parameters (SMN Precip): [ogd-smn-precip_meta_parameters.csv](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn-precip/ogd-smn-precip_meta_parameters.csv)

- Inventory of regular stations (SMN): [ogd-smn_meta_datainventory.csv](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_datainventory.csv)
- Inventory of precipitation stations (SMN Precip): [ogd-smn-precip_meta_datainventory.csv](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn-precip/ogd-smn-precip_meta_datainventory.csv)

## Python API Examples

```python
from datetime import date
from mchextract import get_data

# Get recent weather for analysis
data = get_data(
    stations=['PAY', 'VIT'],
    variables=['temperature', 'precipitation'],
    start_date=date(2024, 6, 1),
    end_date=date(2024, 6, 7),
    timescale='daily'
)

# Basic data exploration
print(f"Data shape: {data.shape}")
print(f"Average temperature: {data['temperature'].mean():.1f}°C")
print(f"Total precipitation: {data['precipitation'].sum():.1f}mm")

# Save for Excel
data.write_csv("weather_analysis.csv")
```

## About the Data

### Swiss Weather Network

This tool accesses data from Switzerland's official weather monitoring network:

- **~160 complete weather stations**: Measure temperature, precipitation, wind, sunshine, humidity, radiation, and pressure
- **~100 precipitation stations**: Focus on rainfall and snow measurements

### Data Types Available

- **10-minute data**: Real-time measurements (updated every 20 minutes)
- **Hourly data**: Hourly summaries
- **Daily data**: Daily summaries (most common for research)
- **Monthly data**: Monthly climate summaries

### Data Coverage

- **Historical**: From when each station started until end of last year
- **Recent**: From January 1st of current year until yesterday
- **Real-time**: Current data (only for hourly and 10-minute intervals)

### Data Quality

- All data comes pre-processed from MeteoSwiss
- Quality control and validation already applied
- Follows international meteorological standards
- Some stations have data going back to 1981 or earlier

## Troubleshooting

### Common Problems

#### `mch-extract`: command not found

- Make sure you have installed the package correctly using `pip install mch-extract`.
- Check your PATH environment variable to ensure the `mch-extract` command is accessible.
- If using a virtual environment, make sure it is activated before running the command.

#### Invalid station code

- Check your 3-letter station codes (e.g., PAY, KLO, GVE)
- The tool will show available stations if you use an invalid code

#### No data available for date range

- Make sure your dates are in YYYY-MM-DD format
- Check that the date range is reasonable (not too far in the future)
- Some stations may not have all variables available

#### "Network error" or "Download failed"

- Check your internet connection
- MeteoSwiss servers might be temporarily unavailable

#### Need more help?

- Use `--verbose` to see detailed information about what's happening
- Check that your dates and station codes are correct

### Getting Detailed Output

Add `--verbose` to any command to see what the tool is doing:

```bash
mch-extract --from 2024-01-01 --stations PAY --variables temperature --daily --output debug.csv --verbose
```

## Important Notes

### Attribution

If using this data in publications or research, please consult MeteoSwiss guidelines on how to cite them. Data is provided under [Creative Commons License CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [Terms of use](https://opendatadocs.meteoswiss.ch/general/terms-of-use).

### Disclaimer

- This tool is **NOT official** and **NOT affiliated** with MeteoSwiss
- It provides convenient access to publicly available MeteoSwiss OpenData
- For climate analyses, consider MeteoSwiss' [official climate data products](https://opendatadocs.meteoswiss.ch/c-climate-data)

### Data Usage

- All data comes from MeteoSwiss OpenData and can be used freely
- Please respect MeteoSwiss servers - don't make excessive requests
- For large-scale or commercial usage, consider contacting MeteoSwiss directly
- This tool is not meant to be integrated into any automated solutions

## Development and Contributing

This project is open source. For developers interested in:

- Setting up a development environment
- Running tests
- Contributing code
- Building from source

Please see [DEVELOPMENT.md](DEVELOPMENT.md) for detailed technical documentation.

## Learn More

- [MeteoSwiss OpenData Documentation](https://opendatadocs.meteoswiss.ch/)
- [Weather Station Network Information](https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations)
- [Interactive Station Map](https://www.meteoswiss.admin.ch/services-and-publications/applications/measurement-values-and-measuring-networks.html#param=messnetz-automatisch&lang=en)
- [MeteoSwiss Open Data Explorer](https://www.meteoswiss.admin.ch/services-and-publications/applications/ext/download-data-without-coding-skills.html)

### Keywords

MeteoSwiss, MeteoSchweiz, MétéoSuisse, data extraction, OpenData, wrapper, Python API, Python package

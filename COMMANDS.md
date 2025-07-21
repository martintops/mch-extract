# Command Line Reference

## mch-extract

A wrapper tool for extracting data from the MeteoSwiss OpenData API.

## Synopsis

`mch-extract [common-flags] --from <YYYY-MM-DD> --stations <S1 S2 S3> -v <variable variable2> -o <output_file> [options...]`

## Description  

### Common Flags

| Flag           | Args | Description                       |
| -------------- | ---- | --------------------------------- |
| `-h`, `--help` |      | Show help message and exit.       |
| `--verbose`    |      | Enable verbose output.            |
| `--no-cache`   |      | Disable caching of API responses. |

### Station Selection

| Flag               | Args                                 | Description                                                           |
| ------------------ | ------------------------------------ | --------------------------------------------------------------------- |
| `-s`, `--stations` | `<station_abbr> <station_abbr2> ...` | Space-separated list of target station abbreviations. E.g.: `PAY VIT`. **Required.** |

### Time Options

#### Range Selection

| Flag     | Args           | Description                                                                    |
| -------- | -------------- | ------------------------------------------------------------------------------ |
| `--from` | `<YYYY-MM-DD>` | Specify the start date for the data extraction. **Required.**                      |
| `--to`   | `<YYYY-MM-DD>` | Specify the end date for the data extraction. Defaults to last available date. |

#### Granularity Options

Specify the granularity of the data to be extracted. Exactly **one** of these options is **required**.

| Flag        | Description                              |
| ----------- | ---------------------------------------- |
| `--10min`   | Extract data at a 10-minute granularity. |
| `--hourly`  | Extract data at an hourly granularity.   |
| `--daily`   | Extract data at a daily granularity.     |
| `--monthly` | Extract data at a monthly granularity.   |

### Variable and Parameter Options

Both `-v` and `--dwh` can be combined. If nothing is specified, all available parameters for the specified stations will be extracted.

| Flag                | Args                                     | Description                               |
| ------------------- | ---------------------------------------- | ----------------------------------------- |
| `-v`, `--variables` | `<variable_group> <variable_group2> ...` | Specify the variable group(s) to extract. |
| `--dwh`             | `<parameter_name> <parameter_name2> ...` | Specify the DWH parameters to extract.    |
| `--short`           |                                          | Use short parameter names in the output.  |

Available variable groups are:

| Code            | Corresponding DWH Parameters | Description                                                                                 | Unit |
| --------------- | ---------------------------- | ------------------------------------------------------------------------------------------- | ---- |
| `evaporation`   | `erefaox0`                   | Reference evaporation from FAO.                                                             | mm/d |
| `humidity`      | `ure200x0`                   | Relative air humidity 2 m above ground.                                                     | %    |
| `precipitation` | `rre150x0`/`rka150d0`        | Precipitation. Note: Daily includes both 6UTC-6UTC (`rre150x0`) and 0UTC-0UTC (`rka150d0`). | mm   |
| `pressure`      | `prestax0`                   | Atmospheric pressure at barometric altitude (QFE).                                          | hPa  |
| `sunshine`      | `sre000x0`                   | Sunshine duration.                                                                          | min  |
| `temperature`   | `tre200x0`                   | Air temperature 2 m above ground.                                                           | °C   |

### Output Arguments

| Flag             | Args            | Description                                                               |
| ---------------- | --------------- | ------------------------------------------------------------------------- |
| `-o`, `--output` | `<output_file>` | Specify the output file path. If not provided, data is printed to stdout. |

The output format will be determined by the file extension of the output file. Supported formats include:

| Format  | File Extension |
| ------- | -------------- |
| CSV     | `.csv`         |
| Parquet | `.parquet`     |
| JSON    | `.json`        |

Other formats will default to CSV.

## Examples

### Basic Usage

Get daily temperature and precipitation data for two stations:

```bash
mch-extract --from 2024-06-01 --to 2024-06-07 \
    --stations PAY VIT \
    --variables temperature precipitation \
    --daily \
    --output my_weather_data.csv
```

Get hourly temperature data with detailed output:

```bash
mch-extract --from 2024-06-01 \
    --stations PAY \
    --variables temperature \
    --hourly \
    --output hourly_temp.csv \
    --verbose
```

### Advanced Examples

Download precipitation data for multiple stations:

```bash
mch-extract --from 2024-01-01 --to 2024-01-31 \
    --stations PAY VIT ROM \
    --variables precipitation \
    --hourly \
    --output rain_data.csv
```

Get temperature and humidity for Zurich area:

```bash
mch-extract --from 2024-12-01 --to 2024-12-31 \
    --stations KLO \
    --variables temperature humidity \
    --daily \
    --output zurich_weather.csv
```

Monthly climate summary for Geneva:

```bash
mch-extract --from 2024-01-01 --to 2025-01-01 \
    --stations GVE \
    --variables temperature precipitation pressure \
    --monthly \
    --output geneva_climate.csv
```

### Output to Different Formats

Save data as Parquet for efficient storage:

```bash
mch-extract --from 2024-06-01 --to 2024-06-07 \
    --stations PAY \
    --variables temperature \
    --daily \
    --output weather_data.parquet
```

Print data to terminal (no output file specified):

```bash
mch-extract --from 2024-06-01 --to 2024-06-07 \
    --stations PAY \
    --variables temperature \
    --daily
```

### Using DWH Parameters Directly

Extract specific MeteoSwiss DWH parameters:

```bash
mch-extract --from 2024-06-01 --to 2024-06-07 \
    --stations PAY \
    --dwh tre200x0 ure200x0 \
    --daily \
    --output specific_params.csv
```

### Debugging and Troubleshooting

Use verbose mode to see detailed information:

```bash
mch-extract --from 2024-06-01 \
    --stations PAY \
    --variables temperature \
    --daily \
    --output debug.csv \
    --verbose
```

Disable caching for testing:

```bash
mch-extract --from 2024-06-01 \
    --stations PAY \
    --variables temperature \
    --daily \
    --output test.csv \
    --no-cache
```

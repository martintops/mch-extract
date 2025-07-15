import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from mchextract.consts import DATA_SOURCES, DEFAULT_CACHE_DIR, DataSource


class MetaDataDownloader:
    """Manages MeteoSwiss station data with local caching for multiple data sources."""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR):
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(exist_ok=True)
        self._logger = logging.getLogger(__name__)

    def _fetch_collection_metadata(self, data_source: DataSource) -> dict[str, Any]:
        """Fetch the STAC collection metadata from the API for a specific data source."""
        try:
            response = requests.get(data_source.collection_url, timeout=30)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.RequestException as e:
            raise Exception(
                f"Failed to fetch collection metadata for {data_source.name}: {e}"
            ) from e

    def _get_cache_file_path(self, data_source: DataSource, file_type: str) -> Path:
        """Get the cache file path for a specific data source and file type."""
        filename = data_source.meta_files[file_type]
        return self._cache_dir / filename

    def _get_local_cache_info(
        self, data_source: DataSource
    ) -> dict[str, datetime | None]:
        """Get the modification times of locally cached CSV files for a data source."""
        cache_info: dict[str, datetime | None] = {}
        for file_type in data_source.meta_files:
            file_path = self._get_cache_file_path(data_source, file_type)
            if file_path.exists():
                cache_info[file_type] = datetime.fromtimestamp(
                    file_path.stat().st_mtime
                )
            else:
                cache_info[file_type] = None
        return cache_info

    def _parse_updated_date(self, date_string: str) -> datetime:
        """Parse ISO format date string to datetime object."""
        # Remove 'Z' and parse the datetime
        if date_string.endswith("Z"):
            date_string = date_string[:-1] + "+00:00"
        return datetime.fromisoformat(date_string).replace(tzinfo=None)

    def _needs_cache_update(
        self, collection_data: dict, data_source: DataSource
    ) -> dict[str, bool]:
        """Check which CSV files need to be updated based on remote metadata."""
        local_cache = self._get_local_cache_info(data_source)
        needs_update: dict[str, bool] = {}

        assets = collection_data.get("assets", {})

        for file_type in data_source.meta_files:
            filename = data_source.meta_files[file_type]
            # Check if file exists locally
            local_modified = local_cache[file_type]
            if local_modified is None:
                needs_update[file_type] = True
                continue

            # Check if remote file has newer update time
            if filename in assets:
                remote_updated = self._parse_updated_date(assets[filename]["updated"])
                needs_update[file_type] = remote_updated > local_modified
            else:
                # If no remote info, assume update needed
                needs_update[file_type] = True

        return needs_update

    def _download_csv_file(
        self, data_source: DataSource, file_type: str, url: str
    ) -> None:
        """Download a single CSV file to the cache directory, converting from Windows-1252 to UTF-8."""
        file_path = self._get_cache_file_path(data_source, file_type)
        filename = data_source.meta_files[file_type]

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            # Decode from Windows-1252 and encode as UTF-8
            try:
                # First try to decode as Windows-1252
                content_text = response.content.decode("windows-1252")
                # Then encode as UTF-8
                utf8_content = content_text.encode("utf-8")
            except UnicodeDecodeError:
                # Fallback to UTF-8 if Windows-1252 fails
                self._logger.warning(
                    f"Could not decode {filename} as Windows-1252, using UTF-8"
                )
                utf8_content = response.content

            with open(file_path, "wb") as f:
                f.write(utf8_content)

        except requests.RequestException as e:
            raise Exception(f"Failed to download {filename}: {e}") from e

    def _update_cache(self, collection_data: dict, data_source: DataSource) -> None:
        """Download CSV files that need updating for a specific data source."""
        needs_update = self._needs_cache_update(collection_data, data_source)
        assets = collection_data.get("assets", {})

        for file_type, should_update in needs_update.items():
            if should_update:
                filename = data_source.meta_files[file_type]
                if filename in assets:
                    url = assets[filename]["href"]
                    self._download_csv_file(data_source, file_type, url)
                else:
                    self._logger.warning(
                        f"{filename} not found in remote assets for {data_source.name}"
                    )

    def ensure_data_available(self) -> dict[str, dict]:
        """Fetch metadata and ensure local cache is up to date for all data sources."""
        collection_data = {}

        for data_source in DATA_SOURCES:
            try:
                self._logger.debug(
                    f"Updating cache for data source: {data_source.name}"
                )
                source_collection = self._fetch_collection_metadata(data_source)
                self._update_cache(source_collection, data_source)
                collection_data[data_source.name] = source_collection
            except Exception as e:
                self._logger.warning(
                    f"Failed to update cache for {data_source.name}: {e}"
                )
                # Continue with other data sources

        return collection_data

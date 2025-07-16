import hashlib
import json
import logging
from pathlib import Path
from typing import TypedDict
from urllib.parse import urljoin

import requests

from .consts import DEFAULT_CACHE_DIR, REQUEST_TIMEOUT_S


class CacheMetadata(TypedDict):
    """Metadata stored in cache for downloaded files."""

    etag: str | None
    content_length: int
    content_type: str | None
    last_modified: str | None
    checksum: str | None


class CachedDownloader:
    """A class that provides a cached downloader interface.
    It uses ETag and If-Match to handle caching and conditional requests.
    """

    def __init__(self, cache_enabled: bool = True, cache_dir: Path = DEFAULT_CACHE_DIR):
        self._logger = logging.getLogger(__name__)
        self._cache_enabled = cache_enabled
        self._cache_dir = cache_dir
        # Ensure cache directory exists
        if self._cache_enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def download(self, base_url: str, file: str) -> bytes:
        """Download a file from the given URL, using cache if available.
        Args:
            base_url (str): The base URL to download from.
            file (str): The file to download.
        Returns:
            bytes: The content of the downloaded file at base_url/file, or from cache if available.
        """
        url = self._build_url(base_url, file)

        if not self._cache_enabled:
            self._logger.debug(f"Cache disabled, downloading directly: {url}")
            return self._download_direct(url).content

        # Create cache file paths
        cache_file_path = self._cache_dir / file
        cache_meta_path = self._cache_dir / f"{file}.meta"

        # Ensure cache subdirectories exist
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing metadata if available
        existing_etag = self._load_existing_etag(cache_meta_path)
        if existing_etag:
            self._logger.debug(f"Found existing ETag for {file}: {existing_etag}")
        else:
            self._logger.debug(f"No ETag found for {file}, will download.")

        # Make request with conditional headers
        headers = {}
        if existing_etag:
            headers["If-None-Match"] = existing_etag

        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_S)

        if response.status_code == 304:
            # Not modified, return cached content
            if cache_file_path.exists():
                self._logger.debug(f"Cache hit for {file}, using cached file.")
                return cache_file_path.read_bytes()
            else:
                self._logger.debug(
                    f"Cache metadata present but file missing for {file}, re-downloading."
                )
                # Cache file missing, force re-download
                response = self._download_direct(url)
                return self._save_to_cache(response, cache_file_path, cache_meta_path)

        elif response.status_code == 200:
            # New or modified content
            self._logger.debug(
                f"Downloaded new or updated file for {file}, updating cache. Previous ETag: {existing_etag}, New ETag: {response.headers.get('ETag')}"
            )
            return self._save_to_cache(response, cache_file_path, cache_meta_path)

        else:
            # Handle error status codes
            self._logger.debug(
                f"Download failed for {file} with status {response.status_code}"
            )
            response.raise_for_status()
            return b""  # This line should never be reached due to raise_for_status()

    def _build_url(self, base_url: str, file: str) -> str:
        """Build the full URL from base URL and file path."""
        return urljoin(base_url.rstrip("/") + "/", file)

    def _load_existing_etag(self, cache_meta_path: Path) -> str | None:
        """Load existing ETag from metadata file."""
        if not cache_meta_path.exists():
            return None

        try:
            with open(cache_meta_path) as f:
                metadata: CacheMetadata = json.load(f)
                return metadata.get("etag")
        except (OSError, json.JSONDecodeError):
            # If metadata is corrupted, ignore and re-download
            return None

    def _download_direct(self, url: str) -> requests.Response:
        """Download file directly without caching."""
        response = requests.get(url, timeout=REQUEST_TIMEOUT_S)
        response.raise_for_status()

        # Verify checksum if provided
        expected_checksum = response.headers.get("X-Amz-Meta-Sha256")
        if expected_checksum:
            actual_checksum = hashlib.sha256(response.content).hexdigest()
            if actual_checksum != expected_checksum:
                raise ValueError(
                    f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                )

        return response

    def _save_to_cache(
        self, response: requests.Response, cache_file_path: Path, cache_meta_path: Path
    ) -> bytes:
        """Save response content and metadata to cache."""
        content = response.content

        # Save content to cache
        cache_file_path.write_bytes(content)

        # Save metadata
        metadata: CacheMetadata = {
            "etag": response.headers.get("ETag"),
            "content_length": len(content),
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
            "checksum": response.headers.get("X-Amz-Meta-Sha256"),
        }

        with open(cache_meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return content

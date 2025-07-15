"""Basic tests for mch-extract package."""

from mchextract import MchExtract, TimeScale, get_data

# TODO


def test_import():
    """Test that the package can be imported."""
    assert MchExtract is not None
    assert get_data is not None
    assert TimeScale is not None

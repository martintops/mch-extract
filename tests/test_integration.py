from datetime import date

from mchextract import get_data


def test_simple_daily():
    # simple test for daily data extraction
    # single historical decade, data shouldn't change anymore
    data = get_data(
        stations=["PAY"],
        variables=["temperature"],
        start_date=date(2020, 2, 1),
        end_date=date(2020, 8, 7),
        timescale="daily",
    )
    # Total should be 189 days (end inclusive)
    assert len(data) == 189
    # assert 3 columns
    assert data.columns == ["station_abbr", "reference_timestamp", "tre200d0"]
    # assert first row
    assert data[0, 0] == "PAY"
    assert data[0, 1] == "01.02.2020 00:00"
    assert data[0, 2] == "9.6"
    # assert last row
    assert data[-1, 0] == "PAY"
    assert data[-1, 1] == "07.08.2020 00:00"
    assert data[-1, 2] == "20.9"


def test_double_daily():
    # simple test for daily data extraction
    # single historical decade, data shouldn't change anymore
    data = get_data(
        stations=["PAY", "VIT"],
        variables=["temperature"],
        start_date=date(2020, 2, 1),
        end_date=date(2020, 8, 7),
        timescale="daily",
    )
    # Total should be 189 days * 2 stations = 378 rows (end inclusive)
    assert len(data) == 378
    # assert 3 columns
    assert data.columns == ["station_abbr", "reference_timestamp", "tre200d0"]
    # assert first row
    assert data[0, 0] == "PAY"
    assert data[0, 1] == "01.02.2020 00:00"
    assert data[0, 2] == "9.6"
    # assert last row
    assert data[-1, 0] == "VIT"
    assert data[-1, 1] == "07.08.2020 00:00"
    assert data[-1, 2] == "19.7"


def test_simple_two_variables():
    # simple test for daily data extraction
    # single historical decade, data shouldn't change anymore
    data = get_data(
        stations=["PAY"],
        variables=["temperature", "precipitation"],
        start_date=date(2020, 2, 1),
        end_date=date(2020, 8, 7),
        timescale="daily",
    )
    # Total should be 189 days (end inclusive)
    assert len(data) == 189
    # assert 4 columns
    assert data.columns == [
        "station_abbr",
        "reference_timestamp",
        "tre200d0",
        "rre150d0",
        "rka150d0",
    ]
    # assert first row
    assert data[0, 0] == "PAY"
    assert data[0, 1] == "01.02.2020 00:00"
    assert data[0, 2] == "9.6"
    assert data[0, 3] == "0.6"
    assert data[0, 4] == "0.6"
    # assert last row
    assert data[-1, 0] == "PAY"
    assert data[-1, 1] == "07.08.2020 00:00"
    assert data[-1, 2] == "20.9"
    assert data[-1, 3] == "0"
    assert data[-1, 4] == "0"


def test_double_two_variables_missing():
    # simple test for daily data extraction
    # single historical decade, data shouldn't change anymore
    data = get_data(
        stations=["PAY", "VIT"],
        variables=["temperature", "pressure"],
        start_date=date(2020, 2, 1),
        end_date=date(2020, 8, 7),
        timescale="daily",
    )
    # Total should be 189 days * 2 stations = 378 rows (end inclusive)
    assert len(data) == 378
    # assert 4 columns
    assert data.columns == [
        "station_abbr",
        "reference_timestamp",
        "tre200d0",
        "prestad0",
    ]
    # assert first row
    assert data[0, 0] == "PAY"
    assert data[0, 1] == "01.02.2020 00:00"
    assert data[0, 2] == "9.6"
    assert data[0, 3] == "958.8"
    # assert last row
    assert data[-1, 0] == "VIT"
    assert data[-1, 1] == "07.08.2020 00:00"
    assert data[-1, 2] == "19.7"
    assert data[-1, 3] is None

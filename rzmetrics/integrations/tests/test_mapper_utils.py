from datetime import datetime, timezone

import pytest

from integrations.mappers.mapper_utils import parse_datetime


def test_parse_datetime_none():
    assert parse_datetime(None) is None


def test_parse_datetime_empty_string():
    assert parse_datetime("") is None


def test_parse_datetime_iso_with_z_suffix():
    result = parse_datetime("2025-08-15T18:30:00Z")
    assert result == datetime(2025, 8, 15, 18, 30, 0, tzinfo=timezone.utc)


def test_parse_datetime_iso_with_offset():
    result = parse_datetime("2025-01-01T12:00:00+03:00")
    assert result.hour == 12

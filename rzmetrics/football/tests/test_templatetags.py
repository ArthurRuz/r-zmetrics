import pytest

from football.templatetags.age_filter import age_word, pluralize_age
from football.templatetags.dict_filters import get_item
from football.templatetags.market_value_filter import market_value_format
from football.templatetags.split_filter import split_filter


@pytest.mark.parametrize(
    "age,expected_word",
    [
        (1, "год"),
        (2, "года"),
        (5, "лет"),
        (11, "лет"),
        (21, "год"),
        (22, "года"),
        (25, "лет"),
    ],
)
def test_pluralize_age(age, expected_word):
    assert pluralize_age(age) == expected_word


@pytest.mark.parametrize(
    "age,expected",
    [
        (25, "25 лет"),
        (1, "1 год"),
        (3, "3 года"),
        (None, ""),
    ],
)
def test_age_word(age, expected):
    assert age_word(age) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (5_000_000, "5 млн €"),
        (1_500_000, "1.5 млн €"),
        (10_000_000, "10 млн €"),
        (500_000, "500 тыс €"),
        (1_000, "1 тыс €"),
        (500, "500 €"),
        (None, ""),
        ("invalid", "invalid"),
    ],
)
def test_market_value_format(value, expected):
    assert market_value_format(value) == expected


def test_get_item_filter():
    data = {"key": "value", "num": 42}
    assert get_item(data, "key") == "value"
    assert get_item(data, "missing") is None


@pytest.mark.parametrize(
    "value,delimiter,expected",
    [
        ("a,b,c", ",", ["a", "b", "c"]),
        ("one|two", "|", ["one", "two"]),
        ("single", ",", ["single"]),
        (123, ",", 123),
    ],
)
def test_split_filter(value, delimiter, expected):
    assert split_filter(value, delimiter) == expected

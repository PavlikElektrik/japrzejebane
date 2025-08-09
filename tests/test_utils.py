from datetime import datetime

import pandas as pd
import pytest

from src import utils


def test_format_date():
    dt = datetime.strptime("2021-12-31 16:44:00", "%Y-%m-%d %H:%M:%S")
    assert utils.format_date(dt) == "31.12.2021"
    assert utils.format_date(None) is None


def test_get_greeting():
    assert utils.get_greeting("2021-12-31 06:00:00") == "Доброе утро"
    assert utils.get_greeting("2021-12-31 13:00:00") == "Добрый день"
    assert utils.get_greeting("2021-12-31 19:00:00") == "Добрый вечер"
    assert utils.get_greeting("2021-12-31 02:00:00") == "Доброй ночи"
    with pytest.raises(ValueError):
        utils.get_greeting()


def test_load_transactions_excel(tmp_path):
    df_input = pd.DataFrame(
        {"Сумма операции": ["100", "200"], "Дата операции": ["01.01.2023 10:00:00", "02.01.2023 12:00:00"]}
    )
    file_path = tmp_path / "ops.xlsx"
    df_input.to_excel(file_path, index=False, engine="openpyxl")
    df = utils.load_transactions_excel(file_path)
    assert pd.api.types.is_numeric_dtype(df["Сумма операции"])
    assert pd.api.types.is_datetime64_any_dtype(df["Дата операции"])


def test_load_user_settings():
    settings = utils.load_user_settings()
    assert isinstance(settings, dict)
    assert "user_currencies" in settings
    assert "user_stocks" in settings


def test_greeting_by_time():
    assert utils.greeting_by_time(datetime(2023, 1, 1, 6)) == "Доброе утро"
    assert utils.greeting_by_time(datetime(2023, 1, 1, 13)) == "Добрый день"
    assert utils.greeting_by_time(datetime(2023, 1, 1, 19)) == "Добрый вечер"
    assert utils.greeting_by_time(datetime(2023, 1, 1, 3)) == "Доброй ночи"


def test_month_start_and_target():
    start, target = utils.month_start_and_target("2023-03-15 12:34:56")
    assert start.day == 1 and start.hour == 0
    assert target == datetime(2023, 3, 15, 12, 34, 56)


def test_filter_transactions_by_range(sample_transactions_df):
    start = datetime(2021, 12, 20)
    end = datetime(2021, 12, 31, 23, 59)
    filtered = utils.filter_transactions_by_range(sample_transactions_df, start, end)
    assert not filtered.empty
    assert all(start <= d <= end for d in filtered["Дата операции"])


def test_get_currency_rates():
    rates = utils.get_currency_rates(["USD", "EUR"])
    assert isinstance(rates, list)
    assert any(r["currency"] == "USD" and r["rate"] == 73.21 for r in rates)
    assert any(r["currency"] == "EUR" and r["rate"] == 87.08 for r in rates)


def test_get_currency_rates_error(monkeypatch):
    def fail_get(*args, **kwargs):
        raise Exception("fail")

    monkeypatch.setattr("requests.get", fail_get)
    rates = utils.get_currency_rates(["USD"])
    assert rates == [{"currency": "USD", "rate": None}]


def test_get_stock_prices():
    prices = utils.get_stock_prices(["AAPL", "AMZN"])
    assert isinstance(prices, list)
    assert any(p["stock"] == "AAPL" and p["price"] == 150.12 for p in prices)
    assert any(p["stock"] == "AMZN" and p["price"] == 3173.18 for p in prices)


def test_get_stock_prices_error(monkeypatch):
    def fail_get(*args, **kwargs):
        raise Exception("fail")

    monkeypatch.setattr("requests.get", fail_get)
    prices = utils.get_stock_prices(["AAPL"])
    assert prices == [{"stock": "AAPL", "price": None}]


def test_cards_summary(sample_transactions_df):
    cards = utils.cards_summary(sample_transactions_df)
    assert isinstance(cards, list)
    for card in cards:
        assert "last_digits" in card
        assert "total_spent" in card
        assert "cashback" in card


def test_top_transactions(sample_transactions_df):
    top = utils.top_transactions(sample_transactions_df, top_n=1)
    assert len(top) == 1
    t = top[0]
    assert "date" in t and "amount" in t and "category" in t and "description" in t

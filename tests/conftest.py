import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def mock_user_settings(monkeypatch):
    fake_settings = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]}

    def fake_load_user_settings(*args, **kwargs):
        return fake_settings

    monkeypatch.setattr("src.utils.load_user_settings", fake_load_user_settings)


@pytest.fixture(autouse=True)
def mock_requests_get(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                if "exchangerate.host" in url:
                    return {"rates": {"USD": 73.21, "EUR": 87.08}}
                if "financialmodelingprep" in url:
                    return [{"symbol": "AAPL", "price": 150.12}, {"symbol": "AMZN", "price": 3173.18}]
                return {}

        return FakeResponse()

    monkeypatch.setattr("requests.get", fake_get)


@pytest.fixture
def sample_transactions_df():
    data = {
        "Дата операции": ["2021-12-31 16:44:00", "2021-12-20 10:30:00"],
        "Номер карты": ["*7197", "*5814"],
        "Сумма платежа": [-160.89, -200.00],
        "Категория": ["Супермаркеты", "Переводы"],
        "Описание": ["Колхоз", "Перевод Кредитная карта. ТП 10.2 RUR"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


@pytest.fixture
def sample_transactions_list():
    return [
        {"Дата операции": "2021-12-31 16:44:00", "Категория": "Супермаркеты", "Описание": "Колхоз"},
        {"Дата операции": "2021-12-20 10:30:00", "Категория": "Переводы", "Описание": "Перевод Кредитная карта"},
    ]


@pytest.fixture
def mock_currency_rates():
    return [{"currency": "USD", "rate": 73.21}, {"currency": "EUR", "rate": 87.08}]


@pytest.fixture
def mock_stock_prices():
    return [{"stock": "AAPL", "price": 150.12}, {"stock": "AMZN", "price": 3173.18}]

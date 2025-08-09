import json

from src import views


def test_main_view(monkeypatch, sample_transactions_df, mock_user_settings, mock_currency_rates, mock_stock_prices):
    monkeypatch.setattr("src.views.load_transactions_excel", lambda: sample_transactions_df)
    monkeypatch.setattr("src.views.load_user_settings", lambda: mock_user_settings)
    monkeypatch.setattr("src.views.get_currency_rates", lambda currencies: mock_currency_rates)
    monkeypatch.setattr("src.views.get_stock_prices", lambda stocks: mock_stock_prices)

    result_json = views.main_view("2021-12-31 16:44:00")
    result = json.loads(result_json)

    assert "greeting" in result
    assert "cards" in result
    assert isinstance(result["cards"], list)
    assert "top_transactions" in result
    assert "currency_rates" in result
    assert "stock_prices" in result

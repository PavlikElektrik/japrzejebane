from typing import Any, Dict, List

from src.reports import spending_by_category
from src.services import simple_search
from src.utils import (
    CurrencyRate,
    StockPrice,
    cards_summary,
    get_currency_rates,
    get_stock_prices,
    load_transactions_excel,
    top_transactions,
)
from src.views import main_view


def run_all() -> None:
    df = load_transactions_excel()
    # settings = {}   # Можно загрузить, если нужно

    # spending_by_category возвращает Dict[str, Any]
    report: Dict[str, Any] = spending_by_category(df, category="Переводы", date="2025-08-09")
    print("Report:", report)

    # simple_search возвращает строку JSON
    # Приводим df к list[dict[str, Any]] — чтобы не было ошибок mypy
    transactions_list: List[Dict[str, Any]] = [
        {str(k): v for k, v in record.items()} for record in df.to_dict(orient="records")
    ]
    search: str = simple_search("магазин", transactions_list, limit=5)
    print("Search:", search)

    # main_view возвращает JSON-строку (вероятно)
    view_json: str = main_view("2025-08-09 00:00:00")
    print("View:", view_json)

    # cards_summary возвращает список словарей с картами
    cards: List[Dict[str, Any]] = cards_summary(df)
    print("Cards summary:", cards)

    # top_transactions возвращает список словарей с топ-транзакциями
    top: List[Dict[str, Any]] = top_transactions(df)
    print("Top transactions:", top)

    # get_currency_rates возвращает список словарей с курсами валют
    rates: List[CurrencyRate] = get_currency_rates(["USD", "EUR"])
    print("Currency rates:", rates)

    # get_stock_prices возвращает список словарей с ценами акций
    stocks: List[StockPrice] = get_stock_prices(["AAPL", "TSLA"])
    print("Stock prices:", stocks)


if __name__ == "__main__":
    run_all()

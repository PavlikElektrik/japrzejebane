import json
import logging
from datetime import datetime

from .utils import (
    cards_summary,
    filter_transactions_by_range,
    get_currency_rates,
    get_stock_prices,
    greeting_by_time,
    load_transactions_excel,
    load_user_settings,
    month_start_and_target,
    top_transactions,
)

logger = logging.getLogger(__name__)


def main_view(date_str: str) -> str:
    logger.info(f"main_view called with {date_str}")
    start_date, end_date = month_start_and_target(date_str)

    df = load_transactions_excel()
    df_filtered = filter_transactions_by_range(df, start_date, end_date)

    cards = cards_summary(df_filtered)
    top = top_transactions(df_filtered, top_n=5)

    settings = load_user_settings()
    if settings is None:
        settings = {}
    user_currencies = settings.get("user_currencies", [])
    user_stocks = settings.get("user_stocks", [])

    currency_rates = get_currency_rates(user_currencies)
    stock_prices = get_stock_prices(user_stocks)

    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    greeting = greeting_by_time(dt)

    response = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    return json.dumps(response, ensure_ascii=False, indent=2)

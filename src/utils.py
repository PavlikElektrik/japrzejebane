import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

import pandas as pd
import requests
from dotenv import load_dotenv
from config import DATA_DIR, ROOT_DIR

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

DATA_FILE = DATA_DIR / "operations.xlsx"
USER_SETTINGS_FILE = ROOT_DIR / "user_settings.json"


def get_greeting(datetime_str: Optional[str] = None) -> str:
    if datetime_str:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        return greeting_by_time(dt)
    raise ValueError("datetime_str required")


def format_date(dt: Optional[datetime], fmt: str = "%d.%m.%Y") -> Optional[str]:
    return dt.strftime(fmt) if dt else None


def load_transactions_excel(path: Optional[Path] = None) -> pd.DataFrame:
    """Считать transactions из Excel в DataFrame."""
    p = path or DATA_FILE
    logger.info("Loading transactions from %s", p)
    df = pd.read_excel(p, engine="openpyxl", dtype=str)

    # Приводим числовые колонки
    num_cols = ["Сумма операции", "Сумма платежа", "Кэшбэк", "Сумма операции с округлением"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Парсим даты
    date_cols = ["Дата операции", "Дата платежа"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d.%m.%Y %H:%M:%S", errors="coerce")

    return df


def load_user_settings(path: Optional[Path] = None) -> Dict[str, Any]:
    p = path or USER_SETTINGS_FILE
    logger.info("Loading user settings from %s", p)
    with open(p, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    return data


def greeting_by_time(dt: datetime) -> str:
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def month_start_and_target(date_str: str) -> Tuple[datetime, datetime]:
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, dt


def filter_transactions_by_range(df: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
    if "Дата операции" not in df.columns:
        logger.warning("Дата операции column not found")
        return pd.DataFrame()
    mask = (df["Дата операции"] >= start) & (df["Дата операции"] <= end)
    return df.loc[mask].copy()


class CurrencyRate(TypedDict):
    currency: str
    rate: Optional[float]


def get_currency_rates(
        currencies: List[str], base: str = "RUB", settings: Optional[Dict[str, Any]] = None
) -> List[CurrencyRate]:
    """Возвращает список курсов в формате [{currency, rate}, ...]"""
    settings = settings or load_user_settings()
    api_conf = settings.get("exchange_api", {})
    if not isinstance(api_conf, dict):
        api_conf = {}
    url = api_conf.get("base_url", "https://api.exchangerate.host/latest")

    logger.info("Requesting currency rates for %s", currencies)
    try:
        resp = requests.get(url, params={"base": base, "symbols": ",".join(currencies)})
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates", {})
        result: List[CurrencyRate] = []
        for cur in currencies:
            rate_val = rates.get(cur)
            rate: Optional[float]
            if rate_val is None:
                rate = None
            else:
                try:
                    rate = float(rate_val)
                except (TypeError, ValueError):
                    rate = None
            result.append({"currency": cur, "rate": rate})
        return result
    except Exception as e:
        logger.exception("Failed to fetch currency rates: %s", e)
        return [{"currency": cur, "rate": None} for cur in currencies]


class StockPrice(TypedDict):
    stock: str
    price: Optional[float]


def get_stock_prices(stocks: List[str], settings: Optional[Dict[str, Any]] = None) -> List[StockPrice]:
    """Возвращает список цен акций в формате [{stock, price}, ...]"""
    api_key = os.getenv("FMP_API_KEY")
    base_url = "https://financialmodelingprep.com/api/v3/quote"
    symbols = ",".join(stocks)
    url = f"{base_url}/{symbols}"
    if api_key:
        url += f"?apikey={api_key}"

    logger.info("Requesting stock prices for %s", stocks)
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        result: List[StockPrice] = []
        for s in stocks:
            match = next((item for item in data if item.get("symbol") == s), None)
            price_val = match.get("price") if match else None
            price: Optional[float]
            if price_val is None:
                price = None
            else:
                try:
                    price = float(price_val)
                except (TypeError, ValueError):
                    price = None
            result.append({"stock": s, "price": price})
        return result
    except Exception as e:
        logger.exception("Failed to fetch stock prices: %s", e)
        return [{"stock": s, "price": None} for s in stocks]


def cards_summary(df: pd.DataFrame) -> List[Dict[str, Union[str, float]]]:
    """Считает для каждой карты: последние 4 цифры, общая сумма расходов (Сумма платежа < 0), кешбэк."""
    if df.empty or "Номер карты" not in df.columns:
        return []

    df2 = df.copy()
    if "Сумма платежа" in df2.columns:
        df2["spent"] = pd.to_numeric(df2["Сумма платежа"], errors="coerce").fillna(0)
        df2["expense"] = df2["spent"].apply(lambda x: -x if x < 0 else 0)
    else:
        df2["expense"] = 0

    cards: List[Dict[str, Union[str, float]]] = []
    for card, group in df2.groupby("Номер карты"):
        last_digits = str(card)[-4:] if pd.notna(card) else ""
        total_spent = float(group["expense"].sum())
        cashback = round(total_spent / 100.0, 2)
        cards.append(
            {
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": cashback,
            }
        )
    return cards


def top_transactions(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Optional[Union[str, float]]]]:
    if df.empty or "Сумма платежа" not in df.columns:
        return []

    df2 = df.copy()
    df2["amount"] = pd.to_numeric(df2["Сумма платежа"], errors="coerce").fillna(0)
    df2["abs_amount"] = df2["amount"].abs()
    top = df2.sort_values("abs_amount", ascending=False).head(top_n)
    res: List[Dict[str, Optional[Union[str, float]]]] = []
    for _, row in top.iterrows():
        date_val = row["Дата операции"]
        date_str: Optional[str] = None
        if pd.notna(date_val) and isinstance(date_val, pd.Timestamp):
            date_str = date_val.strftime("%d.%m.%Y")
        res.append(
            {
                "date": date_str,
                "amount": float(row["amount"]),
                "category": row.get("Категория"),
                "description": row.get("Описание"),
            }
        )
    return res

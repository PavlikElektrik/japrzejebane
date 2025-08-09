import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.reports import spending_by_category
from src.services import simple_search
from src.utils import load_transactions_excel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def search_transactions(query: str, limit: int = 10) -> None:
    logger.info(f"Запускаем поиск по запросу: {query}")
    df = load_transactions_excel(Path("data/operations.xlsx"))
    # Приводим ключи словарей к str, чтобы mypy не ругался
    raw_transactions = df.to_dict(orient="records")
    transactions: List[Dict[str, Any]] = [{str(k): v for k, v in record.items()} for record in raw_transactions]

    results = simple_search(query, transactions, limit=limit)
    print(results)


def category_spending_report(category: str, date: Optional[str] = None) -> None:
    logger.info(f"Генерируем отчёт по тратам для категории: {category}")
    df = load_transactions_excel(Path("data/operations.xlsx"))

    report = spending_by_category(df, category, date)
    print(
        f"Траты по категории '{report['category']}' за период "
        f"{report['start_date']} — {report['end_date']}: {report['total_spent']}"
    )

    print(df.loc[df["Категория"] == category, "Сумма платежа"].describe())


if __name__ == "__main__":
    # Поиск
    search_transactions("Супермаркеты")

    # Отчёт по тратам (можно с датой)
    category_spending_report("Супермаркеты", "2022-12-31")

import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def save_report(file_name: Optional[str] = None) -> Callable[..., Callable[..., Any]]:
    """Декоратор для сохранения результатов отчёта в JSON."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            name = file_name or f"report_{func.__name__}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            report_dir = Path("reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            file_path = report_dir / name
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, default=str)
                logger.info("Report saved to %s", file_path)
            except Exception as e:
                logger.exception("Failed to save report: %s", e)
            return result

        return wrapper

    return decorator


@save_report()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> Dict[str, Any]:
    """Считает траты по категории за последние 3 месяца."""

    if "Дата операции" not in transactions.columns or "Сумма платежа" not in transactions.columns:
        logger.warning("Не найдены необходимые колонки")
        return {}

    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")
    df["Сумма платежа"] = pd.to_numeric(df["Сумма платежа"], errors="coerce").fillna(0)

    # Если дата не передана, берем максимальную дату из данных
    if date:
        end = datetime.strptime(date, "%Y-%m-%d")
    else:
        end = df["Дата операции"].max()
        if pd.isna(end):
            logger.warning("Нет валидных дат в данных")
            return {}

    # Начало периода — ровно 3 месяца назад от end
    start = end - pd.DateOffset(months=3)

    mask = (df["Дата операции"] > start) & (df["Дата операции"] <= end)
    df_filtered = df.loc[mask]

    total_spent = float(
        (
            -df_filtered.loc[
                (df_filtered["Категория"] == category) & (df_filtered["Сумма платежа"] < 0), "Сумма платежа"
            ]
        ).sum()
    )

    return {
        "category": category,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "total_spent": round(total_spent, 2),
    }

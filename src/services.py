import json
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def clean_for_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(i) for i in obj]

    elif isinstance(obj, pd.Timestamp):
        if pd.isna(obj):
            return None
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif obj is pd.NaT or (isinstance(obj, float) and np.isnan(obj)):
        return None
    else:
        return obj


def simple_search(query: str, transactions: List[Dict[str, Any]], limit: Optional[int] = None) -> str:
    logger.info("Simple search for: %s", query)
    q = query.lower()
    filtered = [
        t for t in transactions if q in str(t.get("Описание", "")).lower() or q in str(t.get("Категория", "")).lower()
    ]

    if limit is not None:
        filtered = filtered[:limit]

    results = []
    for t in filtered:
        new_t = t.copy()
        for k, v in new_t.items():
            # Проверяем, можно ли применять pd.isna
            if isinstance(v, pd.Timestamp):
                if pd.isna(v):
                    new_t[k] = None
                else:
                    new_t[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Проверяем, является ли v подходящим типом для pd.isna
                # mypy любит, чтобы вход был конкретного типа
                try:
                    if pd.isna(v):
                        new_t[k] = None
                except Exception:
                    # если pd.isna не сработал, просто пропускаем
                    pass
        results.append(new_t)

    return json.dumps({"query": query, "results": results}, ensure_ascii=False, indent=2)

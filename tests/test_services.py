import json

import pandas as pd

from src import services


def test_clean_for_json(sample_transactions_list):
    obj = {"date": pd.Timestamp("2023-01-01 10:00:00"), "value": float("nan")}
    cleaned = services.clean_for_json(obj)
    assert cleaned["date"] == "2023-01-01 10:00:00"
    assert cleaned["value"] is None


def test_simple_search_found(sample_transactions_list):
    result_json = services.simple_search("Колхоз", sample_transactions_list)
    result = json.loads(result_json)
    assert len(result["results"]) == 1
    assert result["results"][0]["Описание"] == "Колхоз"


def test_simple_search_not_found(sample_transactions_list):
    result_json = services.simple_search("Не найдено", sample_transactions_list)
    result = json.loads(result_json)
    assert len(result["results"]) == 0


def test_simple_search_limit(sample_transactions_list):
    result_json = services.simple_search("перевод", sample_transactions_list, limit=1)
    result = json.loads(result_json)
    assert len(result["results"]) <= 1

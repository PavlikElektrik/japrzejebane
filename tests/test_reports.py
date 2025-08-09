from src import reports


def test_spending_by_category_last_3_months(sample_transactions_df):
    result = reports.spending_by_category(sample_transactions_df, "Супермаркеты", "2022-01-01")
    assert isinstance(result, dict)
    assert "total_spent" in result

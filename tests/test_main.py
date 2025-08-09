from src import main  # или откуда ты импортируешь эти функции


def test_search_transactions(monkeypatch, sample_transactions_df, capsys):
    # Мокаем загрузку Excel
    monkeypatch.setattr("src.utils.load_transactions_excel", lambda *args, **kwargs: sample_transactions_df)
    # Мокаем simple_search, чтобы просто вернуть фиктивный результат
    monkeypatch.setattr(
        "src.services.simple_search", lambda query, transactions, limit=10: '[{"Категория": "Супермаркеты"}]'
    )

    main.search_transactions("Супермаркеты")

    captured = capsys.readouterr()
    assert "Супермаркеты" in captured.out
    assert "[" in captured.out and "]" in captured.out  # Проверяем, что выводится JSON-строка


def test_category_spending_report(monkeypatch, sample_transactions_df, capsys):
    monkeypatch.setattr("src.utils.load_transactions_excel", lambda *args, **kwargs: sample_transactions_df)

    main.category_spending_report("Супермаркеты", "2021-12-31")

    captured = capsys.readouterr()
    assert "Супермаркеты" in captured.out
    assert "2021-12-31" in captured.out
    # Проверим, что сумма расходов (положительное число) есть в выводе (просто ищем цифры)
    assert any(char.isdigit() for char in captured.out)

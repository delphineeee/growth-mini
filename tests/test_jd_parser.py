from pathlib import Path

from app.services.jd_parser import build_matrix, load_jds


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw_jds"


def test_dataset_contains_ten_jds():
    records = load_jds(DATA_DIR)
    assert len(records) == 10
    assert all(record.company for record in records)
    assert all(record.title for record in records)


def test_matrix_is_traceable():
    matrix = build_matrix(load_jds(DATA_DIR))
    assert matrix
    for row in matrix:
        assert row["jd_count"] == len(row["sources"])
        assert 0 <= row["frequency"] <= 1
        assert all(source["excerpt"] and source["source_path"] for source in row["sources"])


def test_role_filter_separates_product_job():
    product = load_jds(DATA_DIR, "product")
    assert len(product) == 1
    assert "产品经理" in product[0].title

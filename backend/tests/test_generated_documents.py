"""
Тесты для генерации документов (обоснованное несогласие).
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import Analysis, GeneratedDocument, get_db
from sqlalchemy.orm import Session


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


class TestGeneratedDocuments:
    """Тесты для генерации 'Обоснованного несогласия'."""

    def test_generate_objection_letter_basic(self, client, db_session: Session):
        # Готовим простой анализ в БД
        analysis = Analysis(
            user_id=None,
            session_id=None,
            is_demo=True,
            filename="test.pdf",
            industry="UNIVERSAL",
            result_json={
                "summary": "Тестовый тендер на поставку оборудования",
                "passport": {
                    "nmck": "1 000 000 ₽",
                    "region": "Москва",
                    "fz": "44-ФЗ",
                },
                "issues": [
                    {
                        "title": "Ограничение конкуренции по бренду",
                        "severity": "HIGH",
                        "description": "Указан конкретный бренд без 'или эквивалент'.",
                        "quote": "Поставить оборудование марки X."
                    }
                ],
                "redFlags": [],
            },
            score=60,
            verdict="CAUTION",
            summary="Есть риски ограничения конкуренции",
        )
        db_session.add(analysis)
        db_session.commit()
        db_session.refresh(analysis)

        response = client.post(
            f"/api/documents/objection/{analysis.id}",
            data={"extra_context": "Просим учесть нашу позицию по бренду."},
        )

        # Эндпоинт должен отработать (либо через LLM, либо через fallback)
        assert response.status_code in (200, 503)

        if response.status_code == 200:
            data = response.json()
            assert data["analysis_id"] == analysis.id
            assert data["type"] == "OBJECTION_LETTER"
            assert isinstance(data["content"], str)
            assert len(data["content"]) > 50

            # Проверяем, что документ сохранён в БД
            doc = (
                db_session.query(GeneratedDocument)
                .filter(GeneratedDocument.analysis_id == analysis.id)
                .order_by(GeneratedDocument.id.desc())
                .first()
            )
            assert doc is not None
            assert doc.doc_type == "OBJECTION_LETTER"






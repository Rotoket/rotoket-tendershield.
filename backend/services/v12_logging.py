import asyncio
import logging
from typing import Any

from database import SessionLocal, V12PredictionLog

logger = logging.getLogger(__name__)


def _is_garbage(fragment_text: str) -> bool:
    try:
        from services.v12_text_utils import is_garbage_text
        return is_garbage_text(fragment_text or "")
    except ImportError:
        return False


async def log_v12_prediction(
    fragment_text: str,
    v12_result: dict,
    source: str,
    analyzer_version: str = "v12",
) -> None:
    """
    Асинхронное логирование одного предсказания v12-two-stage в таблицу V12PredictionLog.

    Ошибки при логировании не должны ломать основной поток обработки запроса.
    Явно мусорные фрагменты (бинарные/XML заголовки и т.п.) не логируются.
    """
    text_trimmed = (fragment_text or "").strip()
    if _is_garbage(text_trimmed):
        logger.debug(
            "v12: пропуск логирования (garbage), sample=%s",
            (text_trimmed or "")[:100],
        )
        return
    if len(text_trimmed) > 4000:
        text_trimmed = text_trimmed[:4000]

    class_label_pred = v12_result.get("class_label") or "Healthy"
    has_risks_pred = bool(v12_result.get("has_risks"))
    raw_result: Any = v12_result

    def _write() -> None:
        db = SessionLocal()
        try:
            record = V12PredictionLog(
                analyzer_version=analyzer_version or "v12",
                source=source or "api/legal/analyze",
                fragment_text=text_trimmed,
                has_risks_pred=has_risks_pred,
                class_label_pred=str(class_label_pred),
                raw_result_json=raw_result,
            )
            db.add(record)
            db.commit()
        except Exception as e:
            logger.error("Failed to log v12 prediction: %s", e)
            db.rollback()
        finally:
            db.close()

    try:
        await asyncio.to_thread(_write)
    except Exception as e:
        logger.error("Unexpected error in async log_v12_prediction: %s", e)


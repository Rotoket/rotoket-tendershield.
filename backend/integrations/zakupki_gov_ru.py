import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

ZAKUPKI_API_BASE = "https://api.zakupki.gov.ru/api/v1"


class ZakupkiAPIError(Exception):
    """Базовое исключение для интеграции с zakupki.gov.ru."""


class ZakupkiAPI:
    """Простейший клиент для получения данных о закупке и документов с zakupki.gov.ru.

    Это MVP-реализация. Структуру полей `tender_data` и список документов
    придётся подправить под фактический JSON официального API.
    """

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        # Маскируемся под обычный браузер, но явно указываем продукт
        self.session.headers.update(
            {
                "User-Agent": "TenderShield/1.0 (+https://tendershield.pro)",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9",
            }
        )

    # ---- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ----

    @staticmethod
    def _validate_document_url(url: str) -> None:
        """Базовые проверки безопасности для URL документа."""

        if not url.startswith("https://"):
            raise ZakupkiAPIError("Допускаются только HTTPS-ссылки")
        if "zakupki.gov.ru" not in url:
            raise ZakupkiAPIError("Домен не в белом списке (ожидается zakupki.gov.ru)")

    # ---- ПУБЛИЧНЫЕ МЕТОДЫ ----

    def get_tender(self, tender_id: str) -> Optional[Dict[str, Any]]:
        """Получить JSON по закупке через официальное API.

        ВАЖНО: структура конкретного эндпойнта может отличаться от примера,
        поэтому этот метод может потребовать доработки под боевую схему.
        """

        url = f"{ZAKUPKI_API_BASE}/orders/{tender_id}"
        try:
            resp = self.session.get(url, timeout=15)
        except requests.RequestException as exc:  # сеть / таймаут и т.п.
            logger.error("Zakupki API error for %s: %s", tender_id, exc)
            raise ZakupkiAPIError("Ошибка обращения к API zakupki.gov.ru") from exc

        if resp.status_code == 404:
            logger.info("Zakupki: tender %s not found (404)", tender_id)
            return None

        if resp.status_code != 200:
            logger.error("Zakupki API non-200 status for %s: %s", tender_id, resp.status_code)
            raise ZakupkiAPIError(f"API вернул статус {resp.status_code}")

        try:
            data: Dict[str, Any] = resp.json()
        except ValueError as exc:
            logger.error("Zakupki API invalid JSON for %s: %s", tender_id, exc)
            raise ZakupkiAPIError("Некорректный JSON от zakupki.gov.ru") from exc

        return data

    def download_documents(self, tender_id: str, tender_data: Dict[str, Any]) -> List[str]:
        """Скачать документы закупки и вернуть список путей к временным файлам.

        Ожидается, что `tender_data` содержит раздел с документами и URL'ами.
        Точный путь до списка нужно будет скорректировать по реальному API.
        """

        # "documents" здесь — абстрактное поле, подлежит уточнению
        documents_meta: List[Dict[str, Any]] = tender_data.get("documents") or []
        downloaded_paths: List[str] = []

        for doc in documents_meta:
            url = str(doc.get("url") or "").strip()
            name = str(doc.get("name") or "document").strip() or "document"

            if not url:
                continue

            try:
                self._validate_document_url(url)
            except ZakupkiAPIError as exc:
                logger.warning("Zakupki document URL skipped (%s): %s", name, exc)
                continue

            try:
                path = self._download_single_document(tender_id, name, url)
                downloaded_paths.append(path)
            except ZakupkiAPIError as exc:
                logger.warning("Zakupki document download failed (%s): %s", name, exc)
                continue

        return downloaded_paths

    def _download_single_document(self, tender_id: str, name: str, url: str) -> str:
        """Скачать один документ и сохранить во временный каталог backend.

        Ограничения:
        - только HTTPS и zakupki.gov.ru (проверяется выше);
        - лимит размера контента ~50 МБ;
        - таймаут 30 сек.
        """

        try:
            resp = self.session.get(url, timeout=30, stream=True)
        except requests.RequestException as exc:
            raise ZakupkiAPIError(f"Ошибка сети при скачивании {url}") from exc

        if resp.status_code != 200:
            raise ZakupkiAPIError(f"Не удалось скачать документ, статус {resp.status_code}")

        content_length = int(resp.headers.get("content-length") or 0)
        max_size = 50_000_000  # 50 MB
        if content_length and content_length > max_size:
            raise ZakupkiAPIError("Документ слишком большой (>50 МБ)")

        # Каталог для временных файлов закупки
        base_dir = os.path.join("tmp_zakupki", tender_id)
        os.makedirs(base_dir, exist_ok=True)

        safe_name = name.replace("/", "_").replace("\\", "_")
        path = os.path.join(base_dir, safe_name)

        try:
            with open(path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except OSError as exc:
            raise ZakupkiAPIError(f"Ошибка записи файла {path}") from exc

        logger.info("Downloaded zakupki document: %s", path)
        return path

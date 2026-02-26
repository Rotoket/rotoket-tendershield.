"""
Разбор логов v12_prediction_logs по тендеру (treski-konservy-rybnye и т.п.).

В таблице v12_prediction_logs НЕТ полей tender_id / external_id / sourcefile —
только source (например "api/legal/analyze") и fragment_text.
Поиск «по этому тендеру» выполняется по содержимому fragment_text:
ключевые слова из названий файлов (трески, консервы, рыбные) или общие маркеры.

Использование (из каталога backend):

    # Записи, где в фрагменте есть трески/консервы/рыбные или ответственность/штрафы
    python scripts/ml/inspect_v12_logs_tender.py

    # Все последние записи (без фильтра по тексту)
    python scripts/ml/inspect_v12_logs_tender.py --all --limit 100

    # Свои ключевые слова для фильтра по тендеру (через запятую)
    python scripts/ml/inspect_v12_logs_tender.py --keywords "треск,консерв,рыбн,договор"
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

# Добавляем корень backend в путь
backend_root = Path(__file__).resolve().parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from database import SessionLocal, V12PredictionLog


# Ключевые слова для фрагментов раздела «Ответственность/штрафы»
RESPONSIBILITY_KEYWORDS = re.compile(
    r"ответственност|штраф|пеня|неустойк|санкци|1/300|просрочк|возмещен",
    re.IGNORECASE
)

# Ключевые слова для привязки к тендеру «treski-konservy-rybnye» (файлы типа Proekt-Kontrakta-file-treski-konservy-rybnye.docx)
TENDER_KEYWORDS_DEFAULT = [
    "треск", "консерв", "рыбн", "konservy", "rybnye", "treski", "нмцк", "договор", "поставк",
    "контракт", "kontrakta", "postavku", "konservov", "ответственност", "otvetstvennost", "штраф",
]


def trim_fragment(text: str, min_len: int = 200, max_len: int = 300) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    # Обрезаем до max_len, стараясь по границе слова
    chunk = text[: max_len + 1]
    last_space = chunk.rfind(" ")
    if last_space >= min_len:
        return chunk[:last_space].strip() + "…"
    return text[:max_len].strip() + "…"


def is_responsibility_fragment(fragment_text: str) -> bool:
    return bool(fragment_text and RESPONSIBILITY_KEYWORDS.search(fragment_text))


def run(
    keywords: Optional[List[str]] = None,
    use_all: bool = False,
    limit: Optional[int] = None,
) -> None:
    session = SessionLocal()
    try:
        query = session.query(V12PredictionLog).order_by(V12PredictionLog.created_at.desc())
        if limit is not None:
            query = query.limit(limit * 3)  # под запас для фильтра по ключевым словам
        rows = query.all()

        if use_all:
            selected = rows[: (limit or 50)]
        else:
            kws = keywords or TENDER_KEYWORDS_DEFAULT
            selected = []
            for r in rows:
                t = (r.fragment_text or "").lower()
                if any(kw.lower() in t for kw in kws):
                    selected.append(r)
                if limit and len(selected) >= limit:
                    break
            selected = selected[: limit] if limit else selected

        total_in_table = session.query(V12PredictionLog).count()
        print("=" * 80)
        print("v12_prediction_logs: разбор по тендеру (treski-konservy-rybnye / по ключевым словам)")
        print("=" * 80)
        print(f"Всего записей в таблице: {total_in_table}")
        print(f"Выбрано записей по фильтру: {len(selected)}")
        if not selected:
            print("\nНет записей. Запустите с --all --limit 100 или задайте --keywords.")
            return

        # 1) Вывод каждой записи
        print("\n" + "-" * 80)
        print("ЗАПИСИ (id, created_at, fragment_text 200–300 символов, pred, gold, feedback)")
        print("-" * 80)

        for r in selected:
            frag = trim_fragment(r.fragment_text or "", 200, 300)
            gold_cl = r.gold_class_label if r.gold_class_label is not None else "—"
            gold_hr = "—"
            if r.gold_has_risks is not None:
                gold_hr = "да" if r.gold_has_risks else "нет"
            print(f"\nid: {r.id}")
            print(f"created_at: {r.created_at}")
            print(f"fragment_text: {frag}")
            print(f"has_risks_pred: {r.has_risks_pred}, class_label_pred: {r.class_label_pred}")
            print(f"gold_class_label: {gold_cl}, gold_has_risks: {gold_hr}, feedback_status: {r.feedback_status}")

        # 2) Группировка: ответственность/штрафы vs остальное
        responsibility = [r for r in selected if is_responsibility_fragment(r.fragment_text or "")]
        other = [r for r in selected if not is_responsibility_fragment(r.fragment_text or "")]

        print("\n" + "=" * 80)
        print("ГРУППЫ ПО ТЕМАТИКЕ ФРАГМЕНТА")
        print("=" * 80)
        print(f"\nФрагменты, относящиеся к разделу «Ответственность/штрафы»: {len(responsibility)}")
        print(f"Остальные фрагменты (описание объекта, заявка, прочее): {len(other)}")

        def dist(labels: list) -> dict:
            d = defaultdict(int)
            for x in labels:
                d[x] += 1
            return dict(d)

        for group_name, group in [("Ответственность/штрафы", responsibility), ("Остальные", other)]:
            if not group:
                print(f"\n[{group_name}] записей нет.")
                continue
            class_dist = dist([r.class_label_pred for r in group])
            has_risks_true = sum(1 for r in group if r.has_risks_pred)
            has_risks_false = len(group) - has_risks_true
            print(f"\n[{group_name}]")
            print(f"  class_label_pred: A={class_dist.get('A',0)} R1={class_dist.get('R1',0)} D={class_dist.get('D',0)} Healthy={class_dist.get('Healthy',0)}")
            print(f"  has_risks_pred: True={has_risks_true}, False={has_risks_false}")

        # 3) Объяснение агрегации вердикта в TenderHubDashboard и бэкенде
        print("\n" + "=" * 80)
        print("КАК АГРЕГИРУЕТСЯ ОБЩИЙ ВЕРДИКТ (TenderHubDashboard / API)")
        print("=" * 80)
        print("""
Бэкенд (api/routes/analysis.py):
- По каждому ФАЙЛУ пакета вызывается v12 один раз на document_text[:3000] (первые 3000 символов).
- В ответ LegalGrounding приходит один class_label и verdict_hint (STOP/CAUTION/PARTICIPATE) в flags.
- verdict документа берётся из v12 flags: STOP → doc.verdict=STOP, иначе CAUTION → CAUTION, иначе PARTICIPATE.
- Итоговый summary_verdict по пакету:
  - STOP, если хотя бы один документ имеет verdict == "STOP";
  - иначе CAUTION, если хотя бы один имеет CAUTION (или CLARIFY);
  - иначе PARTICIPATE.
- На верхний уровень result прокидывается один legalGrounding: приоритет STOP > CAUTION > PARTICIPATE
  (первый документ с STOP, иначе первый с CAUTION, иначе любой с legalGrounding).

Фронт (TenderHubDashboard.tsx):
- effectiveVerdict = v12Verdict || result.verdict;
- v12Verdict = result.legalGrounding?.flags?.find(f => ['STOP','CAUTION','PARTICIPATE'].includes(f)).
- Верхняя плашка «УЧАСТВОВАТЬ / С УСЛОВИЯМИ / НЕ УЧАСТВОВАТЬ» = verdictLabel(effectiveVerdict).
""")

        # 4) Краткий вывод
        print("=" * 80)
        print("КОРОТКИЙ ВЫВОД")
        print("=" * 80)
        resp_a_or_stop = any(
            (r.class_label_pred == "A" or r.has_risks_pred)
            for r in responsibility
        )
        resp_has_stop = any(r.class_label_pred == "A" for r in responsibility)
        other_all_healthy = other and all(r.class_label_pred == "Healthy" and not r.has_risks_pred for r in other)
        if responsibility and resp_has_stop and other_all_healthy:
            print("""
По разделу «ответственность/штрафы» v12 видит класс A (стоп-факторы), но общий вердикт
получается «УЧАСТВОВАТЬ» (PARTICIPATE), потому что:
- в API анализируются только первые 3000 символов КАЖДОГО документа;
- раздел ответственности может находиться дальше в проекте контракта, и в v12 попадает
  фрагмент из начала документа (предмет договора, описание), по которому модель даёт Healthy/PARTICIPATE;
- в v12_prediction_logs одна запись = один вызов v12 (один документ/фрагмент); если по этому
  тендеру в логах есть запись с A по фрагменту «ответственность/штрафы», она могла прийти
  от другого запуска (например, ручной анализ фрагмента), а не от пакетного анализа пакета с файлом
  Proekt-Kontrakta-file-treski-konservy-rybnye.docx. Итоговый вердикт пакета строится по одному
  результату на файл (первые 3000 символов), поэтому вердикт по контракту мог быть PARTICIPATE.
""")
        elif responsibility and resp_has_stop:
            print("""
По разделу «ответственность/штрафы» v12 видит класс A (стоп). Если общий вердикт всё равно
«УЧАСТВОВАТЬ», возможные причины: в пакетном анализе по каждому файлу в v12 уходит только
начало документа (первые 3000 символов); на верхний уровень попал legalGrounding от документа
с PARTICIPATE (например, НМЦК или другой файл), а не от документа с разделом ответственности.
""")
        elif not responsibility and not other:
            print("Нет записей для вывода по группам.")
        else:
            print("""
Распределение по фрагментам см. выше. Итоговый вердикт в UI = effectiveVerdict (v12 из flags
или result.verdict). Если по ответственности v12 ставит A/STOP, но вердикт PARTICIPATE —
проверьте, что в пакетный анализ попал именно тот файл, где есть раздел ответственности,
и что этот раздел попадает в первые 3000 символов документа при отправке в v12.
""")

    finally:
        session.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Разбор v12_prediction_logs по тендеру (treski-konservy-rybnye)")
    ap.add_argument("--keywords", type=str, default=None, help="Ключевые слова через запятую для фильтра по fragment_text")
    ap.add_argument("--all", action="store_true", help="Не фильтровать по ключевым словам, взять последние записи")
    ap.add_argument("--limit", type=int, default=None, help="Максимум записей (по умолчанию без лимита при фильтре)")
    args = ap.parse_args()
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else None
    if args.all and not args.limit:
        args.limit = 50
    run(keywords=keywords, use_all=args.all, limit=args.limit)


if __name__ == "__main__":
    main()

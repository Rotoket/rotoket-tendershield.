"""
Worker для асинхронного анализа документов
Выполняет анализ в фоновом режиме и обновляет статус в БД
"""

import logging
import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from database import AnalysisJob, get_db

logger = logging.getLogger(__name__)


def update_job_progress(db: Session, job_id: str, progress: int, stage: str, status: str = "processing"):
    """Обновляет прогресс задачи анализа"""
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.progress = progress
            job.stage = stage
            job.status = status
            db.commit()
            db.refresh(job)
    except Exception as e:
        logger.error(f"Ошибка обновления прогресса задачи {job_id}: {e}")
        db.rollback()


async def process_analysis_job(job_id: str, file_paths: List[str], mode: str, industry: str, db: Session):
    """
    Обрабатывает задачу анализа в фоновом режиме
    
    Args:
        job_id: ID задачи анализа
        file_paths: Список путей к сохранённым файлам
        mode: "single" | "package"
        industry: Отрасль анализа
        db: Сессия БД
    """
    try:
        # Получаем задачу
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            logger.error(f"Задача анализа {job_id} не найдена")
            return
        
        # Обновляем статус на processing
        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.progress = 0
        job.stage = "parsing_documents"
        db.commit()
        
        logger.info(f"Начата обработка задачи анализа {job_id}, режим: {mode}, файлов: {len(file_paths)}")
        
        # Импортируем функции анализа
        from main import analyze_single_file
        
        # Этапы анализа с прогрессом
        stages = [
            ("parsing_documents", 10, "Чтение документов"),
            ("legal_checks", 30, "Проверка правового режима закупки"),
            ("financial_risks", 55, "Финансовые условия и риски"),
            ("critical_flags", 75, "Скрытые ограничения и неустранимые факторы"),
            ("verdict_building", 100, "Формирование управленческого вывода"),
        ]
        
        # Выполняем анализ в зависимости от режима
        if mode == "single":
            # Single mode - анализируем один файл
            update_job_progress(db, job_id, 5, "parsing_documents")
            
            file_path = file_paths[0] if file_paths else None
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Файл не найден: {file_path}")
            
            filename = os.path.basename(file_path)
            
            # Этап 1: Парсинг документов (10%)
            update_job_progress(db, job_id, 10, "parsing_documents")
            
            # Этап 2: Правовые проверки (30%)
            update_job_progress(db, job_id, 30, "legal_checks")
            
            # Выполняем анализ
            result = await analyze_single_file(file_path, filename, industry)
            
            # Этап 3: Финансовые риски (55%)
            update_job_progress(db, job_id, 55, "financial_risks")
            
            # Этап 4: Критические флаги (75%)
            update_job_progress(db, job_id, 75, "critical_flags")
            
            # Этап 5: Формирование вердикта (100%)
            update_job_progress(db, job_id, 100, "verdict_building")
            
        elif mode == "package":
            # Package mode - анализируем несколько файлов
            update_job_progress(db, job_id, 5, "parsing_documents")
            
            if not file_paths:
                raise ValueError("Не переданы файлы для анализа пакета")
            
            # Этап 1: Парсинг документов (10%)
            update_job_progress(db, job_id, 10, "parsing_documents")
            
            # Анализируем каждый файл
            document_results = []
            total_files = len(file_paths)
            
            for idx, file_path in enumerate(file_paths):
                if not os.path.exists(file_path):
                    logger.warning(f"Файл не найден: {file_path}, пропускаем")
                    continue
                
                filename = os.path.basename(file_path)
                
                # Прогресс внутри пакета: 10% + (idx / total_files) * 60%
                file_progress = 10 + int((idx / total_files) * 60)
                update_job_progress(db, job_id, file_progress, "parsing_documents")
                
                single_result = await analyze_single_file(file_path, filename, industry)
                document_results.append(single_result)
            
            # Этап 2: Правовые проверки (30%)
            update_job_progress(db, job_id, 30, "legal_checks")
            
            # Этап 3: Финансовые риски (55%)
            update_job_progress(db, job_id, 55, "financial_risks")
            
            # Формируем результат пакета
            from main import build_global_issues, DocumentAnalysis
            
            # Преобразуем результаты в DocumentAnalysis
            doc_analyses = []
            for fp, doc_result in zip(file_paths, document_results):
                # Гарантируем, что summary всегда строка (LLM может вернуть dict)
                raw_summary = doc_result.get("summary", "")
                if isinstance(raw_summary, dict):
                    summary_value = (
                        raw_summary.get("description")
                        or raw_summary.get("text")
                        or str(raw_summary)
                    )
                else:
                    summary_value = str(raw_summary)

                doc_analyses.append(
                    DocumentAnalysis(
                        filename=os.path.basename(fp),
                        score=doc_result.get("score", 50),
                        summary=summary_value,
                        verdict=doc_result.get("verdict", "CAUTION"),
                        passport=doc_result.get("passport", {}),
                        passportValidation=doc_result.get("passportValidation"),
                        passportEvidence=doc_result.get("passportEvidence"),
                        issues=doc_result.get("issues", []),
                        specs=doc_result.get("specs", []),
                    )
                )
            
            # Определяем общий вердикт
            scores = [doc.score for doc in doc_analyses]
            avg_score = sum(scores) / len(scores) if scores else 50
            
            # Вердикт пакета по худшему документу
            verdict_order = {"STOP": 2, "CAUTION": 1, "PARTICIPATE": 0}
            worst_doc = max(doc_analyses, key=lambda d: verdict_order.get(d.verdict, 0))
            package_verdict = worst_doc.verdict
            
            # Глобальные риски
            global_issues = build_global_issues(doc_analyses)
            
            # Этап 4: Критические флаги (75%)
            update_job_progress(db, job_id, 75, "critical_flags")
            
            # Формируем PackageAnalysis
            package_id = str(job_id)  # Используем job_id как package_id
            result = {
                "packageId": package_id,
                "verdict": package_verdict,
                "summaryScore": float(avg_score),
                "summary": f"Проанализировано {len(doc_analyses)} документов. Средний балл: {int(avg_score)}",
                "documents": [doc.dict() for doc in doc_analyses],
                "globalIssues": global_issues,
            }
            
            # Этап 5: Формирование вердикта (100%)
            update_job_progress(db, job_id, 100, "verdict_building")
            
        else:
            raise ValueError(f"Неизвестный режим анализа: {mode}")
        
        # Сохраняем результат
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.result_json = result
            job.status = "done"
            job.finished_at = datetime.utcnow()
            job.progress = 100
            job.stage = "done"
            db.commit()
        
        # Удаляем временные файлы
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")
        
        # Удаляем директорию задачи
        try:
            job_dir = os.path.dirname(file_paths[0]) if file_paths else None
            if job_dir and os.path.exists(job_dir):
                os.rmdir(job_dir)
        except Exception as e:
            logger.warning(f"Не удалось удалить директорию задачи {job_dir}: {e}")
        
        logger.info(f"✅ Задача анализа {job_id} завершена успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке задачи анализа {job_id}: {e}", exc_info=True)
        
        # Обновляем статус на error
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                job.status = "error"
                job.error_message = str(e)
                job.finished_at = datetime.utcnow()
                db.commit()
        except Exception as commit_error:
            logger.error(f"Не удалось обновить статус задачи на error: {commit_error}")


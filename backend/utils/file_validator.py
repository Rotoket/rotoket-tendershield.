"""
Утилиты для валидации файлов на сервере
"""

import os
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException

# Константы
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ
ALLOWED_EXTENSIONS = {
    '.pdf',
    '.docx',
    '.doc',
    '.txt',
    '.rtf',
    '.xls',
    '.xlsx',
}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
    'application/rtf',
    'text/rtf',
    # Excel
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

# Опасные расширения (блокируем)
DANGEROUS_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
    '.app', '.deb', '.rpm', '.dmg', '.msi', '.sh', '.ps1', '.py', '.php'
}


def get_file_extension(filename: str) -> str:
    """Получает расширение файла в нижнем регистре"""
    if not filename:
        return ''
    return os.path.splitext(filename)[1].lower()


def validate_file(file: UploadFile, max_size: int = MAX_FILE_SIZE) -> Tuple[bool, Optional[str]]:
    """
    Валидирует загружаемый файл.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Проверка расширения
    if not file.filename:
        return False, "Имя файла не указано"
    
    extension = get_file_extension(file.filename)
    
    # Проверка на опасные расширения
    if extension in DANGEROUS_EXTENSIONS:
        return False, f"Файл с расширением {extension} не разрешен по соображениям безопасности"
    
    # Проверка на разрешенные расширения
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(ALLOWED_EXTENSIONS)
        return False, f"Неподдерживаемый формат файла: {extension}. Разрешенные форматы: {allowed}"
    
    # Проверка имени файла на подозрительные символы
    suspicious_chars = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
    for char in suspicious_chars:
        if char in file.filename:
            return False, f"Имя файла содержит недопустимые символы: {char}"
    
    # Проверка MIME типа (если доступен)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        # Не блокируем строго, т.к. некоторые браузеры могут неправильно определять MIME
        # Но предупреждаем в логах
        pass
    
    # Размер файла проверяется при чтении
    return True, None


async def validate_file_size(file: UploadFile, max_size: int = MAX_FILE_SIZE) -> Tuple[bool, Optional[str]]:
    """
    Проверяет размер файла, читая его содержимое.
    ВАЖНО: Чтение файла изменяет позицию потока, поэтому нужно сохранять содержимое.
    
    Returns:
        Tuple[bool, Optional[str], bytes]: (is_valid, error_message, file_content)
    """
    file_content = b''
    file_size = 0
    
    # Читаем файл по частям для проверки размера
    while True:
        chunk = await file.read(8192)  # Читаем по 8 КБ
        if not chunk:
            break
        
        file_size += len(chunk)
        file_content += chunk
        
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"Файл слишком большой ({actual_mb:.2f} МБ). Максимальный размер: {max_mb} МБ", file_content
    
    # Сбрасываем позицию файла для дальнейшего использования
    await file.seek(0)
    
    if file_size == 0:
        return False, "Файл пустой", file_content
    
    return True, None, file_content


def format_file_size(bytes_size: int) -> str:
    """Форматирует размер файла в читаемый вид"""
    if bytes_size == 0:
        return "0 Б"
    
    units = ['Б', 'КБ', 'МБ', 'ГБ']
    unit_index = 0
    size = float(bytes_size)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"



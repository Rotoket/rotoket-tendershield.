# PowerShell скрипт для создания резервной копии проекта
# Запустите: .\backup_script.ps1

$ErrorActionPreference = "Stop"

# Настройки
$ProjectPath = "c:\Users\Dom\Desktop\tender-shield-pro"
$BackupPath = "D:\Backup\tender-shield-pro-$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"
$BackupPathEnv = "D:\Backup\tender-shield-pro-env-$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"

Write-Host "📦 Создание резервной копии проекта..." -ForegroundColor Cyan
Write-Host "Проект: $ProjectPath" -ForegroundColor Gray
Write-Host "Куда: $BackupPath" -ForegroundColor Gray
Write-Host ""

# Проверка существования проекта
if (-not (Test-Path $ProjectPath)) {
    Write-Host "❌ Ошибка: Проект не найден по пути $ProjectPath" -ForegroundColor Red
    exit 1
}

# Создание папки для бэкапа
New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
New-Item -ItemType Directory -Path $BackupPathEnv -Force | Out-Null

Write-Host "✅ Папка для бэкапа создана" -ForegroundColor Green

# Копирование проекта (исключая ненужные папки)
Write-Host "📁 Копирование файлов проекта..." -ForegroundColor Yellow

$ExcludeDirs = @(
    "node_modules",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".git\objects",
    "dist",
    "build",
    ".next"
)

$ExcludeFiles = @(
    "*.pyc",
    "*.pyo",
    "*.log",
    ".DS_Store"
)

# Копируем все, кроме исключений
Get-ChildItem -Path $ProjectPath -Recurse | Where-Object {
    $item = $_
    $relativePath = $item.FullName.Substring($ProjectPath.Length + 1)
    
    # Проверяем исключения
    $shouldExclude = $false
    foreach ($excludeDir in $ExcludeDirs) {
        if ($relativePath -like "*\$excludeDir\*" -or $relativePath -like "$excludeDir\*") {
            $shouldExclude = $true
            break
        }
    }
    
    if (-not $shouldExclude) {
        foreach ($excludeFile in $ExcludeFiles) {
            if ($item.Name -like $excludeFile) {
                $shouldExclude = $true
                break
            }
        }
    }
    
    -not $shouldExclude
} | Copy-Item -Destination {
    $newPath = $_.FullName.Replace($ProjectPath, $BackupPath)
    $newDir = Split-Path $newPath -Parent
    if (-not (Test-Path $newDir)) {
        New-Item -ItemType Directory -Path $newDir -Force | Out-Null
    }
    $newPath
} -Force

Write-Host "✅ Файлы проекта скопированы" -ForegroundColor Green

# Копирование важных конфигурационных файлов отдельно
Write-Host "🔐 Копирование конфигурационных файлов..." -ForegroundColor Yellow

$ImportantFiles = @(
    "backend\.env",
    "backend\env.example",
    "infra\docker-compose.yml",
    "infra\nginx.conf",
    ".cursorrules",
    ".gitignore"
)

foreach ($file in $ImportantFiles) {
    $sourcePath = Join-Path $ProjectPath $file
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $BackupPathEnv $file
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item $sourcePath $destPath -Force
        Write-Host "  ✅ $file" -ForegroundColor Gray
    }
    else {
        Write-Host "  ⚠️  $file не найден" -ForegroundColor Yellow
    }
}

Write-Host "✅ Конфигурационные файлы скопированы" -ForegroundColor Green

# Экспорт базы данных (если Docker запущен)
Write-Host "💾 Проверка базы данных..." -ForegroundColor Yellow

try {
    $dockerRunning = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dbContainer = docker ps --filter "name=tender_postgres" --format "{{.Names}}"
        if ($dbContainer) {
            Write-Host "  📊 Экспорт базы данных..." -ForegroundColor Gray
            $dbBackupFile = Join-Path $BackupPathEnv "backup_db.sql"
            docker exec tender_postgres pg_dump -U tender_user tender > $dbBackupFile 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ База данных экспортирована" -ForegroundColor Green
            }
            else {
                Write-Host "  ⚠️  Не удалось экспортировать БД (возможно, она пустая)" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "  ⚠️  Контейнер БД не найден" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  ⚠️  Docker не запущен, пропускаем экспорт БД" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ⚠️  Ошибка при экспорте БД: $_" -ForegroundColor Yellow
}

# Создание списка Ollama моделей
Write-Host "🤖 Проверка Ollama моделей..." -ForegroundColor Yellow

try {
    $ollamaList = ollama list 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ollamaBackupFile = Join-Path $BackupPathEnv "ollama_models.txt"
        $ollamaList | Out-File $ollamaBackupFile -Encoding UTF8
        Write-Host "  ✅ Список моделей сохранен" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠️  Ollama не установлен или не запущен" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ⚠️  Ollama не найден" -ForegroundColor Yellow
}

# Создание информации о системе
Write-Host "ℹ️  Создание информации о системе..." -ForegroundColor Yellow

$systemInfo = @"
Дата создания бэкапа: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Система: $(Get-ComputerInfo | Select-Object -ExpandProperty WindowsProductName)
Версия: $(Get-ComputerInfo | Select-Object -ExpandProperty WindowsVersion)
Пользователь: $env:USERNAME
Путь проекта: $ProjectPath
"@

$systemInfoFile = Join-Path $BackupPathEnv "system_info.txt"
$systemInfo | Out-File $systemInfoFile -Encoding UTF8

Write-Host "✅ Информация о системе сохранена" -ForegroundColor Green

# Итоговая информация
Write-Host ""
Write-Host "🎉 Резервная копия создана успешно!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Проект: $BackupPath" -ForegroundColor Cyan
Write-Host "🔐 Конфиги: $BackupPathEnv" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  ВАЖНО: Проверьте, что файл backend\.env сохранен в папке конфигов!" -ForegroundColor Yellow
Write-Host ""


# PowerShell script for project backup
# Run: .\backup_script.ps1

$ErrorActionPreference = "Continue"

# Settings
$ProjectPath = "c:\Users\Dom\Desktop\tender-shield-pro"
$BackupBasePath = "F:\Backup"
$BackupPath = "$BackupBasePath\tender-shield-pro-$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"
$BackupPathEnv = "$BackupBasePath\tender-shield-pro-env-$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"

Write-Host "Creating project backup..." -ForegroundColor Cyan
Write-Host "Project: $ProjectPath" -ForegroundColor Gray
Write-Host "Backup to: $BackupPath" -ForegroundColor Gray
Write-Host ""

# Check if project exists
if (-not (Test-Path $ProjectPath)) {
    Write-Host "ERROR: Project not found at $ProjectPath" -ForegroundColor Red
    exit 1
}

# Create backup directories
New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
New-Item -ItemType Directory -Path $BackupPathEnv -Force | Out-Null

Write-Host "Backup directories created" -ForegroundColor Green

# Copy project using robocopy (handles long paths better)
Write-Host "Copying project files (this may take a while)..." -ForegroundColor Yellow

# Exclude patterns for robocopy
$excludePatterns = @(
    "/XD", "node_modules", "venv", "__pycache__", ".pytest_cache", ".git\objects", "dist", "build", ".next",
    "/XF", "*.pyc", "*.pyo", "*.log", ".DS_Store"
)

# Use robocopy for better handling of long paths
$robocopyArgs = @($ProjectPath, $BackupPath, "/E", "/R:3", "/W:1", "/NFL", "/NDL", "/NP")
$robocopyArgs += $excludePatterns

$robocopyResult = & robocopy @robocopyArgs 2>&1
$exitCode = $LASTEXITCODE

# Robocopy returns 0-7 for success, 8+ for errors
if ($exitCode -le 7) {
    Write-Host "Project files copied successfully" -ForegroundColor Green
} else {
    Write-Host "WARNING: Some files may not have been copied (exit code: $exitCode)" -ForegroundColor Yellow
}

# Copy important configuration files separately
Write-Host "Copying configuration files..." -ForegroundColor Yellow

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
        try {
            Copy-Item $sourcePath $destPath -Force -ErrorAction Stop
            Write-Host "  OK: $file" -ForegroundColor Gray
        } catch {
            Write-Host "  WARNING: Failed to copy $file" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  WARNING: $file not found" -ForegroundColor Yellow
    }
}

Write-Host "Configuration files copied" -ForegroundColor Green

# Export database (if Docker is running)
Write-Host "Checking database..." -ForegroundColor Yellow

try {
    $dockerRunning = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dbContainer = docker ps --filter "name=tender_postgres" --format "{{.Names}}"
        if ($dbContainer) {
            Write-Host "  Exporting database..." -ForegroundColor Gray
            $dbBackupFile = Join-Path $BackupPathEnv "backup_db.sql"
            docker exec tender_postgres pg_dump -U tender_user tender > $dbBackupFile 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Database exported" -ForegroundColor Green
            }
            else {
                Write-Host "  WARNING: Failed to export DB (may be empty)" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "  WARNING: DB container not found" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  WARNING: Docker not running, skipping DB export" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  WARNING: Error exporting DB: $_" -ForegroundColor Yellow
}

# Create list of Ollama models
Write-Host "Checking Ollama models..." -ForegroundColor Yellow

try {
    $ollamaList = ollama list 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ollamaBackupFile = Join-Path $BackupPathEnv "ollama_models.txt"
        $ollamaList | Out-File $ollamaBackupFile -Encoding UTF8
        Write-Host "  Model list saved" -ForegroundColor Green
    }
    else {
        Write-Host "  WARNING: Ollama not installed or not running" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  WARNING: Ollama not found" -ForegroundColor Yellow
}

# Create system information
Write-Host "Creating system information..." -ForegroundColor Yellow

$systemInfo = @"
Backup created: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
System: $(Get-ComputerInfo | Select-Object -ExpandProperty WindowsProductName)
Version: $(Get-ComputerInfo | Select-Object -ExpandProperty WindowsVersion)
User: $env:USERNAME
Project path: $ProjectPath
"@

$systemInfoFile = Join-Path $BackupPathEnv "system_info.txt"
$systemInfo | Out-File $systemInfoFile -Encoding UTF8

Write-Host "System information saved" -ForegroundColor Green

# Final information
Write-Host ""
Write-Host "Backup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Project: $BackupPath" -ForegroundColor Cyan
Write-Host "Configs: $BackupPathEnv" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Check that backend\.env file is saved in configs folder!" -ForegroundColor Yellow
Write-Host ""

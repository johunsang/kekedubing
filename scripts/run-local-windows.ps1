$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "Python is required. Install it from https://www.python.org/downloads/ or Microsoft Store."
  exit 1
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
  } else {
    Write-Host "ffmpeg is required. Install it, then reopen PowerShell."
    exit 1
  }
}

if (-not (Test-Path ".local-ai")) {
  python -m venv .local-ai
}

& ".\.local-ai\Scripts\python.exe" -m pip install --upgrade pip
& ".\.local-ai\Scripts\python.exe" -m pip install -r backend\requirements.txt

if ((-not (Test-Path "certs\localhost.crt")) -or (-not (Test-Path "certs\localhost.key"))) {
  New-Item -ItemType Directory -Force certs | Out-Null
  openssl req -x509 -newkey rsa:2048 -nodes `
    -keyout certs\localhost.key `
    -out certs\localhost.crt `
    -days 365 `
    -subj "/CN=localhost"
}

$env:APP_ROOT = "$Root"
$env:WEB_DIR = "$Root\web"
$env:DATA_DIR = "$Root\data"
$env:MAX_UPLOAD_MB = "0"
$env:DEFAULT_SOURCE_LANG = "auto"
$env:DEFAULT_TARGET_LANG = "en"
$env:SUPERTONIC_VOICE = "M1"
$env:SUBTITLE_STYLE = "bold"
$env:SUBTITLE_POSITION = "bottom"
$env:SUBTITLE_SIZE = "100"
$env:SUBTITLE_FONT = "Noto Sans"
$env:MIN_DUB_SPEED = "0.85"
$env:MAX_DUB_SPEED = "1.75"

& ".\.local-ai\Scripts\uvicorn.exe" backend.app.main:app `
  --host 127.0.0.1 `
  --port 8801 `
  --ssl-certfile certs\localhost.crt `
  --ssl-keyfile certs\localhost.key

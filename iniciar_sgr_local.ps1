$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$pythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv (Join-Path $PSScriptRoot ".venv")
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv (Join-Path $PSScriptRoot ".venv")
    } else {
        throw "No se encontró Python. Instala Python 3.11 o posterior y vuelve a ejecutar este script."
    }
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno Python." }
}

function Invoke-SgrPython {
    param([string[]]$PythonArguments)
    & $pythonPath @PythonArguments
    if ($LASTEXITCODE -ne 0) { throw "Falló el comando Python: $PythonArguments" }
}

Invoke-SgrPython -PythonArguments @("-m", "pip", "install", "-r", "requirements.txt")
Invoke-SgrPython -PythonArguments @("manage.py", "migrate")
Invoke-SgrPython -PythonArguments @("manage.py", "load_demo_data")

$hasAdmin = & $pythonPath manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.filter(is_superuser=True).exists())"
if ($LASTEXITCODE -ne 0) { throw "No se pudo comprobar la cuenta administradora." }
if (($hasAdmin | Out-String).Trim() -notmatch "True$") {
    Write-Host "Crea la cuenta que usarás para iniciar sesión en el SGR."
    Invoke-SgrPython -PythonArguments @("manage.py", "createsuperuser")
}

Write-Host "SGR disponible en http://127.0.0.1:8000/ (Ctrl+C para detener)." -ForegroundColor Green
Invoke-SgrPython -PythonArguments @("manage.py", "runserver", "127.0.0.1:8000")

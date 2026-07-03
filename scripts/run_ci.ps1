$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Missing .venv. Create it with: py -3.13 -m venv .venv"
}

Push-Location (Join-Path $Root "cloudorder-ops-api")
try {
    & $Python -m pytest tests -q
    if ($LASTEXITCODE -ne 0) { throw "Unit tests failed" }
}
finally {
    Pop-Location
}

& $Python -m py_compile (Join-Path $Root "enterprise-rag-dataset\evaluation\runner\run_eval.py")
if ($LASTEXITCODE -ne 0) { throw "run_eval.py compile failed" }
& $Python -m py_compile (Join-Path $Root "enterprise-rag-dataset\evaluation\runner\run_retrieval_eval.py")
if ($LASTEXITCODE -ne 0) { throw "run_retrieval_eval.py compile failed" }
& $Python -m py_compile (Join-Path $Root "enterprise-rag-dataset\evaluation\runner\run_load_test.py")
if ($LASTEXITCODE -ne 0) { throw "run_load_test.py compile failed" }
& $Python (Join-Path $Root "scripts\validate_project.py")
if ($LASTEXITCODE -ne 0) { throw "Project validation failed" }

Write-Host "Local CI checks passed." -ForegroundColor Green

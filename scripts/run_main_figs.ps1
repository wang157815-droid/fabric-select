param(
  [string]$Results = "outputs/results_main.csv",
  [string]$OutDir = "outputs/figs_main"
)

$ErrorActionPreference = "Stop"

& .\.venv\Scripts\python -m src.summarize --results $Results --out-dir $OutDir

if ($LASTEXITCODE -ne 0) {
  throw "summarize failed: exit=$LASTEXITCODE"
}

Write-Host "Wrote figs -> $OutDir"



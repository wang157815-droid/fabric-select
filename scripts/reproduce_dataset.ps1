param(
  [int]$Seed = 42,
  [int]$NOutdoor = 650,
  [int]$NWinter = 650,
  [int]$CleanPerScenario = 500
)

$ErrorActionPreference = "Stop"

Write-Host "Reproducing FabricSelectBench dataset..."
Write-Host "  seed=$Seed"
Write-Host "  n_outdoor=$NOutdoor"
Write-Host "  n_winter=$NWinter"
Write-Host "  clean_per_scenario=$CleanPerScenario"

& .\.venv\Scripts\python -m src.dataset_v1 `
  --seed $Seed `
  --n-outdoor $NOutdoor `
  --n-winter $NWinter `
  --clean-per-scenario $CleanPerScenario

if ($LASTEXITCODE -ne 0) {
  throw "dataset_v1 failed: exit=$LASTEXITCODE"
}

Write-Host ""
Write-Host "Dataset reproduction complete. Expected outputs include:"
Write-Host "  data\questions_v1.jsonl"
Write-Host "  data\questions_v1_meta.json"
Write-Host "  data\questions_v1_clean.jsonl"
Write-Host "  outputs\dataset_report.md"

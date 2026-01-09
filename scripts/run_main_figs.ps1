param(
  [string]$Results = "outputs/results_main.csv",
  [string]$LogJsonl = "outputs/per_question_log_main.jsonl",
  [string]$OutDir = "outputs/figs_main",
  [string]$QuestionsJsonl = "data/questions_v1_clean.jsonl"
)

$ErrorActionPreference = "Stop"

if (Test-Path $LogJsonl) {
  if (Test-Path $QuestionsJsonl) {
    & .\.venv\Scripts\python -m src.summarize --results $Results --out-dir $OutDir --log-jsonl $LogJsonl --questions-jsonl $QuestionsJsonl --paper
  } else {
    & .\.venv\Scripts\python -m src.summarize --results $Results --out-dir $OutDir --log-jsonl $LogJsonl --paper
  }
} else {
  if (Test-Path $QuestionsJsonl) {
    & .\.venv\Scripts\python -m src.summarize --results $Results --out-dir $OutDir --questions-jsonl $QuestionsJsonl --paper
  } else {
    & .\.venv\Scripts\python -m src.summarize --results $Results --out-dir $OutDir --paper
  }
}

if ($LASTEXITCODE -ne 0) {
  throw "summarize failed: exit=$LASTEXITCODE"
}

Write-Host "Wrote figs -> $OutDir"





param(
  [int]$ExpectedRuns = 6,
  [string]$Results = "outputs/results_gpt5_sanity.csv",
  [string]$LogJsonl = "outputs/per_question_log_gpt5_sanity.jsonl",
  [string]$QuestionsJsonl = "data/questions_v1_clean.jsonl",
  [string]$OutDir = "outputs/figs_main_gpt5_sanity",
  [int]$PollSeconds = 60
)

$ErrorActionPreference = "Stop"

function Get-ResultRowCount([string]$Path) {
  if (!(Test-Path $Path)) { return 0 }
  $n = (Get-Content $Path | Measure-Object -Line).Lines
  if ($n -le 1) { return 0 } # header only
  return ($n - 1)
}

Write-Host "[postprocess] waiting for GPT-5 sanity results..."
Write-Host "  results=$Results"
Write-Host "  expected_runs=$ExpectedRuns poll_seconds=$PollSeconds"

while ($true) {
  $rows = Get-ResultRowCount $Results
  if ($rows -ge $ExpectedRuns) {
    break
  }
  Write-Host "[postprocess] current_runs=$rows / $ExpectedRuns (sleep ${PollSeconds}s)..."
  Start-Sleep -Seconds $PollSeconds
}

Write-Host "[postprocess] detected completion: current_runs=$(Get-ResultRowCount $Results)"
Write-Host "[postprocess] running summarize -> $OutDir"

& .\.venv\Scripts\python -m src.summarize --results $Results --out-dir $OutDir --log-jsonl $LogJsonl --questions-jsonl $QuestionsJsonl --paper
if ($LASTEXITCODE -ne 0) { throw "summarize failed: exit=$LASTEXITCODE" }

Write-Host "[postprocess] updating PAPER_TABLES.md / PAPER_FIGURES.md"
& .\.venv\Scripts\python scripts/compile_paper_tables.py --main-dir outputs/figs_main --ablation-dir outputs/figs_ablation --out-md PAPER_TABLES.md
if ($LASTEXITCODE -ne 0) { throw "compile_paper_tables failed: exit=$LASTEXITCODE" }
& .\.venv\Scripts\python scripts/compile_paper_figures.py --outputs-dir outputs --out-md PAPER_FIGURES.md
if ($LASTEXITCODE -ne 0) { throw "compile_paper_figures failed: exit=$LASTEXITCODE" }

Write-Host "[postprocess] git commit/push (paper docs only)"
git add PAPER_TABLES.md PAPER_FIGURES.md scripts/compile_paper_tables.py
git commit -m "docs: add gpt-5 sanity check appendix tables/figures"
git push

Write-Host "[postprocess] done."


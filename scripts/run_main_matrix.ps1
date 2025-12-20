param(
  [int]$Repeats = 3,
  [int]$NQuestions = 500,
  [int]$Seed = 1000,
  [string]$QuestionsPath = "data/questions_v1_clean.jsonl",
  [string]$OutDir = "outputs",
  [string]$ResultsName = "results_main.csv",
  [string]$LogName = "per_question_log_main.jsonl",
  [int]$ProgressEvery = 25,
  [string[]]$Scenarios = @("outdoor_dwr_windbreaker", "winter_warm_midlayer"),
  [string[]]$Strategies = @(
    "zero_shot",
    "few_shot",
    "cot_few_shot",
    "self_reflection",
    "fashionprompt",
    "voting",
    "weighted_voting",
    "borda",
    "garmentagents_fixed",
    "garmentagents_adaptive"
  )
)

$ErrorActionPreference = "Stop"

Write-Host "Running main matrix..."
Write-Host "  questions_path=$QuestionsPath"
Write-Host "  repeats=$Repeats n_questions=$NQuestions seed=$Seed"
Write-Host "  out_dir=$OutDir results=$ResultsName log=$LogName"
Write-Host "  scenarios=$($Scenarios -join ',')"
Write-Host "  strategies=$($Strategies -join ',')"

foreach ($scenario in $Scenarios) {
  foreach ($strategy in $Strategies) {
    Write-Host ""
    Write-Host "=== scenario=$scenario strategy=$strategy ==="

    & .\.venv\Scripts\python -m src.eval_run `
      --strategy $strategy `
      --scenario $scenario `
      --temperature 1.0 `
      --repeats $Repeats `
      --n-questions $NQuestions `
      --seed $Seed `
      --max-tokens 512 `
      --retry-on-none `
      --retry-max-tokens 1024 `
      --progress `
      --progress-every $ProgressEvery `
      --questions-path $QuestionsPath `
      --out-dir $OutDir `
      --results-name $ResultsName `
      --log-name $LogName `
      --skip-existing `
      --no-log-messages

    if ($LASTEXITCODE -ne 0) {
      throw "eval_run failed: scenario=$scenario strategy=$strategy exit=$LASTEXITCODE"
    }
  }
}

Write-Host ""
Write-Host "Done. Results written to:"
Write-Host "  $OutDir\$ResultsName"
Write-Host "  $OutDir\$LogName"



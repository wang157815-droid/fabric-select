param(
  [int]$NQuestionsPerScenario = 100,
  [int]$Seed = 2000,
  [int]$Repeats = 1,
  [int]$MaxTokens = 1536,
  [int]$RetryMaxTokens = 2048,
  [string]$QuestionsPath = "data/questions_v1_clean.jsonl",
  [string]$OutDir = "outputs",
  [string]$ResultsName = "results_gpt5_sanity.csv",
  [string]$LogName = "per_question_log_gpt5_sanity.jsonl",
  [int]$ProgressEvery = 25,
  [string[]]$Scenarios = @("outdoor_dwr_windbreaker", "winter_warm_midlayer"),
  [string[]]$Strategies = @("few_shot", "cot_few_shot", "garmentagents_adaptive")
)

$ErrorActionPreference = "Stop"

# 复核用更强模型
$env:MODEL = "gpt-5"

Write-Host "Running GPT-5 sanity check..."
Write-Host "  model=$env:MODEL"
Write-Host "  questions_path=$QuestionsPath"
Write-Host "  repeats=$Repeats n_questions_per_scenario=$NQuestionsPerScenario seed=$Seed"
Write-Host "  max_tokens=$MaxTokens retry_max_tokens=$RetryMaxTokens"
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
      --n-questions $NQuestionsPerScenario `
      --seed $Seed `
      --max-tokens $MaxTokens `
      --retry-on-none `
      --retry-max-tokens $RetryMaxTokens `
      --progress `
      --progress-every $ProgressEvery `
      --questions-path $QuestionsPath `
      --out-dir $OutDir `
      --results-name $ResultsName `
      --log-name $LogName `
      --skip-existing `
      --no-log-messages `
      --resume `
      --no-abort-on-llm-error

    if ($LASTEXITCODE -ne 0) {
      Write-Host "[WARN] eval_run returned exit=$LASTEXITCODE for scenario=$scenario strategy=$strategy, continuing..."
    }
  }
}

Write-Host ""
Write-Host "Done. Results written to:"
Write-Host "  $OutDir\$ResultsName"
Write-Host "  $OutDir\$LogName"


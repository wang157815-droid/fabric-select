# FabricSelectBench

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19106553.svg)](https://doi.org/10.5281/zenodo.19106553)

FabricSelectBench is a benchmark for constraint-aware fabric selection in apparel engineering. This repository accompanies the manuscript *Benchmarking Large Language Model Decision Strategies for Constraint-Aware Fabric Selection in Apparel Engineering* and contains the dataset construction code, strategy implementations, evaluation scripts, result summaries, and external-validation utilities used in the paper.

## Archive And Project Links

- Archival DOI: [10.5281/zenodo.19106553](https://doi.org/10.5281/zenodo.19106553)
- Development repository: [github.com/wang157815-droid/fabric-select](https://github.com/wang157815-droid/fabric-select)

## Project Overview

The benchmark compares three families of decision strategies on four-way fabric selection questions with explicit hard constraints (`must`) and soft preferences (`prefer`):

- Non-LLM baselines: `nonllm_feasible_random`, `nonllm_simple_heuristic`, `nonllm_topsis`, `nonllm_vikor`
- Single-agent prompting: `zero_shot`, `few_shot`, `cot_few_shot`, `self_reflection`, `fashionprompt`
- Multi-agent orchestration: `voting`, `weighted_voting`, `borda`, `garmentagents_fixed`, `garmentagents_adaptive`

The main reported metrics are accuracy (oracle agreement), token usage, API calls, latency, valid-output rate, and hard-constraint violation behavior.

## Dataset Information

### Main benchmark

- Primary cleaned dataset: `data/questions_v1_clean.jsonl`
- Metadata summary: `data/questions_v1_meta.json`
- Default size: 1000 cleaned questions
- Scenarios:
  - `outdoor_dwr_windbreaker` (500 questions)
  - `winter_warm_midlayer` (500 questions)

Each question contains:

- A natural-language task description
- A set of hard constraints (`must`)
- A textual preference list (`prefer`)
- Four candidate options (`A/B/C/D`) with structured attributes
- A gold answer derived from the deterministic rule-based oracle
- Oracle scores, ambiguity margin, and option tags in metadata

### External validation subsets

Real-catalog sanity-check assets are stored under `data/real_validation/`. Generated external question sets and companion metadata files are stored as:

- `data/questions_external_*.jsonl`
- `data/questions_external_*.meta.json`

These subsets are intended as reduced-schema external sanity checks rather than full replacements for the semi-synthetic benchmark.

### Third-party source provenance for external validation

The released external-validation subsets are derived from the following third-party public sources:

- Outdoor datasheet subset:
  - Source family: Ripstop by the Roll public fabric datasheets and product specification pages
  - URL: [https://ripstopbytheroll.com/pages/data-sheets](https://ripstopbytheroll.com/pages/data-sheets)
  - Use in this project: raw PDF datasheets were parsed into `data/real_validation/outdoor_catalog.csv`, then converted into external multiple-choice questions
- Winter knitting subset:
  - Source: *knitting-dataset* (Mendeley Data)
  - DOI: [10.17632/vs2vjzkw5h.1](https://doi.org/10.17632/vs2vjzkw5h.1)
  - Use in this project: selected columns such as `GSM`, `tightness_factor`, `composition`, and `construction` were mapped into proxy winter attributes in `data/real_validation/winter_catalog.csv`
- Winter MIT subset:
  - Source: MIT Fabric Properties Dataset from Bouman et al.
  - Dataset page: [https://people.csail.mit.edu/klbouman/pw/projects/materialproperties/dataset.html](https://people.csail.mit.edu/klbouman/pw/projects/materialproperties/dataset.html)
  - Ground-truth measurements download: [https://people.csail.mit.edu/klbouman/pw/data/materialproperties/material_properties.zip](https://people.csail.mit.edu/klbouman/pw/data/materialproperties/material_properties.zip)
  - Use in this project: measured thickness and area-weight fields were exported and mapped into a winter-style catalog in `data/real_validation/winter_catalog_mit.csv`

Accessed: 2026-03-19.

## Code Information

Key files and directories:

- `src/dataset_v1.py`: main FabricSelectBench v1 generator used for the cleaned benchmark
- `src/scoring.py`: hard-constraint checking, preference scoring, oracle label selection, tie-breaking
- `src/strategies_non_llm.py`: random, heuristic, TOPSIS, and VIKOR baselines
- `src/strategies_single.py`: single-agent prompting strategies
- `src/strategies_multi.py`: voting, role-based orchestration, and adaptive early stopping
- `src/prompts.py`: shared prompt formatting and few-shot exemplars
- `src/eval_run.py`: end-to-end evaluation runner with logging and cost accounting
- `src/summarize.py`: figure/table generation and paper-oriented result summaries
- `src/external_validation.py`: build question sets from small real catalogs
- `scripts/reproduce_dataset.ps1`: one-command wrapper to regenerate the simulated FabricSelectBench dataset
- `scripts/run_main_matrix.ps1`: reproduce the main experiment matrix
- `scripts/run_main_figs.ps1`: regenerate paper figures/tables from the main results
- `tests/test_scoring.py`: unit test for oracle scoring and constraint logic

Legacy generators such as `src/catalog_gen.py` and `src/question_gen.py` are retained for earlier experiments and backward compatibility, but `src/dataset_v1.py` is the canonical entry point for the current paper.

## Requirements

Recommended environment:

- Python 3.10 or newer
- PowerShell for the provided Windows scripts
- OpenAI API access for LLM-based strategies

This archive was validated in a local environment using:

- Python `3.13.1`
- Windows 11 (`10.0.26220`)

Package dependencies are listed in `requirements.txt`:

- `openai>=1.0.0`
- `pydantic>=2.0.0`
- `python-dotenv>=1.0.0`
- `typer>=0.9.0`
- `pandas>=2.0.0`
- `matplotlib>=3.7.0`
- `scipy>=1.10.0`
- `statsmodels>=0.14.0`
- `PyMuPDF>=1.23.0`

## Installation

```powershell
cd D:\fabric-select-bench
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root if you plan to run LLM-based experiments:

```dotenv
OPENAI_API_KEY=your_api_key_here
MODEL=gpt-5-mini
REASONING_EFFORT=low
```

Notes:

- `OPENAI_API_KEY` is required for LLM-based strategies.
- `MODEL` defaults to `gpt-5-mini` if omitted.
- Data generation, non-LLM baselines, and many analysis scripts do not require API access.

## Usage Instructions

### 1. Reproduce the simulated dataset

The main benchmark used in the paper can be regenerated either directly with `src/dataset_v1.py` or via the wrapper script `scripts/reproduce_dataset.ps1`.

Recommended one-command reproduction:

```powershell
cd D:\fabric-select-bench
.\scripts\reproduce_dataset.ps1
```

Equivalent direct command:

```powershell
cd D:\fabric-select-bench
.\.venv\Scripts\python -m src.dataset_v1 --seed 42 --n-outdoor 650 --n-winter 650 --clean-per-scenario 500
```

Expected outputs include:

- `data/questions_v1.jsonl`
- `data/questions_v1_meta.json`
- `data/questions_v1_clean.jsonl`
- `outputs/dataset_report.md`

### 2. Run a single evaluation command

Example: run `few_shot` on the cleaned outdoor questions.

```powershell
cd D:\fabric-select-bench
.\.venv\Scripts\python -m src.eval_run `
  --strategy few_shot `
  --scenario outdoor_dwr_windbreaker `
  --temperature 1.0 `
  --repeats 1 `
  --n-questions 50 `
  --seed 123 `
  --questions-path data/questions_v1_clean.jsonl `
  --results-name results_example.csv `
  --log-name per_question_log_example.jsonl
```

### 3. Reproduce the main experiment matrix

The manuscript-level main run is scripted in `scripts/run_main_matrix.ps1`:

```powershell
cd D:\fabric-select-bench
.\scripts\run_main_matrix.ps1
```

By default this script runs:

- 14 strategies
- 2 scenarios
- 3 repeats
- 500 questions per scenario
- Output files:
  - `outputs/results_main.csv`
  - `outputs/per_question_log_main.jsonl`

### 4. Regenerate figures and paper summaries

```powershell
cd D:\fabric-select-bench
.\scripts\run_main_figs.ps1
.\.venv\Scripts\python scripts\compile_paper_tables.py --out-md ../mypaper/PAPER_TABLES.md
.\.venv\Scripts\python scripts\compile_paper_figures.py --out-md ../mypaper/PAPER_FIGURES.md
```

Common outputs:

- `outputs/figs_main/summary_by_strategy.csv`
- `outputs/figs_main/stats_tests.csv`
- `outputs/figs_main/*.png`

## Methodology Summary

### Semi-synthetic benchmark generation

The main FabricSelectBench pipeline follows these steps:

1. Generate or load scenario-specific candidate catalogs with structured attributes.
2. Sample 2-4 hard constraints from curated templates.
3. Pair them with fixed scenario-level soft-preference lists.
4. Build four-way multiple-choice questions with one oracle-best candidate, one hard-constraint-violating distractor, and feasible but suboptimal distractors.
5. Compute oracle scores and ambiguity margins.
6. Clean the benchmark by removing highly ambiguous items and retaining the highest-margin questions per scenario.

### External validation preprocessing

The external-validation pipeline adds real-data preprocessing:

1. Read small CSV catalogs derived from public datasheets or spreadsheets.
2. Normalize units and map fields into the shared benchmark schema.
3. Optionally derive ordinal `1..5` fields from raw measurements (`*_raw` columns).
4. Drop sparse rules using coverage thresholds.
5. Generate new four-way questions with a controlled minimum oracle margin.
6. Export companion metadata describing effective rules and dropped fields.

## External Validation Usage

For a detailed description of the real-catalog sanity-check workflow, see `data/real_validation/README.md`.

Example command:

```powershell
cd D:\fabric-select-bench
.\.venv\Scripts\python -m src.external_validation build `
  --scenario outdoor_dwr_windbreaker `
  --catalog-csv data/real_validation/outdoor_catalog.csv `
  --rules-path configs/rules_outdoor.json `
  --out-questions data/questions_external_outdoor.jsonl `
  --out-meta data/questions_external_outdoor.meta.json `
  --n-questions 200 `
  --seed 42 `
  --min-margin 0.02 `
  --min-coverage 0.3
```

## Tests

Run the bundled unit tests with:

```powershell
cd D:\fabric-select-bench
.\.venv\Scripts\python -m unittest discover -s tests -v
```

## Citation

If you use this archive, please cite both the dataset/code archive and the manuscript:

- Sai Wang and Tao Wu. *FabricSelectBench* archive. Zenodo. DOI: [10.5281/zenodo.19106553](https://doi.org/10.5281/zenodo.19106553)
- Sai Wang and Tao Wu. *Benchmarking Large Language Model Decision Strategies for Constraint-Aware Fabric Selection in Apparel Engineering*. Manuscript under review.

## License And Contribution Guidelines

### License

No separate license file is bundled in the current submission snapshot. Please refer to the Zenodo/GitHub release metadata for the applicable release terms, or contact the corresponding author before redistribution or reuse.

### Contributions

Bug reports, reproducibility questions, and documentation fixes are welcome. During peer review, the archive is primarily maintained for reproducibility; large feature changes are not being accepted. After publication, pull requests that improve documentation, tests, and reproducibility scripts are encouraged.

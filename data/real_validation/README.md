# External Validation (Small Real-Catalog Sanity Check)

This directory documents the external-validation workflow used in the manuscript. The goal is not to replace the semi-synthetic main benchmark, but to add an **external sanity check** built from a small number of real fabrics (public datasheets, supplier samples, or internal swatches) and to test whether the qualitative LLM trends remain consistent under noisier inputs.

## Third-Party Source Summary

The released examples in this directory were derived from three third-party public source families:

- Ripstop by the Roll public datasheets:
  - [https://ripstopbytheroll.com/pages/data-sheets](https://ripstopbytheroll.com/pages/data-sheets)
- *knitting-dataset* on Mendeley Data:
  - [https://doi.org/10.17632/vs2vjzkw5h.1](https://doi.org/10.17632/vs2vjzkw5h.1)
- MIT Fabric Properties Dataset (Bouman et al., ICCV 2013):
  - Dataset page: [https://people.csail.mit.edu/klbouman/pw/projects/materialproperties/dataset.html](https://people.csail.mit.edu/klbouman/pw/projects/materialproperties/dataset.html)
  - Measurements ZIP: [https://people.csail.mit.edu/klbouman/pw/data/materialproperties/material_properties.zip](https://people.csail.mit.edu/klbouman/pw/data/materialproperties/material_properties.zip)

Accessed: 2026-03-19.

## What To Prepare

Prepare one CSV catalog per scenario:

- `outdoor_catalog.csv`: outdoor DWR windbreaker scenario, typically 20-50 fabrics
- `winter_catalog.csv`: winter midlayer scenario, typically 20-50 fabrics

You do not need to populate every field. The script automatically removes rules whose fields have insufficient coverage in the provided catalog.

## Recommended CSV Fields

### Common fields

- `id`: required unique identifier
- `source_url`: optional datasheet or webpage URL
- `source_name`: optional supplier, brand, or source name

### Recommended outdoor fields

- `weight_gsm`: fabric weight in gsm
- `water_repellency`: ordinal score `1..5` (higher is better)
- `breathability`: ordinal score `1..5` (higher is better)
- `abrasion`: ordinal score `1..5` (higher is better)
- `handfeel_noise`: ordinal score `1..5` (higher is better, optional)
- `compliance.pfas_free`: `true` / `false` (optional)

### Recommended winter fields

- `loft_or_clo`: continuous insulation value (higher is warmer)
- `wind_blocking`: ordinal score `1..5` (higher is better, optional)
- `moisture_management`: ordinal score `1..5` (higher is better)
- `bulk_weight`: ordinal score `1..5` (lower is lighter/thinner)
- `care.machine_wash`: `true` / `false` (optional)

## Optional Raw-Measurement Columns

If you only have raw measurement columns (for example air permeability or Martindale cycles), the builder can derive ordinal `1..5` fields from `*_raw` columns using quantile-based binning within the provided catalog:

- `water_repellency_raw` -> `water_repellency` (`high`)
- `breathability_raw` -> `breathability` (`high`)
- `abrasion_raw` -> `abrasion` (`high`)
- `moisture_management_raw` -> `moisture_management` (`high`)
- `bulk_weight_raw` -> `bulk_weight` (`low`)

## Build External Question Sets

### Outdoor example

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

### Winter example

```powershell
cd D:\fabric-select-bench
.\.venv\Scripts\python -m src.external_validation build `
  --scenario winter_warm_midlayer `
  --catalog-csv data/real_validation/winter_catalog.csv `
  --rules-path configs/rules_winter.json `
  --out-questions data/questions_external_winter.jsonl `
  --out-meta data/questions_external_winter.meta.json `
  --n-questions 200 `
  --seed 42 `
  --min-margin 0.02 `
  --min-coverage 0.7
```

The builder writes:

- the question set (`*.jsonl`)
- a companion metadata report (`*.meta.json`)
- the effective rules after coverage filtering
- information about dropped fields and derived ordinal variables

## Run Evaluation

Example: evaluate `few_shot` on the outdoor external subset.

```powershell
cd D:\fabric-select-bench
.\.venv\Scripts\python -m src.eval_run `
  --strategy few_shot `
  --scenario outdoor_dwr_windbreaker `
  --questions-path data/questions_external_outdoor.jsonl `
  --repeats 2 `
  --n-questions 200 `
  --results-name results_external.csv `
  --log-name per_question_log_external.jsonl
```

For multi-agent strategies, replace `--strategy` with `voting`, `weighted_voting`, `borda`, `garmentagents_fixed`, or `garmentagents_adaptive`.

## Interpretation

These real-catalog subsets use partial schemas, proxy-derived fields, and coverage-based rule filtering. They should therefore be interpreted as **LLM-side external sanity checks**, not as full external re-rankings of the structured non-LLM baselines.


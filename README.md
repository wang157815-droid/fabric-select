# fabric-select-bench

一个**可复现**的 “面料选择决策（Fabric Selection Decision）MCQ benchmark”，用于比较：

- 单智能体提示工程策略（Zero-shot / Few-shot / CoT+Few-shot / Self-reflection / 结构化决策模板）
- 多智能体协作策略（Voting / Weighted voting / Borda）
- 提出方法：GarmentAgents-Fabric（产业链多角色 + 场景自适应协作 + 成本预算早停）

输出关注三类指标：**Accuracy + 成本（calls/tokens）+ 时间（latency）**，并支持按场景拆分与统计检验。

## 1) 安装

建议 Python 3.10+。

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

复制环境变量示例并填写：

```bash
copy .env.example .env
```

## 2) 生成数据（catalog + questions）

生成两份候选面料库（outdoor/winter）：

```bash
python -m src.catalog_gen --seed 42 --n-outdoor 120 --n-winter 120
```

从 catalog 生成 MCQ 题库（自动用规则评分器产生标准答案与关键依据点）：

```bash
python -m src.question_gen --seed 42 --n-outdoor 200 --n-winter 200
```

输出文件：

- `data/catalog_outdoor.jsonl`
- `data/catalog_winter.jsonl`
- `data/questions.jsonl`

## 3) 跑实验（调用 OpenAI API）

确保 `.env` 中有：

- `OPENAI_API_KEY`
- `MODEL`（例如 `gpt-5-mini` 用于低成本，或 `gpt-5` 用于高质量对照）

> 注意：若 `MODEL` 以 `gpt-5` 开头（含 `gpt-5-mini`），在当前 API 行为下通常不支持自定义 `temperature`；
> `eval_run` 会自动强制 `temperature=1.0` 并打印提示，避免“参数不生效/报错”导致的混淆。

示例：跑一个单智能体 Zero-shot（户外场景、温度 1.0、重复 2 次、抽 50 题）：

```bash
python -m src.eval_run --strategy zero_shot --scenario outdoor_dwr_windbreaker --temperature 1.0 --repeats 2 --n-questions 50 --seed 123
```

示例：跑 GarmentAgents（自适应 + early-stop）：

```bash
python -m src.eval_run --strategy garmentagents_adaptive --scenario winter_warm_midlayer --temperature 1.0 --repeats 2 --n-questions 50 --seed 123
```

### 3.1) 成本控制：`max_tokens` 与“抽取失败才重试”

- **`--max-tokens`（默认 512）**：单次调用允许的“最大输出 token 上限”。通常模型不会把上限吃满；真实消耗取决于实际输出长度与模型行为。
- **`--retry-on-none`（默认开启）**：当无法从输出中抽取 `A/B/C/D`（即 `pred=None`）时，自动用更高的 token 上限 **重试一次**（只对单智能体策略触发）。
- **`--retry-max-tokens`（默认 1024）**：重试时使用的 token 上限。它是“兜底上限”，**不代表每次都要用 1024**；预算敏感时可以调低（但需大于 `--max-tokens`），或用 `--no-retry-on-none` 关闭重试。

示例：主要用 512，只有抽取失败才升到 1024 重试，并显示进度/ETA：

```bash
python -m src.eval_run --strategy cot_few_shot --scenario outdoor_dwr_windbreaker --temperature 1.0 --repeats 1 --n-questions 20 --seed 300 --max-tokens 512 --retry-on-none --retry-max-tokens 1024 --progress --progress-every 5
```

### 3.2) 运行进度与 ETA

- **`--progress/--no-progress`**：是否输出逐题进度与 ETA（默认开启）
- **`--progress-every N`**：每隔 N 题输出一次（例如 `5` 表示每 5 题打一次点）

策略名一览：

- 单智能体：`zero_shot` / `few_shot` / `cot_few_shot` / `self_reflection` / `fashionprompt`
- 多智能体：`voting` / `weighted_voting` / `borda` / `garmentagents_fixed` / `garmentagents_adaptive`

输出文件（默认写到 `outputs/`）：

- `outputs/results.csv`：每次运行（策略×场景×温度×重复）的汇总指标
- `outputs/per_question_log.jsonl`：逐题原始输出、抽取结果、token/time/calls 等

## 4) 统计与绘图（可选）

```bash
python -m src.summarize --results outputs/results.csv --out-dir outputs/figs
```

说明：`summarize` 默认会按 **(scenario, temperature, n_questions, model)** 分桶汇总/出图，避免把不同实验设置混在一张图里；图文件名也会包含这些标签（例如 `acc_bar_outdoor_dwr_windbreaker__t1__n20__gpt-5-mini.png`）。

你也可以按需过滤：

```bash
python -m src.summarize --results outputs/results.csv --out-dir outputs/figs --scenario outdoor_dwr_windbreaker --temperature 1.0 --n-questions 20 --model gpt-5-mini
```

## 5) 单元测试

```bash
python -m unittest discover -s tests -v
```



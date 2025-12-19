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

示例：跑一个单智能体 Zero-shot（户外场景、温度 0.6、重复 2 次、抽 50 题）：

```bash
python -m src.eval_run --strategy zero_shot --scenario outdoor_dwr_windbreaker --temperature 0.6 --repeats 2 --n-questions 50 --seed 123
```

示例：跑 GarmentAgents（自适应 + early-stop）：

```bash
python -m src.eval_run --strategy garmentagents_adaptive --scenario winter_warm_midlayer --temperature 0.6 --repeats 2 --n-questions 50 --seed 123
```

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

## 5) 单元测试

```bash
python -m unittest discover -s tests -v
```



# fabric-select-bench

`fabric-select-bench` 是一个面向面料选择任务的多选题 benchmark。仓库里包含数据生成、题目生成、策略评测，以及结果汇总和绘图脚本。

目前主要比较三类方法：

- 单智能体提示策略：`zero_shot`、`few_shot`、`cot_few_shot`、`self_reflection`、`fashionprompt`
- 多智能体协作策略：`voting`、`weighted_voting`、`borda`
- `GarmentAgents-Fabric`：带角色分工和自适应早停的多智能体方案

默认关注三个指标：准确率、调用成本（`calls` / `tokens`）和延迟（`latency`）。

## 安装

建议使用 Python 3.10+。

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

然后复制环境变量示例文件并填写自己的配置：

```bash
copy .env.example .env
```

## 生成数据

先生成两份候选面料库，对应户外和冬季两个场景：

```bash
python -m src.catalog_gen --seed 42 --n-outdoor 120 --n-winter 120
```

再根据 catalog 生成题库。标准答案和关键依据由规则评分器给出：

```bash
python -m src.question_gen --seed 42 --n-outdoor 200 --n-winter 200
```

默认会输出这些文件：

- `data/catalog_outdoor.jsonl`
- `data/catalog_winter.jsonl`
- `data/questions.jsonl`

## 运行实验

运行前先确认 `.env` 里至少有：

- `OPENAI_API_KEY`
- `MODEL`，例如 `gpt-5-mini` 或 `gpt-5`

如果 `MODEL` 以 `gpt-5` 开头（包括 `gpt-5-mini`），当前 API 一般不支持自定义 `temperature`。`eval_run` 会自动把温度改成 `1.0`，并打印提示。

单智能体示例：

```bash
python -m src.eval_run --strategy zero_shot --scenario outdoor_dwr_windbreaker --temperature 1.0 --repeats 2 --n-questions 50 --seed 123
```

`garmentagents_adaptive` 示例：

```bash
python -m src.eval_run --strategy garmentagents_adaptive --scenario winter_warm_midlayer --temperature 1.0 --repeats 2 --n-questions 50 --seed 123
```

### `max_tokens` 和重试

- `--max-tokens`，默认 `512`。表示单次调用允许的最大输出 token 数。
- `--retry-on-none`，默认开启。只有在没能从输出里抽出 `A/B/C/D` 时才会重试一次。
- `--retry-max-tokens`，默认 `1024`。这是重试时用的上限，不代表每次都会消耗这么多 token。

如果你比较在意成本，可以降低 `--retry-max-tokens`，或者直接用 `--no-retry-on-none` 关闭重试。

例如下面这条命令会先用 `512`，只有抽取失败时才升到 `1024`，同时显示进度和 ETA：

```bash
python -m src.eval_run --strategy cot_few_shot --scenario outdoor_dwr_windbreaker --temperature 1.0 --repeats 1 --n-questions 20 --seed 300 --max-tokens 512 --retry-on-none --retry-max-tokens 1024 --progress --progress-every 5
```

### 进度输出

- `--progress/--no-progress`：是否输出逐题进度和 ETA，默认开启
- `--progress-every N`：每隔 N 题打印一次进度

默认输出目录是 `outputs/`，其中常用的两个文件是：

- `outputs/results.csv`：按策略、场景、温度和重复次数汇总的结果
- `outputs/per_question_log.jsonl`：逐题日志，包含原始输出、抽取结果、token、时间和调用次数

## 汇总和绘图

```bash
python -m src.summarize --results outputs/results.csv --out-dir outputs/figs
```

`summarize` 默认会按 `(scenario, temperature, n_questions, model)` 分桶，这样不同设置不会被混到一张图里。输出文件名里也会带这些信息，例如 `acc_bar_outdoor_dwr_windbreaker__t1__n20__gpt-5-mini.png`。

如果只想看某个子集，可以直接加过滤条件：

```bash
python -m src.summarize --results outputs/results.csv --out-dir outputs/figs --scenario outdoor_dwr_windbreaker --temperature 1.0 --n-questions 20 --model gpt-5-mini
```

## 单元测试

```bash
python -m unittest discover -s tests -v
```



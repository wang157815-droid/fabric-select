## 项目进展总结（截至 2026-01-11）

本文件用于记录：**数据集概况**、**主实验设计**、**主实验结果**、**已生成的论文素材**与**下一步计划**。

---

## 总体状态

- **主实验矩阵**：已完成  
  - 2 个场景 × 10 个策略 × 3 次重复 × 500 题/场景 = **60/60 runs 完整跑完**
  - 主结果：`outputs/results_main.csv`（60 行）
  - 逐题日志：`outputs/per_question_log_main.jsonl`（≈30k 行；少量行可能因 JSON 解析失败被分析脚本跳过）
- **论文素材（主图/主表/统计检验）**：已生成  
  - 输出目录：`outputs/figs_main/`
- **非 LLM 朴素基线**：已完成并纳入主表/主图  
  - 策略：`nonllm_feasible_random`, `nonllm_simple_heuristic`（零 API 成本）
  - 已写入：`outputs/results_main.csv` 与 `outputs/per_question_log_main.jsonl`
- **跨模型复核（GPT-5 sanity check，子集）**：已完成  
  - 2 个场景 × 3 个代表策略 × 1 次重复 × 100 题/场景 = **6 runs**
  - 结果：`outputs/results_gpt5_sanity.csv`
  - 日志：`outputs/per_question_log_gpt5_sanity.jsonl`
  - 论文素材：`outputs/figs_main_gpt5_sanity/`
- **错误分析（Discussion 可用）**：已生成  
  - 报告：`outputs/error_analysis.md`（抽样 80 个错误案例 + 分类统计）
- **代码已提交并推送**  
  - 已推送到远程 `main` 分支
- **论文汇总总表/总图**：已生成并持续更新  
  - 表格汇总：`PAPER_TABLES.md`
  - 图片汇总：`PAPER_FIGURES.md`

---

## 数据集概况（Dataset v1 clean）

- **数据文件**：`data/questions_v1_clean.jsonl`
- **总题量**：1000  
  - `outdoor_dwr_windbreaker`：500  
  - `winter_warm_midlayer`：500

### Gold 答案分布（每场景）

| 场景 | A | B | C | D |
|---|---:|---:|---:|---:|
| outdoor_dwr_windbreaker | 120 | 129 | 121 | 130 |
| winter_warm_midlayer | 115 | 116 | 139 | 130 |

### 数据集“可发表可信度”要点（oracle margin & must 数量）

> 说明：`margin` 来自题目 `meta.oracle_scores` 的 top1-top2 差距（越小越难、越接近“可混淆”样本）。

| 场景 | n | margin_mean | margin_p10 | margin_p50 | margin_p90 | must_n_mean |
|---|---:|---:|---:|---:|---:|---:|
| outdoor_dwr_windbreaker | 500 | 0.105 | 0.058 | 0.093 | 0.164 | 2.924 |
| winter_warm_midlayer | 500 | 0.101 | 0.062 | 0.093 | 0.151 | 2.886 |

### must 约束类型覆盖（每场景包含该类约束的题目数）

| 场景 | perf | weight | compliance | lead | cost |
|---|---:|---:|---:|---:|---:|
| outdoor_dwr_windbreaker | 452 | 298 | 185 | 149 | 118 |
| winter_warm_midlayer | 436 | 167 | 170 | 140 | 167 |

> 对应文件：  
> - `outputs/figs_main/paper_dataset_summary_by_scenario.csv`  
> - `outputs/figs_main/paper_dataset_answer_dist.csv`  
> - `outputs/figs_main/paper_dataset_constraint_counts.csv`

---

## 主实验设计（Main Matrix）

### 配置

- **模型**：`gpt-5-mini`
- **temperature**：对 `gpt-5*` 系列在 `src/eval_run.py` 中强制为 **1.0**（避免“日志记录温度与实际调用不一致”）
- **每场景题量**：500  
- **重复次数**：3（seed=1000，repeat_idx=0/1/2）
- **输出 tokens 上限**：`max_tokens=512`（单次调用）  
- **重试**：`--retry-on-none`（仅单智能体策略在 `pred=None` 时会用更高 `retry_max_tokens=1024` 重试一次）

### 策略列表（10 个）

- 单智能体：`zero_shot`, `few_shot`, `cot_few_shot`, `self_reflection`, `fashionprompt`
- 多智能体：`voting`, `weighted_voting`, `borda`, `garmentagents_fixed`, `garmentagents_adaptive`

### 补充对比：非 LLM 朴素基线（0 API 成本）

- `nonllm_feasible_random`：先按 must 约束过滤可行集合，再随机选一个
- `nonllm_simple_heuristic`：先按 must 过滤，再用少量关键字段启发式排序选最优（不使用 `oracle_scores`，避免“把 ground truth 当 baseline”）

### 关键日志与可复现入口

- **逐题日志**：`outputs/per_question_log_main.jsonl`
- **run 汇总**：`outputs/results_main.csv`
- **生成论文主图/主表**：`scripts/run_main_figs.ps1`
- **主实验矩阵脚本**：`scripts/run_main_matrix.ps1`

---

## 主实验结果概览（Overall + per-scenario）

> 下表来自：`outputs/figs_main/paper_table1_overall_questions_path-data_questions_v1_clean.jsonl__t1__n500__gpt-5-mini.csv`  
> 指标含义：  
> - `Tokens/题`、`Calls/题`、`Latency(s)/题` 为**均值**（跨 2 场景 × 3 repeats）  
> - `Valid rate` ≈ 1 - `pred=null` 比例  

| 策略 | Acc(总体) | Acc SD | Tokens/题 | Calls/题 | Latency(s)/题 | Valid rate | LLM error rate | Acc(outdoor) | Acc(winter) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nonllm_simple_heuristic | 0.570 | 0.035 | 0 | 0.00 | 0.0 | 1.000 | 0.000 | 0.538 | 0.602 |
| nonllm_feasible_random | 0.365 | 0.014 | 0 | 0.00 | 0.0 | 1.000 | 0.000 | 0.365 | 0.365 |
| few_shot | 0.780 | 0.035 | 2072 | 1.26 | 9.8 | 0.996 | 0.001 | 0.749 | 0.811 |
| fashionprompt | 0.742 | 0.019 | 2085 | 1.48 | 15.7 | 0.996 | 0.004 | 0.725 | 0.758 |
| self_reflection | 0.735 | 0.042 | 3005 | 2.44 | 28.9 | 0.990 | 0.012 | 0.701 | 0.769 |
| cot_few_shot | 0.642 | 0.110 | 1867 | 1.18 | 10.6 | 0.946 | 0.053 | 0.567 | 0.716 |
| zero_shot | 0.572 | 0.039 | 2334 | 1.76 | 21.0 | 0.909 | 0.000 | 0.601 | 0.543 |
| weighted_voting | 0.415 | 0.018 | 6546 | 5.00 | 42.9 | 0.868 | 0.001 | 0.419 | 0.410 |
| voting | 0.409 | 0.017 | 6529 | 5.00 | 44.7 | 0.870 | 0.004 | 0.412 | 0.406 |
| borda | 0.406 | 0.019 | 6548 | 5.00 | 42.7 | 0.878 | 0.000 | 0.395 | 0.416 |
| garmentagents_fixed | 0.397 | 0.023 | 6553 | 5.00 | 41.9 | 0.859 | 0.000 | 0.390 | 0.405 |
| garmentagents_adaptive | 0.387 | 0.030 | 4890 | 3.73 | 31.6 | 0.845 | 0.000 | 0.406 | 0.369 |

### 关键观察（可直接写进论文）

- **最强策略**：`few_shot` 在两个场景均为最佳（总体 **0.780±0.035**；outdoor 0.749 / winter 0.811）。
- **成本-效果 trade-off**：多智能体类（`voting/weighted_voting/borda/garmentagents_fixed`）平均 **~6500 tokens/题、5 calls/题、~43s/题**，但准确率仅 **~0.40**；相较之下 `few_shot` **~2070 tokens/题、1.26 calls/题、~9.8s/题** 且准确率更高。
- **`garmentagents_adaptive`**：相比 `garmentagents_fixed`，calls/题 更低（3.73 vs 5.00）与 tokens/题 更低（4890 vs 6553），但准确率更低（0.387 vs 0.397），且 winter 场景明显更差（0.369）。
- **非 LLM baseline（0 API 成本）**：`nonllm_simple_heuristic` 达到 **0.57**，已接近/超过 `zero_shot`（0.57），说明“结构化属性 + must 过滤”的信息量在本任务中很强；但仍显著低于 `few_shot`（0.78），保留了 LLM 的增益空间。

---

## 统计检验（可信度）

输出文件：`outputs/figs_main/stats_tests.csv`

- **Kruskal–Wallis（全策略）**：
  - outdoor：p = 0.00226
  - winter：p = 0.00140
  - 结论：两场景下**策略总体差异显著**。
- **Pairwise Mann–Whitney + BH(FDR=0.05)**：当前基于 run-level（每策略每场景 n=3）功效偏低，BH 校正后未出现 `reject=True`；建议后续补充**按题配对**的检验（如 McNemar / paired bootstrap）增强说服力。

---

## 错误分析（Discussion 必备）

报告：`outputs/error_analysis.md`（脚本：`scripts/error_analysis.py`）

- **Total records（可解析行）**：29998  
- **Total errors**：13546（45.2%）

| 错误类型 | 数量 | 占比 | 解释 |
|---|---:|---:|---|
| soft_tradeoff | 7741 | 57.1% | 软偏好权衡失误（非 must 违规） |
| must_fail_chosen | 3276 | 24.2% | 选择了违反硬约束的选项（可用于讨论“合规/约束遵循”问题） |
| pred_null | 2529 | 18.7% | 未输出 A/B/C/D（影响 valid output rate） |

> 经验性观察：多智能体策略的 `pred_null` 与 `must_fail_chosen` 更突出，可作为“多智能体在结构化输出与约束一致性上的脆弱性”论据。

---

## 论文素材清单（已生成）

目录：`outputs/figs_main/`

- **主图**：
  - `acc_bar_*`：每场景准确率柱状图
  - `acc_vs_tokens_*`：准确率 vs tokens
  - `acc_vs_latency_*`：准确率 vs latency
  - `paper_tradeoff_bubble_*`：trade-off 气泡图（accuracy×tokens，气泡=latency）
  - `paper_acc_grouped_by_scenario_*`：分场景分组柱状图
- **分层分析**：
  - `paper_heatmap_difficulty_*`：按难度热力图
  - `paper_heatmap_constraint_*`：按约束类型热力图
  - `paper_acc_by_difficulty*.csv` / `paper_acc_by_constraint*.csv`：对应表格
- **稳健性/可用性指标**：
  - `paper_valid_output_rate_*`：有效输出率
  - `paper_llm_error_rate_*`：LLM 错误率
- **数据集可信度材料**：
  - `paper_dataset_margin_hist.png`
  - `paper_dataset_must_count.png`
  - `paper_dataset_answer_dist.csv`
  - `paper_dataset_constraint_counts.csv`

---

## 消融实验结果（Ablation Study）

目录：`outputs/figs_ablation/`

基于 `per_question_log_main.jsonl` 中已保存的 5-role agent 输出进行**离线计算**（无需额外 API 调用）。

### A1: Early Stopping 消融

| 变体 | Accuracy | Avg API Calls/题 |
|---|---:|---:|
| **With Early Stop**（默认） | 0.387 | **3.73** |
| No Early Stop（强制跑满 5 agents） | 0.387 | 5.00 |

**结论**：Early stopping 机制在准确率上**无损失**，同时节省 **~25%** 的 API 调用成本。

### B1: 聚合方式消融（5 agents 输出）

| 聚合方式 | Accuracy |
|---|---:|
| **majority**（多数投票） | **0.417** |
| **confidence**（纯置信度加权） | **0.417** |
| weighted（角色权重加权） | 0.397 |
| borda（Borda 计数） | 0.394 |

**结论**：简单的 majority voting 和 confidence-weighted 效果最好，复杂的 borda 和 weighted 反而略差。

### B2: Agent 数量扫描（K=1..5）

| K | Accuracy (outdoor) | Accuracy (winter) |
|---|---:|---:|
| 1 | 0.190 | 0.209 |
| 2 | 0.283 | 0.311 |
| 3 | 0.354 | 0.364 |
| 4 | 0.394 | 0.383 |
| **5** | **0.428** | **0.406** |

**结论**：Agent 数量与准确率呈**正相关**，K=5 时达到最佳。增加 agent 带来的边际收益在 K=3→4 时开始递减。

### C1: 角色 Dropout 消融

| Dropped Role | Accuracy | Δ vs Baseline |
|---|---:|---:|
| **none (baseline)** | **0.397** | — |
| textile | 0.378 | -0.019 |
| compliance | 0.374 | -0.023 |
| sourcing | 0.369 | -0.028 |
| product | 0.363 | -0.034 |
| **technical** | 0.361 | **-0.036** |

**结论**：移除任何角色都会导致准确率下降，其中 **technical** 角色贡献最大（drop 后下降 3.6pp），说明技术性能约束在面料选择中最为关键。

### 消融图表

- `ablation_a1_early_stop.png`：Early stop 对比
- `ablation_b1_aggregator.png`：聚合方式对比
- `ablation_b2_agents_sweep.png`：Agent 数量曲线
- `ablation_c1_role_dropout.png`：角色 dropout 对比
- `ablation_a3_threshold_sweep.png`：阈值扫描

---

## 下一步（可选增强）

- ✅ **消融实验（Ablation）**：已完成
- ✅ **高阶模型复核（GPT-5 sanity check）**：已完成  
  - 结果目录：`outputs/figs_main_gpt5_sanity/`
  - 代表策略在 gpt-5 上的趋势用于“外部有效性/敏感性分析”（子集 200 题）
- **论文写作清单（建议立刻启动）**  
  方法（数据集+策略定义）→ 实验设置 → 结果（主表+主图+trade-off）→ 消融分析 → 统计检验 → 错误分析 → 局限与未来工作。

---

## GPT-5 复核实验（Sanity Check）说明（重要复现细节）

- **运行脚本**：`scripts/run_gpt5_sanity.ps1`
- **结果/日志**：`outputs/results_gpt5_sanity.csv` / `outputs/per_question_log_gpt5_sanity.jsonl`
- **关键坑与修复**：  
  - 初版在 `max_tokens=512`（以及单智能体重试 `retry_max_tokens=1024`）下，`gpt-5` 有概率把输出预算全部用于 `reasoning_tokens`，导致 **返回 `status=incomplete` 且 `response_text=''`**，进而出现 `pred=None`（尤其是 `garmentagents_adaptive` 的多角色 JSON 输出更容易触发）。  
  - 现已将 gpt-5 复核的 `max_tokens` 提高到 **1536**（重试 2048），从而稳定产出可解析文本/JSON，避免无效消耗。


# 论文表格汇总（自动生成）

- 生成时间：2026-01-10 18:34:29  
- 脚本：`scripts/compile_paper_tables.py`

## 主实验（Main Results）

### Table 1 总体结果汇总（mean±std，含成本/可靠性指标）

- **来源**: `outputs/figs_main/paper_table1_overall_questions_path-data_questions_v1_clean.jsonl__t1__n500__gpt-5-mini.csv`  
- **行数**: 12  
- **列数**: 13

| strategy | n | acc_mean | acc_std | tokens_mean | calls_mean | latency_mean | valid_output_rate_mean | llm_error_rate_mean | acc_mean__outdoor_dwr_windbreaker | acc_mean__winter_warm_midlayer | acc_std__outdoor_dwr_windbreaker | acc_std__winter_warm_midlayer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nonllm_feasible_random | 6 | 0.365 | 0.014 | 0 | 0.00 | 0.00 | 1.000 | 0 | 0.365 | 0.365 | 0.016 | 0.016 |
| nonllm_simple_heuristic | 6 | 0.570 | 0.035 | 0 | 0.00 | 0.00 | 1.000 | 0 | 0.538 | 0.602 | 0.000 | 0.000 |
| zero_shot | 6 | 0.572 | 0.039 | 2334 | 1.76 | 20.96 | 0.909 | 3.33e-04 | 0.601 | 0.543 | 0.025 | 0.025 |
| few_shot | 6 | 0.780 | 0.035 | 2072 | 1.26 | 9.78 | 0.996 | 0.001 | 0.749 | 0.811 | 0.011 | 0.004 |
| cot_few_shot | 6 | 0.642 | 0.110 | 1867 | 1.18 | 10.58 | 0.946 | 0.053 | 0.567 | 0.716 | 0.116 | 0.008 |
| self_reflection | 6 | 0.735 | 0.042 | 3005 | 2.44 | 28.87 | 0.990 | 0.012 | 0.701 | 0.769 | 0.001 | 0.030 |
| fashionprompt | 6 | 0.742 | 0.019 | 2085 | 1.48 | 15.68 | 0.996 | 0.0037 | 0.725 | 0.758 | 0.005 | 0.007 |
| voting | 6 | 0.409 | 0.017 | 6529 | 5.00 | 44.67 | 0.870 | 0.004 | 0.412 | 0.406 | 0.019 | 0.017 |
| weighted_voting | 6 | 0.415 | 0.018 | 6546 | 5.00 | 42.91 | 0.868 | 0.001 | 0.419 | 0.410 | 0.027 | 0.005 |
| borda | 6 | 0.406 | 0.019 | 6548 | 5.00 | 42.71 | 0.878 | 0 | 0.395 | 0.416 | 0.011 | 0.021 |
| garmentagents_fixed | 6 | 0.397 | 0.023 | 6553 | 5.00 | 41.92 | 0.859 | 0 | 0.390 | 0.405 | 0.030 | 0.017 |
| garmentagents_adaptive | 6 | 0.387 | 0.030 | 4890 | 3.73 | 31.58 | 0.845 | 3.33e-04 | 0.406 | 0.369 | 0.027 | 0.022 |

### Table 2 分场景结果汇总（每场景 mean±std）

- **来源**: `outputs/figs_main/summary_by_strategy.csv`  
- **行数**: 24  
- **列数**: 13

| scenario | temperature | n_questions | model | strategy | n | acc_mean | acc_std | tokens_mean | calls_mean | latency_mean | valid_output_rate_mean | llm_error_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | few_shot | 3 | 0.749 | 0.011 | 2118 | 1.26 | 10.70 | 0.999 | 0 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | fashionprompt | 3 | 0.725 | 0.005 | 2030 | 1.43 | 15.62 | 0.992 | 0.0073 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | self_reflection | 3 | 0.701 | 0.001 | 3105 | 2.47 | 25.16 | 0.984 | 0.017 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | zero_shot | 3 | 0.601 | 0.025 | 2388 | 1.77 | 24.06 | 0.958 | 6.67e-04 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | cot_few_shot | 3 | 0.567 | 0.116 | 1836 | 1.25 | 11.84 | 0.893 | 0.107 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | nonllm_simple_heuristic | 3 | 0.538 | 0.000 | 0 | 0.00 | 0.00 | 1.000 | 0 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | weighted_voting | 3 | 0.419 | 0.027 | 6694 | 5.00 | 45.49 | 0.891 | 6.67e-04 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | voting | 3 | 0.412 | 0.019 | 6654 | 5.00 | 47.49 | 0.897 | 0.008 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | garmentagents_adaptive | 3 | 0.406 | 0.027 | 4881 | 3.64 | 31.23 | 0.870 | 6.67e-04 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | borda | 3 | 0.395 | 0.011 | 6695 | 5.00 | 45.11 | 0.907 | 0 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | garmentagents_fixed | 3 | 0.390 | 0.030 | 6701 | 5.00 | 43.59 | 0.891 | 0 |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | nonllm_feasible_random | 3 | 0.365 | 0.016 | 0 | 0.00 | 0.00 | 1.000 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | few_shot | 3 | 0.811 | 0.004 | 2026 | 1.26 | 8.87 | 0.993 | 0.002 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | self_reflection | 3 | 0.769 | 0.030 | 2904 | 2.41 | 32.57 | 0.997 | 0.0067 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | fashionprompt | 3 | 0.758 | 0.007 | 2139 | 1.54 | 15.75 | 1.000 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | cot_few_shot | 3 | 0.716 | 0.008 | 1897 | 1.12 | 9.33 | 0.999 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | nonllm_simple_heuristic | 3 | 0.602 | 0.000 | 0 | 0.00 | 0.00 | 1.000 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | zero_shot | 3 | 0.543 | 0.025 | 2279 | 1.75 | 17.87 | 0.860 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | borda | 3 | 0.416 | 0.021 | 6401 | 5.00 | 40.30 | 0.849 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | weighted_voting | 3 | 0.410 | 0.005 | 6398 | 5.00 | 40.34 | 0.844 | 0.0013 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | voting | 3 | 0.406 | 0.017 | 6403 | 5.00 | 41.84 | 0.842 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | garmentagents_fixed | 3 | 0.405 | 0.017 | 6405 | 5.00 | 40.24 | 0.827 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | garmentagents_adaptive | 3 | 0.369 | 0.022 | 4899 | 3.82 | 31.93 | 0.819 | 0 |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | nonllm_feasible_random | 3 | 0.365 | 0.016 | 0 | 0.00 | 0.00 | 1.000 | 0 |

### Table 3 按约束类型分组的准确率（mean±std）

- **来源**: `outputs/figs_main/paper_acc_by_constraint.csv`  
- **行数**: 120  
- **列数**: 6

<details>
<summary>展开表格（120 行）</summary>

| strategy | scenario | constraint | acc_mean | acc_std | n_runs |
| --- | --- | --- | --- | --- | --- |
| borda | outdoor_dwr_windbreaker | compliance | 0.414 | 0.033 | 3 |
| borda | outdoor_dwr_windbreaker | cost | 0.387 | 0.018 | 3 |
| borda | outdoor_dwr_windbreaker | lead | 0.360 | 0.021 | 3 |
| borda | outdoor_dwr_windbreaker | perf | 0.396 | 0.018 | 3 |
| borda | outdoor_dwr_windbreaker | weight | 0.385 | 0.036 | 3 |
| borda | winter_warm_midlayer | compliance | 0.416 | 0.022 | 3 |
| borda | winter_warm_midlayer | cost | 0.363 | 0.031 | 3 |
| borda | winter_warm_midlayer | lead | 0.402 | 0.037 | 3 |
| borda | winter_warm_midlayer | perf | 0.420 | 0.031 | 3 |
| borda | winter_warm_midlayer | weight | 0.429 | 0.039 | 3 |
| cot_few_shot | outdoor_dwr_windbreaker | compliance | 0.589 | 0.109 | 3 |
| cot_few_shot | outdoor_dwr_windbreaker | cost | 0.562 | 0.113 | 3 |
| cot_few_shot | outdoor_dwr_windbreaker | lead | 0.570 | 0.110 | 3 |
| cot_few_shot | outdoor_dwr_windbreaker | perf | 0.559 | 0.124 | 3 |
| cot_few_shot | outdoor_dwr_windbreaker | weight | 0.591 | 0.120 | 3 |
| cot_few_shot | winter_warm_midlayer | compliance | 0.706 | 0.006 | 3 |
| cot_few_shot | winter_warm_midlayer | cost | 0.711 | 0.019 | 3 |
| cot_few_shot | winter_warm_midlayer | lead | 0.719 | 0.061 | 3 |
| cot_few_shot | winter_warm_midlayer | perf | 0.717 | 0.012 | 3 |
| cot_few_shot | winter_warm_midlayer | weight | 0.727 | 0.003 | 3 |
| fashionprompt | outdoor_dwr_windbreaker | compliance | 0.748 | 0.020 | 3 |
| fashionprompt | outdoor_dwr_windbreaker | cost | 0.718 | 0.018 | 3 |
| fashionprompt | outdoor_dwr_windbreaker | lead | 0.727 | 0.027 | 3 |
| fashionprompt | outdoor_dwr_windbreaker | perf | 0.727 | 0.005 | 3 |
| fashionprompt | outdoor_dwr_windbreaker | weight | 0.724 | 0.010 | 3 |
| fashionprompt | winter_warm_midlayer | compliance | 0.755 | 0.012 | 3 |
| fashionprompt | winter_warm_midlayer | cost | 0.780 | 0.017 | 3 |
| fashionprompt | winter_warm_midlayer | lead | 0.793 | 0.021 | 3 |
| fashionprompt | winter_warm_midlayer | perf | 0.748 | 0.006 | 3 |
| fashionprompt | winter_warm_midlayer | weight | 0.770 | 0.012 | 3 |
| few_shot | outdoor_dwr_windbreaker | compliance | 0.768 | 0.030 | 3 |
| few_shot | outdoor_dwr_windbreaker | cost | 0.794 | 0.021 | 3 |
| few_shot | outdoor_dwr_windbreaker | lead | 0.716 | 0.022 | 3 |
| few_shot | outdoor_dwr_windbreaker | perf | 0.750 | 0.006 | 3 |
| few_shot | outdoor_dwr_windbreaker | weight | 0.770 | 0.014 | 3 |
| few_shot | winter_warm_midlayer | compliance | 0.796 | 0.009 | 3 |
| few_shot | winter_warm_midlayer | cost | 0.808 | 0.016 | 3 |
| few_shot | winter_warm_midlayer | lead | 0.840 | 0.008 | 3 |
| few_shot | winter_warm_midlayer | perf | 0.813 | 0.006 | 3 |
| few_shot | winter_warm_midlayer | weight | 0.840 | 0.035 | 3 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | compliance | 0.445 | 0.045 | 3 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | cost | 0.401 | 0.030 | 3 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | lead | 0.371 | 0.021 | 3 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | perf | 0.398 | 0.022 | 3 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | weight | 0.425 | 0.052 | 3 |
| garmentagents_adaptive | winter_warm_midlayer | compliance | 0.335 | 0.026 | 3 |
| garmentagents_adaptive | winter_warm_midlayer | cost | 0.349 | 0.049 | 3 |
| garmentagents_adaptive | winter_warm_midlayer | lead | 0.412 | 0.025 | 3 |
| garmentagents_adaptive | winter_warm_midlayer | perf | 0.359 | 0.019 | 3 |
| garmentagents_adaptive | winter_warm_midlayer | weight | 0.385 | 0.019 | 3 |
| garmentagents_fixed | outdoor_dwr_windbreaker | compliance | 0.418 | 0.038 | 3 |
| garmentagents_fixed | outdoor_dwr_windbreaker | cost | 0.415 | 0.045 | 3 |
| garmentagents_fixed | outdoor_dwr_windbreaker | lead | 0.356 | 0.027 | 3 |
| garmentagents_fixed | outdoor_dwr_windbreaker | perf | 0.390 | 0.036 | 3 |
| garmentagents_fixed | outdoor_dwr_windbreaker | weight | 0.390 | 0.037 | 3 |
| garmentagents_fixed | winter_warm_midlayer | compliance | 0.408 | 0.034 | 3 |
| garmentagents_fixed | winter_warm_midlayer | cost | 0.397 | 0.018 | 3 |
| garmentagents_fixed | winter_warm_midlayer | lead | 0.388 | 0.048 | 3 |
| garmentagents_fixed | winter_warm_midlayer | perf | 0.399 | 0.011 | 3 |
| garmentagents_fixed | winter_warm_midlayer | weight | 0.405 | 0.009 | 3 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | compliance | 0.360 | 0.050 | 3 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | cost | 0.393 | 0.027 | 3 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | lead | 0.338 | 0.032 | 3 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | perf | 0.366 | 0.018 | 3 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | weight | 0.360 | 0.030 | 3 |
| nonllm_feasible_random | winter_warm_midlayer | compliance | 0.376 | 0.069 | 3 |
| nonllm_feasible_random | winter_warm_midlayer | cost | 0.381 | 0.019 | 3 |
| nonllm_feasible_random | winter_warm_midlayer | lead | 0.350 | 0.058 | 3 |
| nonllm_feasible_random | winter_warm_midlayer | perf | 0.358 | 0.014 | 3 |
| nonllm_feasible_random | winter_warm_midlayer | weight | 0.361 | 0.042 | 3 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | compliance | 0.524 | 0.000 | 3 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | cost | 0.669 | 0.000 | 3 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | lead | 0.443 | 0.000 | 3 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | perf | 0.531 | 0.000 | 3 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | weight | 0.544 | 0.000 | 3 |
| nonllm_simple_heuristic | winter_warm_midlayer | compliance | 0.576 | 0.000 | 3 |
| nonllm_simple_heuristic | winter_warm_midlayer | cost | 0.569 | 0.000 | 3 |
| nonllm_simple_heuristic | winter_warm_midlayer | lead | 0.693 | 0.000 | 3 |
| nonllm_simple_heuristic | winter_warm_midlayer | perf | 0.596 | 0.000 | 3 |
| nonllm_simple_heuristic | winter_warm_midlayer | weight | 0.593 | 0.000 | 3 |
| self_reflection | outdoor_dwr_windbreaker | compliance | 0.701 | 0.017 | 3 |
| self_reflection | outdoor_dwr_windbreaker | cost | 0.729 | 0.008 | 3 |
| self_reflection | outdoor_dwr_windbreaker | lead | 0.682 | 0.004 | 3 |
| self_reflection | outdoor_dwr_windbreaker | perf | 0.701 | 0.002 | 3 |
| self_reflection | outdoor_dwr_windbreaker | weight | 0.717 | 0.002 | 3 |
| self_reflection | winter_warm_midlayer | compliance | 0.735 | 0.036 | 3 |
| self_reflection | winter_warm_midlayer | cost | 0.745 | 0.040 | 3 |
| self_reflection | winter_warm_midlayer | lead | 0.819 | 0.022 | 3 |
| self_reflection | winter_warm_midlayer | perf | 0.770 | 0.033 | 3 |
| self_reflection | winter_warm_midlayer | weight | 0.802 | 0.026 | 3 |
| voting | outdoor_dwr_windbreaker | compliance | 0.440 | 0.008 | 3 |
| voting | outdoor_dwr_windbreaker | cost | 0.410 | 0.049 | 3 |
| voting | outdoor_dwr_windbreaker | lead | 0.394 | 0.030 | 3 |
| voting | outdoor_dwr_windbreaker | perf | 0.412 | 0.020 | 3 |
| voting | outdoor_dwr_windbreaker | weight | 0.407 | 0.034 | 3 |
| voting | winter_warm_midlayer | compliance | 0.396 | 0.012 | 3 |
| voting | winter_warm_midlayer | cost | 0.393 | 0.021 | 3 |
| voting | winter_warm_midlayer | lead | 0.390 | 0.027 | 3 |
| voting | winter_warm_midlayer | perf | 0.399 | 0.016 | 3 |
| voting | winter_warm_midlayer | weight | 0.447 | 0.024 | 3 |
| weighted_voting | outdoor_dwr_windbreaker | compliance | 0.440 | 0.039 | 3 |
| weighted_voting | outdoor_dwr_windbreaker | cost | 0.415 | 0.022 | 3 |
| weighted_voting | outdoor_dwr_windbreaker | lead | 0.405 | 0.015 | 3 |
| weighted_voting | outdoor_dwr_windbreaker | perf | 0.409 | 0.025 | 3 |
| weighted_voting | outdoor_dwr_windbreaker | weight | 0.428 | 0.019 | 3 |
| weighted_voting | winter_warm_midlayer | compliance | 0.392 | 0.019 | 3 |
| weighted_voting | winter_warm_midlayer | cost | 0.397 | 0.034 | 3 |
| weighted_voting | winter_warm_midlayer | lead | 0.386 | 0.021 | 3 |
| weighted_voting | winter_warm_midlayer | perf | 0.410 | 0.009 | 3 |
| weighted_voting | winter_warm_midlayer | weight | 0.427 | 0.012 | 3 |
| zero_shot | outdoor_dwr_windbreaker | compliance | 0.602 | 0.034 | 4 |
| zero_shot | outdoor_dwr_windbreaker | cost | 0.617 | 0.039 | 4 |
| zero_shot | outdoor_dwr_windbreaker | lead | 0.621 | 0.096 | 4 |
| zero_shot | outdoor_dwr_windbreaker | perf | 0.604 | 0.026 | 4 |
| zero_shot | outdoor_dwr_windbreaker | weight | 0.646 | 0.043 | 4 |
| zero_shot | winter_warm_midlayer | compliance | 0.514 | 0.033 | 3 |
| zero_shot | winter_warm_midlayer | cost | 0.545 | 0.048 | 3 |
| zero_shot | winter_warm_midlayer | lead | 0.581 | 0.036 | 3 |
| zero_shot | winter_warm_midlayer | perf | 0.546 | 0.025 | 3 |
| zero_shot | winter_warm_midlayer | weight | 0.587 | 0.032 | 3 |

</details>


### Table A1 按约束类型分组的准确率（每个 repeat/run）

- **来源**: `outputs/figs_main/paper_acc_by_constraint_per_run.csv`  
- **行数**: 365  
- **列数**: 8

<details>
<summary>展开表格（365 行）</summary>

| strategy | scenario | temperature | repeat_idx | seed | n | acc | constraint |
| --- | --- | --- | --- | --- | --- | --- | --- |
| borda | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.381 | cost |
| borda | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.373 | cost |
| borda | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.407 | cost |
| borda | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.389 | cost |
| borda | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.329 | cost |
| borda | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.371 | cost |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.619 | cost |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.432 | cost |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.636 | cost |
| cot_few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.689 | cost |
| cot_few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.719 | cost |
| cot_few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.725 | cost |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.712 | cost |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.737 | cost |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.703 | cost |
| fashionprompt | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.760 | cost |
| fashionprompt | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.790 | cost |
| fashionprompt | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.790 | cost |
| few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.771 | cost |
| few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.797 | cost |
| few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.814 | cost |
| few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.820 | cost |
| few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.790 | cost |
| few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.814 | cost |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.373 | cost |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.432 | cost |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.398 | cost |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.371 | cost |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.293 | cost |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.383 | cost |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.398 | cost |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.466 | cost |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.381 | cost |
| garmentagents_fixed | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.377 | cost |
| garmentagents_fixed | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.413 | cost |
| garmentagents_fixed | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.401 | cost |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.373 | cost |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.381 | cost |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.424 | cost |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.359 | cost |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.395 | cost |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.389 | cost |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.669 | cost |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.669 | cost |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.669 | cost |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.569 | cost |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.569 | cost |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.569 | cost |
| self_reflection | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.729 | cost |
| self_reflection | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.737 | cost |
| self_reflection | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.720 | cost |
| self_reflection | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.790 | cost |
| self_reflection | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.725 | cost |
| self_reflection | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.719 | cost |
| voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.466 | cost |
| voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.381 | cost |
| voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.381 | cost |
| voting | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.371 | cost |
| voting | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.413 | cost |
| voting | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.395 | cost |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 118 | 0.432 | cost |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.424 | cost |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.390 | cost |
| weighted_voting | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.425 | cost |
| weighted_voting | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.407 | cost |
| weighted_voting | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.359 | cost |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 0 | 11 | 0.636 | cost |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 107 | 0.664 | cost |
| zero_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 118 | 0.585 | cost |
| zero_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 118 | 0.585 | cost |
| zero_shot | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.491 | cost |
| zero_shot | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.563 | cost |
| zero_shot | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.581 | cost |
| borda | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.383 | lead |
| borda | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.356 | lead |
| borda | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.342 | lead |
| borda | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.443 | lead |
| borda | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.393 | lead |
| borda | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.371 | lead |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.624 | lead |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.443 | lead |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 148 | 0.642 | lead |
| cot_few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.657 | lead |
| cot_few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.721 | lead |
| cot_few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.779 | lead |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.732 | lead |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.698 | lead |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.752 | lead |
| fashionprompt | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.814 | lead |
| fashionprompt | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.771 | lead |
| fashionprompt | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.793 | lead |
| few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.725 | lead |
| few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.691 | lead |
| few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.732 | lead |
| few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.836 | lead |
| few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.850 | lead |
| few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.836 | lead |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.349 | lead |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.389 | lead |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.376 | lead |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.436 | lead |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.386 | lead |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.414 | lead |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.383 | lead |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.356 | lead |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.329 | lead |
| garmentagents_fixed | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.429 | lead |
| garmentagents_fixed | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.336 | lead |
| garmentagents_fixed | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.400 | lead |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.302 | lead |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.362 | lead |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.349 | lead |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.286 | lead |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.364 | lead |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.400 | lead |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.443 | lead |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.443 | lead |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.443 | lead |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.693 | lead |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.693 | lead |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.693 | lead |
| self_reflection | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.685 | lead |
| self_reflection | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.678 | lead |
| self_reflection | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.685 | lead |
| self_reflection | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.843 | lead |
| self_reflection | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.814 | lead |
| self_reflection | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.800 | lead |
| voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.423 | lead |
| voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.396 | lead |
| voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.362 | lead |
| voting | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.421 | lead |
| voting | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.379 | lead |
| voting | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.371 | lead |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 149 | 0.396 | lead |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.396 | lead |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.423 | lead |
| weighted_voting | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.386 | lead |
| weighted_voting | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.364 | lead |
| weighted_voting | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.407 | lead |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 0 | 41 | 0.756 | lead |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 108 | 0.602 | lead |
| zero_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 149 | 0.530 | lead |
| zero_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 149 | 0.597 | lead |
| zero_shot | winter_warm_midlayer | 1 | 0 | 1000 | 140 | 0.543 | lead |
| zero_shot | winter_warm_midlayer | 1 | 1 | 1000 | 140 | 0.614 | lead |
| zero_shot | winter_warm_midlayer | 1 | 2 | 1000 | 140 | 0.586 | lead |
| borda | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.384 | compliance |
| borda | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.411 | compliance |
| borda | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.449 | compliance |
| borda | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.441 | compliance |
| borda | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.406 | compliance |
| borda | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.400 | compliance |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.632 | compliance |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.465 | compliance |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.670 | compliance |
| cot_few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.712 | compliance |
| cot_few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.700 | compliance |
| cot_few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.706 | compliance |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.757 | compliance |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.724 | compliance |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.762 | compliance |
| fashionprompt | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.741 | compliance |
| fashionprompt | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.765 | compliance |
| fashionprompt | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.759 | compliance |
| few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.795 | compliance |
| few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.735 | compliance |
| few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.773 | compliance |
| few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.788 | compliance |
| few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.794 | compliance |
| few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.806 | compliance |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.395 | compliance |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.481 | compliance |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.459 | compliance |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.324 | compliance |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.318 | compliance |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.365 | compliance |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.454 | compliance |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.422 | compliance |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.378 | compliance |
| garmentagents_fixed | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.447 | compliance |
| garmentagents_fixed | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.382 | compliance |
| garmentagents_fixed | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.394 | compliance |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.389 | compliance |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.389 | compliance |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.303 | compliance |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.300 | compliance |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.435 | compliance |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.394 | compliance |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.524 | compliance |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.524 | compliance |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.524 | compliance |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.576 | compliance |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.576 | compliance |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.576 | compliance |
| self_reflection | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.708 | compliance |
| self_reflection | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.714 | compliance |
| self_reflection | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.681 | compliance |
| self_reflection | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.759 | compliance |
| self_reflection | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.753 | compliance |
| self_reflection | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.694 | compliance |
| voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.438 | compliance |
| voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.449 | compliance |
| voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.432 | compliance |
| voting | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.406 | compliance |
| voting | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.400 | compliance |
| voting | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.382 | compliance |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 185 | 0.465 | compliance |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.459 | compliance |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.395 | compliance |
| weighted_voting | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.400 | compliance |
| weighted_voting | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.371 | compliance |
| weighted_voting | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.406 | compliance |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 0 | 40 | 0.625 | compliance |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 145 | 0.621 | compliance |
| zero_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 185 | 0.551 | compliance |
| zero_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 185 | 0.611 | compliance |
| zero_shot | winter_warm_midlayer | 1 | 0 | 1000 | 170 | 0.476 | compliance |
| zero_shot | winter_warm_midlayer | 1 | 1 | 1000 | 170 | 0.524 | compliance |
| zero_shot | winter_warm_midlayer | 1 | 2 | 1000 | 170 | 0.541 | compliance |
| borda | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.346 | weight |
| borda | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.393 | weight |
| borda | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.416 | weight |
| borda | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.467 | weight |
| borda | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.431 | weight |
| borda | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.389 | weight |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.648 | weight |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.453 | weight |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 296 | 0.672 | weight |
| cot_few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.725 | weight |
| cot_few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.725 | weight |
| cot_few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.731 | weight |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.735 | weight |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.718 | weight |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.718 | weight |
| fashionprompt | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.760 | weight |
| fashionprompt | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.784 | weight |
| fashionprompt | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.766 | weight |
| few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.765 | weight |
| few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.758 | weight |
| few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.785 | weight |
| few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.880 | weight |
| few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.814 | weight |
| few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.826 | weight |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.366 | weight |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.463 | weight |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.446 | weight |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.371 | weight |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.377 | weight |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.407 | weight |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.393 | weight |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.426 | weight |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.352 | weight |
| garmentagents_fixed | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.413 | weight |
| garmentagents_fixed | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.395 | weight |
| garmentagents_fixed | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.407 | weight |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.326 | weight |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.383 | weight |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.372 | weight |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.365 | weight |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.401 | weight |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.317 | weight |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.544 | weight |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.544 | weight |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.544 | weight |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.593 | weight |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.593 | weight |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.593 | weight |
| self_reflection | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.718 | weight |
| self_reflection | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.718 | weight |
| self_reflection | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.715 | weight |
| self_reflection | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.832 | weight |
| self_reflection | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.784 | weight |
| self_reflection | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.790 | weight |
| voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.433 | weight |
| voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.419 | weight |
| voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.369 | weight |
| voting | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.473 | weight |
| voting | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.425 | weight |
| voting | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.443 | weight |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 298 | 0.423 | weight |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.450 | weight |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.413 | weight |
| weighted_voting | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.437 | weight |
| weighted_voting | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.413 | weight |
| weighted_voting | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.431 | weight |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 0 | 68 | 0.706 | weight |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 230 | 0.648 | weight |
| zero_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 298 | 0.624 | weight |
| zero_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 298 | 0.607 | weight |
| zero_shot | winter_warm_midlayer | 1 | 0 | 1000 | 167 | 0.575 | weight |
| zero_shot | winter_warm_midlayer | 1 | 1 | 1000 | 167 | 0.563 | weight |
| zero_shot | winter_warm_midlayer | 1 | 2 | 1000 | 167 | 0.623 | weight |
| borda | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.381 | perf |
| borda | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.392 | perf |
| borda | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.416 | perf |
| borda | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.450 | perf |
| borda | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.424 | perf |
| borda | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.388 | perf |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.639 | perf |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.416 | perf |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 450 | 0.622 | perf |
| cot_few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.704 | perf |
| cot_few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.720 | perf |
| cot_few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.727 | perf |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.730 | perf |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.721 | perf |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.730 | perf |
| fashionprompt | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.743 | perf |
| fashionprompt | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.755 | perf |
| fashionprompt | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.748 | perf |
| few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.752 | perf |
| few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.743 | perf |
| few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.754 | perf |
| few_shot | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.819 | perf |
| few_shot | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.807 | perf |
| few_shot | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.814 | perf |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.374 | perf |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.418 | perf |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.403 | perf |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.365 | perf |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.337 | perf |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.374 | perf |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.403 | perf |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.418 | perf |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.350 | perf |
| garmentagents_fixed | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.411 | perf |
| garmentagents_fixed | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.390 | perf |
| garmentagents_fixed | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.397 | perf |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.345 | perf |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.372 | perf |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.381 | perf |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.342 | perf |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.369 | perf |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.362 | perf |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.531 | perf |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.531 | perf |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.531 | perf |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.596 | perf |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.596 | perf |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.596 | perf |
| self_reflection | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.704 | perf |
| self_reflection | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.699 | perf |
| self_reflection | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.701 | perf |
| self_reflection | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.807 | perf |
| self_reflection | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.745 | perf |
| self_reflection | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.757 | perf |
| voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.429 | perf |
| voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.416 | perf |
| voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.389 | perf |
| voting | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.406 | perf |
| voting | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.411 | perf |
| voting | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.381 | perf |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 452 | 0.429 | perf |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.416 | perf |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.381 | perf |
| weighted_voting | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.420 | perf |
| weighted_voting | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.408 | perf |
| weighted_voting | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.401 | perf |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 0 | 95 | 0.632 | perf |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | 357 | 0.619 | perf |
| zero_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | 452 | 0.577 | perf |
| zero_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | 452 | 0.586 | perf |
| zero_shot | winter_warm_midlayer | 1 | 0 | 1000 | 436 | 0.521 | perf |
| zero_shot | winter_warm_midlayer | 1 | 1 | 1000 | 436 | 0.571 | perf |
| zero_shot | winter_warm_midlayer | 1 | 2 | 1000 | 436 | 0.546 | perf |

</details>


### Table 4 按难度分组的准确率（mean±std）

- **来源**: `outputs/figs_main/paper_acc_by_difficulty.csv`  
- **行数**: 72  
- **列数**: 5

| strategy | scenario | difficulty | acc_mean | acc_std |
| --- | --- | --- | --- | --- |
| borda | outdoor_dwr_windbreaker | easy | 0.429 | 0.050 |
| borda | outdoor_dwr_windbreaker | hard | 0.359 | 0.018 |
| borda | outdoor_dwr_windbreaker | medium | 0.399 | 0.015 |
| borda | winter_warm_midlayer | easy | 0.487 | 0.029 |
| borda | winter_warm_midlayer | hard | 0.383 | 0.020 |
| borda | winter_warm_midlayer | medium | 0.379 | 0.059 |
| cot_few_shot | outdoor_dwr_windbreaker | easy | 0.727 | 0.026 |
| cot_few_shot | outdoor_dwr_windbreaker | hard | 0.394 | 0.317 |
| cot_few_shot | outdoor_dwr_windbreaker | medium | 0.587 | 0.027 |
| cot_few_shot | winter_warm_midlayer | easy | 0.844 | 0.013 |
| cot_few_shot | winter_warm_midlayer | hard | 0.590 | 0.046 |
| cot_few_shot | winter_warm_midlayer | medium | 0.720 | 0.033 |
| fashionprompt | outdoor_dwr_windbreaker | easy | 0.840 | 0.016 |
| fashionprompt | outdoor_dwr_windbreaker | hard | 0.669 | 0.018 |
| fashionprompt | outdoor_dwr_windbreaker | medium | 0.671 | 0.027 |
| fashionprompt | winter_warm_midlayer | easy | 0.885 | 0.031 |
| fashionprompt | winter_warm_midlayer | hard | 0.667 | 0.021 |
| fashionprompt | winter_warm_midlayer | medium | 0.727 | 0.016 |
| few_shot | outdoor_dwr_windbreaker | easy | 0.855 | 0.014 |
| few_shot | outdoor_dwr_windbreaker | hard | 0.682 | 0.010 |
| few_shot | outdoor_dwr_windbreaker | medium | 0.713 | 0.021 |
| few_shot | winter_warm_midlayer | easy | 0.929 | 0.003 |
| few_shot | winter_warm_midlayer | hard | 0.711 | 0.028 |
| few_shot | winter_warm_midlayer | medium | 0.799 | 0.028 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | easy | 0.444 | 0.034 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | hard | 0.359 | 0.056 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | medium | 0.417 | 0.019 |
| garmentagents_adaptive | winter_warm_midlayer | easy | 0.426 | 0.017 |
| garmentagents_adaptive | winter_warm_midlayer | hard | 0.335 | 0.027 |
| garmentagents_adaptive | winter_warm_midlayer | medium | 0.346 | 0.056 |
| garmentagents_fixed | outdoor_dwr_windbreaker | easy | 0.434 | 0.030 |
| garmentagents_fixed | outdoor_dwr_windbreaker | hard | 0.365 | 0.041 |
| garmentagents_fixed | outdoor_dwr_windbreaker | medium | 0.373 | 0.018 |
| garmentagents_fixed | winter_warm_midlayer | easy | 0.491 | 0.032 |
| garmentagents_fixed | winter_warm_midlayer | hard | 0.351 | 0.000 |
| garmentagents_fixed | winter_warm_midlayer | medium | 0.375 | 0.020 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | easy | 0.374 | 0.022 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | hard | 0.378 | 0.048 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | medium | 0.343 | 0.052 |
| nonllm_feasible_random | winter_warm_midlayer | easy | 0.376 | 0.021 |
| nonllm_feasible_random | winter_warm_midlayer | hard | 0.377 | 0.048 |
| nonllm_feasible_random | winter_warm_midlayer | medium | 0.342 | 0.061 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | easy | 0.607 | 0.000 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | hard | 0.506 | 0.000 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | medium | 0.503 | 0.000 |
| nonllm_simple_heuristic | winter_warm_midlayer | easy | 0.752 | 0.000 |
| nonllm_simple_heuristic | winter_warm_midlayer | hard | 0.517 | 0.000 |
| nonllm_simple_heuristic | winter_warm_midlayer | medium | 0.540 | 0.000 |
| self_reflection | outdoor_dwr_windbreaker | easy | 0.845 | 0.029 |
| self_reflection | outdoor_dwr_windbreaker | hard | 0.629 | 0.027 |
| self_reflection | outdoor_dwr_windbreaker | medium | 0.633 | 0.047 |
| self_reflection | winter_warm_midlayer | easy | 0.899 | 0.030 |
| self_reflection | winter_warm_midlayer | hard | 0.674 | 0.039 |
| self_reflection | winter_warm_midlayer | medium | 0.739 | 0.022 |
| voting | outdoor_dwr_windbreaker | easy | 0.460 | 0.043 |
| voting | outdoor_dwr_windbreaker | hard | 0.388 | 0.031 |
| voting | outdoor_dwr_windbreaker | medium | 0.389 | 0.006 |
| voting | winter_warm_midlayer | easy | 0.467 | 0.042 |
| voting | winter_warm_midlayer | hard | 0.341 | 0.032 |
| voting | winter_warm_midlayer | medium | 0.414 | 0.024 |
| weighted_voting | outdoor_dwr_windbreaker | easy | 0.454 | 0.022 |
| weighted_voting | outdoor_dwr_windbreaker | hard | 0.396 | 0.034 |
| weighted_voting | outdoor_dwr_windbreaker | medium | 0.409 | 0.068 |
| weighted_voting | winter_warm_midlayer | easy | 0.503 | 0.022 |
| weighted_voting | winter_warm_midlayer | hard | 0.349 | 0.023 |
| weighted_voting | winter_warm_midlayer | medium | 0.381 | 0.013 |
| zero_shot | outdoor_dwr_windbreaker | easy | 0.684 | 0.033 |
| zero_shot | outdoor_dwr_windbreaker | hard | 0.555 | 0.062 |
| zero_shot | outdoor_dwr_windbreaker | medium | 0.577 | 0.012 |
| zero_shot | winter_warm_midlayer | easy | 0.608 | 0.052 |
| zero_shot | winter_warm_midlayer | hard | 0.508 | 0.048 |
| zero_shot | winter_warm_midlayer | medium | 0.516 | 0.022 |

### Table A2 按难度分组的准确率（每个 repeat/run）

- **来源**: `outputs/figs_main/paper_acc_by_difficulty_per_run.csv`  
- **行数**: 217  
- **列数**: 8

<details>
<summary>展开表格（217 行）</summary>

| strategy | scenario | temperature | repeat_idx | seed | difficulty | n | acc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| borda | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.417 |
| borda | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.341 |
| borda | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.401 |
| borda | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.387 |
| borda | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.376 |
| borda | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.413 |
| borda | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.485 |
| borda | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.359 |
| borda | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.383 |
| borda | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.497 |
| borda | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.402 |
| borda | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.410 |
| borda | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.455 |
| borda | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.385 |
| borda | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.416 |
| borda | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.509 |
| borda | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.362 |
| borda | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.311 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.755 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.547 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.617 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.724 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.029 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.563 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 161 | 0.702 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.606 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.581 |
| cot_few_shot | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.855 |
| cot_few_shot | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.546 |
| cot_few_shot | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.733 |
| cot_few_shot | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.830 |
| cot_few_shot | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.638 |
| cot_few_shot | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.683 |
| cot_few_shot | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.848 |
| cot_few_shot | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.586 |
| cot_few_shot | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.745 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.847 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.653 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.695 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.822 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.665 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.677 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.853 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.688 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.641 |
| fashionprompt | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.848 |
| fashionprompt | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.672 |
| fashionprompt | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.745 |
| fashionprompt | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.903 |
| fashionprompt | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.684 |
| fashionprompt | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.714 |
| fashionprompt | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.903 |
| fashionprompt | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.644 |
| fashionprompt | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.720 |
| few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.871 |
| few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.676 |
| few_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.725 |
| few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.847 |
| few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.676 |
| few_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.689 |
| few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.847 |
| few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.694 |
| few_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.725 |
| few_shot | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.927 |
| few_shot | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.724 |
| few_shot | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.801 |
| few_shot | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.933 |
| few_shot | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.730 |
| few_shot | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.770 |
| few_shot | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.927 |
| few_shot | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.678 |
| few_shot | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.826 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.411 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.324 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.395 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.442 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.424 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.425 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.479 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.329 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.431 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.436 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.356 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.342 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.436 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.305 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.292 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.406 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.345 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.404 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.454 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.382 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.377 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.448 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.394 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.389 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.399 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.318 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.353 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.527 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.351 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.398 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.467 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.351 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.360 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.479 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.351 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.366 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.356 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.400 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.287 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.368 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.412 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.353 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.399 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.324 |
| nonllm_feasible_random | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.389 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.364 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.402 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.273 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.364 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.408 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.360 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.400 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.322 |
| nonllm_feasible_random | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.391 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.607 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.506 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.503 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.607 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.506 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.503 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.607 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.506 |
| nonllm_simple_heuristic | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.503 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.752 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.517 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.540 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.752 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.517 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.540 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.752 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.517 |
| nonllm_simple_heuristic | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.540 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.822 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.635 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.647 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.877 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.653 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.581 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.834 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.600 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.671 |
| self_reflection | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.933 |
| self_reflection | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.718 |
| self_reflection | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.764 |
| self_reflection | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.879 |
| self_reflection | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.644 |
| self_reflection | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.733 |
| self_reflection | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.885 |
| self_reflection | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.661 |
| self_reflection | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.720 |
| voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.479 |
| voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.424 |
| voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.389 |
| voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.491 |
| voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.371 |
| voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.383 |
| voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.411 |
| voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.371 |
| voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.395 |
| voting | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.509 |
| voting | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.356 |
| voting | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.404 |
| voting | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.424 |
| voting | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.362 |
| voting | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.441 |
| voting | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.467 |
| voting | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.305 |
| voting | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.398 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 163 | 0.479 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.371 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.485 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.448 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.435 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.389 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.436 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.382 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.353 |
| weighted_voting | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.527 |
| weighted_voting | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.322 |
| weighted_voting | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.391 |
| weighted_voting | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.485 |
| weighted_voting | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.362 |
| weighted_voting | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.366 |
| weighted_voting | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.497 |
| weighted_voting | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.362 |
| weighted_voting | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.385 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 0 | easy | 107 | 0.673 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | easy | 56 | 0.732 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | hard | 170 | 0.618 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 0 | 1000 | medium | 167 | 0.581 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | easy | 163 | 0.675 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | hard | 170 | 0.494 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 1 | 1000 | medium | 167 | 0.587 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | easy | 163 | 0.656 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | hard | 170 | 0.553 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 2 | 1000 | medium | 167 | 0.563 |
| zero_shot | winter_warm_midlayer | 1 | 0 | 1000 | easy | 165 | 0.570 |
| zero_shot | winter_warm_midlayer | 1 | 0 | 1000 | hard | 174 | 0.483 |
| zero_shot | winter_warm_midlayer | 1 | 0 | 1000 | medium | 161 | 0.497 |
| zero_shot | winter_warm_midlayer | 1 | 1 | 1000 | easy | 165 | 0.588 |
| zero_shot | winter_warm_midlayer | 1 | 1 | 1000 | hard | 174 | 0.563 |
| zero_shot | winter_warm_midlayer | 1 | 1 | 1000 | medium | 161 | 0.540 |
| zero_shot | winter_warm_midlayer | 1 | 2 | 1000 | easy | 165 | 0.667 |
| zero_shot | winter_warm_midlayer | 1 | 2 | 1000 | hard | 174 | 0.477 |
| zero_shot | winter_warm_midlayer | 1 | 2 | 1000 | medium | 161 | 0.509 |

</details>


### Table 5 统计检验（Kruskal–Wallis / Mann–Whitney U + BH-FDR）

- **来源**: `outputs/figs_main/stats_tests.csv`  
- **行数**: 158  
- **列数**: 8

<details>
<summary>展开表格（158 行）</summary>

| scenario | temperature | n_questions | model | test | strategy | p | bh_reject@0.05 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | borda | 0.51 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | cot_few_shot | 0.0661 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | fashionprompt | 0.78 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | few_shot | 0.174 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | garmentagents_adaptive | 0.637 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | garmentagents_fixed | 0.194 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | nonllm_feasible_random | 0.497 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | nonllm_simple_heuristic | 1 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | self_reflection | 0 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | voting | 0.826 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | weighted_voting | 0.716 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | shapiro | zero_shot | 0.23 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | kruskal_wallis | ALL | 0.000739 |  |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs cot_few_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs fashionprompt | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs few_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs garmentagents_adaptive | 0.7 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs garmentagents_fixed | 1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs nonllm_feasible_random | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs nonllm_simple_heuristic | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs self_reflection | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs voting | 0.268 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs weighted_voting | 0.4 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs zero_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs fashionprompt | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs few_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs garmentagents_adaptive | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs garmentagents_fixed | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs nonllm_feasible_random | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs nonllm_simple_heuristic | 0.643 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs self_reflection | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs voting | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs weighted_voting | 0.2 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs zero_shot | 0.825 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs few_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs garmentagents_adaptive | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs garmentagents_fixed | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs nonllm_feasible_random | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs nonllm_simple_heuristic | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs self_reflection | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs voting | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs weighted_voting | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs zero_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs garmentagents_adaptive | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs garmentagents_fixed | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs nonllm_feasible_random | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs nonllm_simple_heuristic | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs self_reflection | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs voting | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs weighted_voting | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs zero_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs garmentagents_fixed | 0.4 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs nonllm_feasible_random | 0.2 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs nonllm_simple_heuristic | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs self_reflection | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs voting | 0.825 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs weighted_voting | 0.7 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs zero_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs nonllm_feasible_random | 0.4 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs nonllm_simple_heuristic | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs self_reflection | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs voting | 0.4 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs weighted_voting | 0.4 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs zero_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs nonllm_simple_heuristic | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs self_reflection | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs voting | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs weighted_voting | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs zero_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_simple_heuristic vs self_reflection | 0.0593 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_simple_heuristic vs voting | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_simple_heuristic vs weighted_voting | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_simple_heuristic vs zero_shot | 0.0636 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | self_reflection vs voting | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | self_reflection vs weighted_voting | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | self_reflection vs zero_shot | 0.0765 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | voting vs weighted_voting | 1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | voting vs zero_shot | 0.1 | False |
| outdoor_dwr_windbreaker | 1 | 500 | gpt-5-mini | mannwhitneyu | weighted_voting vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | borda | 0.843 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | cot_few_shot | 1 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | fashionprompt | 0 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | few_shot | 0.463 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | garmentagents_adaptive | 0.266 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | garmentagents_fixed | 0.339 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | nonllm_feasible_random | 0.497 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | nonllm_simple_heuristic | 1 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | self_reflection | 0.127 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | voting | 0.806 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | weighted_voting | 0.363 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | shapiro | zero_shot | 0.549 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | kruskal_wallis | ALL | 0.000441 |  |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs cot_few_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs fashionprompt | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs few_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs garmentagents_adaptive | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs garmentagents_fixed | 0.7 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs nonllm_feasible_random | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs nonllm_simple_heuristic | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs self_reflection | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs voting | 0.7 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs weighted_voting | 0.7 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | borda vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs fashionprompt | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs few_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs garmentagents_adaptive | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs garmentagents_fixed | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs nonllm_feasible_random | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs nonllm_simple_heuristic | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs self_reflection | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs weighted_voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | cot_few_shot vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs few_shot | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs garmentagents_adaptive | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs garmentagents_fixed | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs nonllm_feasible_random | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs nonllm_simple_heuristic | 0.0593 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs self_reflection | 1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs voting | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs weighted_voting | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | fashionprompt vs zero_shot | 0.0765 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs garmentagents_adaptive | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs garmentagents_fixed | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs nonllm_feasible_random | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs nonllm_simple_heuristic | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs self_reflection | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs weighted_voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | few_shot vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs garmentagents_fixed | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs nonllm_feasible_random | 0.825 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs nonllm_simple_heuristic | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs self_reflection | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs weighted_voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_adaptive vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs nonllm_feasible_random | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs nonllm_simple_heuristic | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs self_reflection | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs voting | 1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs weighted_voting | 0.7 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | garmentagents_fixed vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs nonllm_simple_heuristic | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs self_reflection | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs weighted_voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_feasible_random vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_simple_heuristic vs self_reflection | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_simple_heuristic vs voting | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_simple_heuristic vs weighted_voting | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | nonllm_simple_heuristic vs zero_shot | 0.0636 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | self_reflection vs voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | self_reflection vs weighted_voting | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | self_reflection vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | voting vs weighted_voting | 1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | voting vs zero_shot | 0.1 | False |
| winter_warm_midlayer | 1 | 500 | gpt-5-mini | mannwhitneyu | weighted_voting vs zero_shot | 0.1 | False |

</details>


## 数据集统计（Dataset）

### Table D1 数据集按场景摘要（margin / must 约束数量）

- **来源**: `outputs/figs_main/paper_dataset_summary_by_scenario.csv`  
- **行数**: 2  
- **列数**: 7

| scenario | n | margin_mean | margin_p10 | margin_p50 | margin_p90 | must_n_mean |
| --- | --- | --- | --- | --- | --- | --- |
| outdoor_dwr_windbreaker | 500 | 0.105 | 0.058 | 0.093 | 0.164 | 2.924 |
| winter_warm_midlayer | 500 | 0.101 | 0.062 | 0.093 | 0.151 | 2.886 |

### Table D2 各场景约束类型计数

- **来源**: `outputs/figs_main/paper_dataset_constraint_counts.csv`  
- **行数**: 10  
- **列数**: 3

| scenario | constraint | n_questions |
| --- | --- | --- |
| outdoor_dwr_windbreaker | cost | 118 |
| outdoor_dwr_windbreaker | lead | 149 |
| outdoor_dwr_windbreaker | compliance | 185 |
| outdoor_dwr_windbreaker | weight | 298 |
| outdoor_dwr_windbreaker | perf | 452 |
| winter_warm_midlayer | cost | 167 |
| winter_warm_midlayer | lead | 140 |
| winter_warm_midlayer | compliance | 170 |
| winter_warm_midlayer | weight | 167 |
| winter_warm_midlayer | perf | 436 |

### Table D3 答案分布（gold 选项分布）

- **来源**: `outputs/figs_main/paper_dataset_answer_dist.csv`  
- **行数**: 8  
- **列数**: 3

| scenario | gold | n |
| --- | --- | --- |
| outdoor_dwr_windbreaker | A | 120 |
| outdoor_dwr_windbreaker | B | 129 |
| outdoor_dwr_windbreaker | C | 121 |
| outdoor_dwr_windbreaker | D | 130 |
| winter_warm_midlayer | A | 115 |
| winter_warm_midlayer | B | 116 |
| winter_warm_midlayer | C | 139 |
| winter_warm_midlayer | D | 130 |

## 消融实验（Ablation）

### Ablation Study Results (Offline)

基于 `per_question_log_main.jsonl` 中已保存的 5-role agent 输出进行离线计算。

#### A1: No Early Stopping

| Variant | Scenario | Repeat | N | Accuracy | Avg Calls |
|---------|----------|--------|---|----------|-----------|
| adaptive_default | outdoor_dwr_windbreaker | 0 | 500 | 0.376 | 3.65 |
| adaptive_default | outdoor_dwr_windbreaker | 1 | 500 | 0.430 | 3.63 |
| adaptive_default | outdoor_dwr_windbreaker | 2 | 500 | 0.412 | 3.63 |
| adaptive_default | winter_warm_midlayer | 0 | 500 | 0.378 | 3.88 |
| adaptive_default | winter_warm_midlayer | 1 | 500 | 0.344 | 3.86 |
| adaptive_default | winter_warm_midlayer | 2 | 500 | 0.384 | 3.73 |
| adaptive_no_early_stop | outdoor_dwr_windbreaker | 0 | 500 | 0.376 | 5.00 |
| adaptive_no_early_stop | outdoor_dwr_windbreaker | 1 | 500 | 0.430 | 5.00 |
| adaptive_no_early_stop | outdoor_dwr_windbreaker | 2 | 500 | 0.412 | 5.00 |
| adaptive_no_early_stop | winter_warm_midlayer | 0 | 500 | 0.378 | 5.00 |
| adaptive_no_early_stop | winter_warm_midlayer | 1 | 500 | 0.344 | 5.00 |
| adaptive_no_early_stop | winter_warm_midlayer | 2 | 500 | 0.384 | 5.00 |

#### A2: Static vs Adaptive Routing (with Early Stop)

| Variant | Scenario | Repeat | N | Accuracy | Avg Calls |
|---------|----------|--------|---|----------|-----------|
| adaptive_routing_early_stop | outdoor_dwr_windbreaker | 0 | 500 | 0.376 | 3.65 |
| adaptive_routing_early_stop | outdoor_dwr_windbreaker | 1 | 500 | 0.430 | 3.63 |
| adaptive_routing_early_stop | outdoor_dwr_windbreaker | 2 | 500 | 0.412 | 3.63 |
| adaptive_routing_early_stop | winter_warm_midlayer | 0 | 500 | 0.378 | 3.88 |
| adaptive_routing_early_stop | winter_warm_midlayer | 1 | 500 | 0.344 | 3.86 |
| adaptive_routing_early_stop | winter_warm_midlayer | 2 | 500 | 0.384 | 3.73 |
| static_routing_early_stop | outdoor_dwr_windbreaker | 0 | 500 | 0.352 | 4.03 |
| static_routing_early_stop | outdoor_dwr_windbreaker | 1 | 500 | 0.402 | 4.08 |
| static_routing_early_stop | outdoor_dwr_windbreaker | 2 | 500 | 0.402 | 4.06 |
| static_routing_early_stop | winter_warm_midlayer | 0 | 500 | 0.364 | 4.13 |
| static_routing_early_stop | winter_warm_midlayer | 1 | 500 | 0.360 | 4.08 |
| static_routing_early_stop | winter_warm_midlayer | 2 | 500 | 0.370 | 4.04 |

#### A3: Threshold Sweep

| Scenario | Repeat | Top1 Thresh | Gap Thresh | Accuracy | Avg Calls |
|----------|--------|-------------|------------|----------|-----------|
| outdoor_dwr_windbreaker | 0 | 0.50 | 0.15 | 0.364 | 3.50 |
| outdoor_dwr_windbreaker | 0 | 0.60 | 0.20 | 0.376 | 3.65 |
| outdoor_dwr_windbreaker | 0 | 0.70 | 0.25 | 0.376 | 3.65 |
| outdoor_dwr_windbreaker | 0 | 0.80 | 0.30 | 0.376 | 3.75 |
| outdoor_dwr_windbreaker | 0 | 0.90 | 0.35 | 0.376 | 3.84 |
| outdoor_dwr_windbreaker | 0 | 1.00 | 1.00 | 0.376 | 4.16 |
| outdoor_dwr_windbreaker | 1 | 0.50 | 0.15 | 0.430 | 3.47 |
| outdoor_dwr_windbreaker | 1 | 0.60 | 0.20 | 0.430 | 3.63 |
| outdoor_dwr_windbreaker | 1 | 0.70 | 0.25 | 0.430 | 3.63 |
| outdoor_dwr_windbreaker | 1 | 0.80 | 0.30 | 0.430 | 3.72 |
| outdoor_dwr_windbreaker | 1 | 0.90 | 0.35 | 0.430 | 3.82 |
| outdoor_dwr_windbreaker | 1 | 1.00 | 1.00 | 0.430 | 4.08 |
| outdoor_dwr_windbreaker | 2 | 0.50 | 0.15 | 0.402 | 3.48 |
| outdoor_dwr_windbreaker | 2 | 0.60 | 0.20 | 0.412 | 3.63 |
| outdoor_dwr_windbreaker | 2 | 0.70 | 0.25 | 0.412 | 3.63 |
| outdoor_dwr_windbreaker | 2 | 0.80 | 0.30 | 0.412 | 3.72 |
| outdoor_dwr_windbreaker | 2 | 0.90 | 0.35 | 0.412 | 3.84 |
| outdoor_dwr_windbreaker | 2 | 1.00 | 1.00 | 0.412 | 4.07 |
| winter_warm_midlayer | 0 | 0.50 | 0.15 | 0.370 | 3.62 |
| winter_warm_midlayer | 0 | 0.60 | 0.20 | 0.378 | 3.88 |
| winter_warm_midlayer | 0 | 0.70 | 0.25 | 0.378 | 3.88 |
| winter_warm_midlayer | 0 | 0.80 | 0.30 | 0.378 | 4.14 |
| winter_warm_midlayer | 0 | 0.90 | 0.35 | 0.378 | 4.14 |
| winter_warm_midlayer | 0 | 1.00 | 1.00 | 0.378 | 4.25 |
| winter_warm_midlayer | 1 | 0.50 | 0.15 | 0.332 | 3.61 |
| winter_warm_midlayer | 1 | 0.60 | 0.20 | 0.344 | 3.86 |
| winter_warm_midlayer | 1 | 0.70 | 0.25 | 0.344 | 3.86 |
| winter_warm_midlayer | 1 | 0.80 | 0.30 | 0.344 | 4.06 |
| winter_warm_midlayer | 1 | 0.90 | 0.35 | 0.344 | 4.06 |
| winter_warm_midlayer | 1 | 1.00 | 1.00 | 0.344 | 4.18 |
| winter_warm_midlayer | 2 | 0.50 | 0.15 | 0.378 | 3.47 |
| winter_warm_midlayer | 2 | 0.60 | 0.20 | 0.384 | 3.73 |
| winter_warm_midlayer | 2 | 0.70 | 0.25 | 0.384 | 3.73 |
| winter_warm_midlayer | 2 | 0.80 | 0.30 | 0.384 | 3.96 |
| winter_warm_midlayer | 2 | 0.90 | 0.35 | 0.384 | 3.96 |
| winter_warm_midlayer | 2 | 1.00 | 1.00 | 0.384 | 4.06 |

#### B1: Aggregator Ablation

| Aggregator | Scenario | Repeat | Accuracy |
|------------|----------|--------|----------|
| borda | outdoor_dwr_windbreaker | 0 | 0.398 |
| borda | outdoor_dwr_windbreaker | 1 | 0.408 |
| borda | outdoor_dwr_windbreaker | 2 | 0.348 |
| borda | winter_warm_midlayer | 0 | 0.424 |
| borda | winter_warm_midlayer | 1 | 0.388 |
| borda | winter_warm_midlayer | 2 | 0.398 |
| confidence | outdoor_dwr_windbreaker | 0 | 0.448 |
| confidence | outdoor_dwr_windbreaker | 1 | 0.440 |
| confidence | outdoor_dwr_windbreaker | 2 | 0.396 |
| confidence | winter_warm_midlayer | 0 | 0.428 |
| confidence | winter_warm_midlayer | 1 | 0.386 |
| confidence | winter_warm_midlayer | 2 | 0.404 |
| majority | outdoor_dwr_windbreaker | 0 | 0.448 |
| majority | outdoor_dwr_windbreaker | 1 | 0.440 |
| majority | outdoor_dwr_windbreaker | 2 | 0.396 |
| majority | winter_warm_midlayer | 0 | 0.428 |
| majority | winter_warm_midlayer | 1 | 0.386 |
| majority | winter_warm_midlayer | 2 | 0.404 |
| weighted | outdoor_dwr_windbreaker | 0 | 0.404 |
| weighted | outdoor_dwr_windbreaker | 1 | 0.410 |
| weighted | outdoor_dwr_windbreaker | 2 | 0.356 |
| weighted | winter_warm_midlayer | 0 | 0.424 |
| weighted | winter_warm_midlayer | 1 | 0.392 |
| weighted | winter_warm_midlayer | 2 | 0.398 |

#### B2: #Agents Sweep

| K | Scenario | Repeat | Accuracy | Roles |
|---|----------|--------|----------|-------|
| 1 | outdoor_dwr_windbreaker | 0 | 0.204 | textile |
| 1 | outdoor_dwr_windbreaker | 1 | 0.204 | textile |
| 1 | outdoor_dwr_windbreaker | 2 | 0.162 | textile |
| 1 | winter_warm_midlayer | 0 | 0.204 | textile |
| 1 | winter_warm_midlayer | 1 | 0.232 | textile |
| 1 | winter_warm_midlayer | 2 | 0.190 | textile |
| 2 | outdoor_dwr_windbreaker | 0 | 0.326 | textile,compliance |
| 2 | outdoor_dwr_windbreaker | 1 | 0.278 | textile,compliance |
| 2 | outdoor_dwr_windbreaker | 2 | 0.246 | textile,compliance |
| 2 | winter_warm_midlayer | 0 | 0.316 | textile,technical |
| 2 | winter_warm_midlayer | 1 | 0.318 | textile,technical |
| 2 | winter_warm_midlayer | 2 | 0.300 | textile,technical |
| 3 | outdoor_dwr_windbreaker | 0 | 0.376 | textile,compliance,technical |
| 3 | outdoor_dwr_windbreaker | 1 | 0.386 | textile,compliance,technical |
| 3 | outdoor_dwr_windbreaker | 2 | 0.300 | textile,compliance,technical |
| 3 | winter_warm_midlayer | 0 | 0.376 | textile,technical,product |
| 3 | winter_warm_midlayer | 1 | 0.364 | textile,technical,product |
| 3 | winter_warm_midlayer | 2 | 0.352 | textile,technical,product |
| 4 | outdoor_dwr_windbreaker | 0 | 0.414 | textile,compliance,technical,product |
| 4 | outdoor_dwr_windbreaker | 1 | 0.408 | textile,compliance,technical,product |
| 4 | outdoor_dwr_windbreaker | 2 | 0.360 | textile,compliance,technical,product |
| 4 | winter_warm_midlayer | 0 | 0.402 | textile,technical,product,sourcing |
| 4 | winter_warm_midlayer | 1 | 0.370 | textile,technical,product,sourcing |
| 4 | winter_warm_midlayer | 2 | 0.378 | textile,technical,product,sourcing |
| 5 | outdoor_dwr_windbreaker | 0 | 0.448 | textile,compliance,technical,product,sourcing |
| 5 | outdoor_dwr_windbreaker | 1 | 0.440 | textile,compliance,technical,product,sourcing |
| 5 | outdoor_dwr_windbreaker | 2 | 0.396 | textile,compliance,technical,product,sourcing |
| 5 | winter_warm_midlayer | 0 | 0.428 | textile,technical,product,sourcing,compliance |
| 5 | winter_warm_midlayer | 1 | 0.386 | textile,technical,product,sourcing,compliance |
| 5 | winter_warm_midlayer | 2 | 0.404 | textile,technical,product,sourcing,compliance |

#### C1: Role Dropout

| Dropped Role | Scenario | Repeat | Accuracy |
|--------------|----------|--------|----------|
| compliance | outdoor_dwr_windbreaker | 0 | 0.364 |
| compliance | outdoor_dwr_windbreaker | 1 | 0.386 |
| compliance | outdoor_dwr_windbreaker | 2 | 0.338 |
| compliance | winter_warm_midlayer | 0 | 0.396 |
| compliance | winter_warm_midlayer | 1 | 0.378 |
| compliance | winter_warm_midlayer | 2 | 0.382 |
| none | outdoor_dwr_windbreaker | 0 | 0.404 |
| none | outdoor_dwr_windbreaker | 1 | 0.410 |
| none | outdoor_dwr_windbreaker | 2 | 0.356 |
| none | winter_warm_midlayer | 0 | 0.424 |
| none | winter_warm_midlayer | 1 | 0.392 |
| none | winter_warm_midlayer | 2 | 0.398 |
| product | outdoor_dwr_windbreaker | 0 | 0.370 |
| product | outdoor_dwr_windbreaker | 1 | 0.382 |
| product | outdoor_dwr_windbreaker | 2 | 0.310 |
| product | winter_warm_midlayer | 0 | 0.382 |
| product | winter_warm_midlayer | 1 | 0.376 |
| product | winter_warm_midlayer | 2 | 0.358 |
| sourcing | outdoor_dwr_windbreaker | 0 | 0.374 |
| sourcing | outdoor_dwr_windbreaker | 1 | 0.370 |
| sourcing | outdoor_dwr_windbreaker | 2 | 0.332 |
| sourcing | winter_warm_midlayer | 0 | 0.390 |
| sourcing | winter_warm_midlayer | 1 | 0.370 |
| sourcing | winter_warm_midlayer | 2 | 0.380 |
| technical | outdoor_dwr_windbreaker | 0 | 0.386 |
| technical | outdoor_dwr_windbreaker | 1 | 0.380 |
| technical | outdoor_dwr_windbreaker | 2 | 0.326 |
| technical | winter_warm_midlayer | 0 | 0.364 |
| technical | winter_warm_midlayer | 1 | 0.362 |
| technical | winter_warm_midlayer | 2 | 0.348 |
| textile | outdoor_dwr_windbreaker | 0 | 0.422 |
| textile | outdoor_dwr_windbreaker | 1 | 0.402 |
| textile | outdoor_dwr_windbreaker | 2 | 0.374 |
| textile | winter_warm_midlayer | 0 | 0.384 |
| textile | winter_warm_midlayer | 1 | 0.336 |
| textile | winter_warm_midlayer | 2 | 0.352 |

#### D1: Clean vs Ambiguous (by margin < 0.08)

| Strategy | Scenario | Repeat | Subset | N | Accuracy |
|----------|----------|--------|--------|---|----------|
| borda | outdoor_dwr_windbreaker | 0 | ambiguous | 175 | 0.394 |
| borda | outdoor_dwr_windbreaker | 0 | clean | 275 | 0.451 |
| borda | outdoor_dwr_windbreaker | 1 | ambiguous | 179 | 0.419 |
| borda | outdoor_dwr_windbreaker | 1 | clean | 278 | 0.435 |
| borda | outdoor_dwr_windbreaker | 2 | ambiguous | 175 | 0.394 |
| borda | outdoor_dwr_windbreaker | 2 | clean | 279 | 0.484 |
| borda | winter_warm_midlayer | 0 | ambiguous | 144 | 0.465 |
| borda | winter_warm_midlayer | 0 | clean | 289 | 0.522 |
| borda | winter_warm_midlayer | 1 | ambiguous | 127 | 0.488 |
| borda | winter_warm_midlayer | 1 | clean | 289 | 0.509 |
| borda | winter_warm_midlayer | 2 | ambiguous | 141 | 0.433 |
| borda | winter_warm_midlayer | 2 | clean | 284 | 0.479 |
| cot_few_shot | outdoor_dwr_windbreaker | 0 | ambiguous | 193 | 0.565 |
| cot_few_shot | outdoor_dwr_windbreaker | 0 | clean | 306 | 0.686 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | ambiguous | 33 | 0.576 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | clean | 307 | 0.645 |
| cot_few_shot | outdoor_dwr_windbreaker | 2 | ambiguous | 193 | 0.611 |
| cot_few_shot | outdoor_dwr_windbreaker | 2 | clean | 305 | 0.639 |
| cot_few_shot | winter_warm_midlayer | 0 | ambiguous | 165 | 0.533 |
| cot_few_shot | winter_warm_midlayer | 0 | clean | 335 | 0.794 |
| cot_few_shot | winter_warm_midlayer | 1 | ambiguous | 165 | 0.636 |
| cot_few_shot | winter_warm_midlayer | 1 | clean | 334 | 0.757 |
| cot_few_shot | winter_warm_midlayer | 2 | ambiguous | 165 | 0.588 |
| cot_few_shot | winter_warm_midlayer | 2 | clean | 335 | 0.791 |
| fashionprompt | outdoor_dwr_windbreaker | 0 | ambiguous | 193 | 0.668 |
| fashionprompt | outdoor_dwr_windbreaker | 0 | clean | 307 | 0.769 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | ambiguous | 192 | 0.672 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | clean | 296 | 0.780 |
| fashionprompt | outdoor_dwr_windbreaker | 2 | ambiguous | 193 | 0.689 |
| fashionprompt | outdoor_dwr_windbreaker | 2 | clean | 307 | 0.749 |
| fashionprompt | winter_warm_midlayer | 0 | ambiguous | 165 | 0.661 |
| fashionprompt | winter_warm_midlayer | 0 | clean | 335 | 0.800 |
| fashionprompt | winter_warm_midlayer | 1 | ambiguous | 165 | 0.673 |
| fashionprompt | winter_warm_midlayer | 1 | clean | 335 | 0.812 |
| fashionprompt | winter_warm_midlayer | 2 | ambiguous | 165 | 0.642 |
| fashionprompt | winter_warm_midlayer | 2 | clean | 335 | 0.809 |
| few_shot | outdoor_dwr_windbreaker | 0 | ambiguous | 193 | 0.694 |
| few_shot | outdoor_dwr_windbreaker | 0 | clean | 306 | 0.797 |
| few_shot | outdoor_dwr_windbreaker | 1 | ambiguous | 193 | 0.679 |
| few_shot | outdoor_dwr_windbreaker | 1 | clean | 307 | 0.772 |
| few_shot | outdoor_dwr_windbreaker | 2 | ambiguous | 193 | 0.699 |
| few_shot | outdoor_dwr_windbreaker | 2 | clean | 307 | 0.788 |
| few_shot | winter_warm_midlayer | 0 | ambiguous | 164 | 0.720 |
| few_shot | winter_warm_midlayer | 0 | clean | 334 | 0.868 |
| few_shot | winter_warm_midlayer | 1 | ambiguous | 162 | 0.735 |
| few_shot | winter_warm_midlayer | 1 | clean | 332 | 0.861 |
| few_shot | winter_warm_midlayer | 2 | ambiguous | 163 | 0.675 |
| few_shot | winter_warm_midlayer | 2 | clean | 335 | 0.878 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 0 | ambiguous | 164 | 0.396 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 0 | clean | 278 | 0.442 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | ambiguous | 172 | 0.477 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | clean | 264 | 0.504 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 2 | ambiguous | 166 | 0.404 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 2 | clean | 261 | 0.533 |
| garmentagents_adaptive | winter_warm_midlayer | 0 | ambiguous | 127 | 0.465 |
| garmentagents_adaptive | winter_warm_midlayer | 0 | clean | 270 | 0.481 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | ambiguous | 132 | 0.394 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | clean | 273 | 0.440 |
| garmentagents_adaptive | winter_warm_midlayer | 2 | ambiguous | 137 | 0.401 |
| garmentagents_adaptive | winter_warm_midlayer | 2 | clean | 290 | 0.472 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 0 | ambiguous | 176 | 0.438 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 0 | clean | 277 | 0.451 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | ambiguous | 170 | 0.447 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | clean | 275 | 0.469 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 2 | ambiguous | 171 | 0.380 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 2 | clean | 267 | 0.423 |
| garmentagents_fixed | winter_warm_midlayer | 0 | ambiguous | 135 | 0.437 |
| garmentagents_fixed | winter_warm_midlayer | 0 | clean | 286 | 0.535 |
| garmentagents_fixed | winter_warm_midlayer | 1 | ambiguous | 132 | 0.439 |
| garmentagents_fixed | winter_warm_midlayer | 1 | clean | 282 | 0.489 |
| garmentagents_fixed | winter_warm_midlayer | 2 | ambiguous | 131 | 0.435 |
| garmentagents_fixed | winter_warm_midlayer | 2 | clean | 275 | 0.516 |
| self_reflection | outdoor_dwr_windbreaker | 0 | ambiguous | 193 | 0.648 |
| self_reflection | outdoor_dwr_windbreaker | 0 | clean | 307 | 0.733 |
| self_reflection | outdoor_dwr_windbreaker | 1 | ambiguous | 193 | 0.668 |
| self_reflection | outdoor_dwr_windbreaker | 1 | clean | 283 | 0.784 |
| self_reflection | outdoor_dwr_windbreaker | 2 | ambiguous | 193 | 0.627 |
| self_reflection | outdoor_dwr_windbreaker | 2 | clean | 307 | 0.746 |
| self_reflection | winter_warm_midlayer | 0 | ambiguous | 165 | 0.727 |
| self_reflection | winter_warm_midlayer | 0 | clean | 333 | 0.847 |
| self_reflection | winter_warm_midlayer | 1 | ambiguous | 164 | 0.659 |
| self_reflection | winter_warm_midlayer | 1 | clean | 335 | 0.797 |
| self_reflection | winter_warm_midlayer | 2 | ambiguous | 165 | 0.673 |
| self_reflection | winter_warm_midlayer | 2 | clean | 333 | 0.799 |
| voting | outdoor_dwr_windbreaker | 0 | ambiguous | 177 | 0.463 |
| voting | outdoor_dwr_windbreaker | 0 | clean | 268 | 0.496 |
| voting | outdoor_dwr_windbreaker | 1 | ambiguous | 178 | 0.393 |
| voting | outdoor_dwr_windbreaker | 1 | clean | 275 | 0.498 |
| voting | outdoor_dwr_windbreaker | 2 | ambiguous | 177 | 0.401 |
| voting | outdoor_dwr_windbreaker | 2 | clean | 271 | 0.461 |
| voting | winter_warm_midlayer | 0 | ambiguous | 130 | 0.454 |
| voting | winter_warm_midlayer | 0 | clean | 293 | 0.519 |
| voting | winter_warm_midlayer | 1 | ambiguous | 132 | 0.432 |
| voting | winter_warm_midlayer | 1 | clean | 292 | 0.503 |
| voting | winter_warm_midlayer | 2 | ambiguous | 133 | 0.383 |
| voting | winter_warm_midlayer | 2 | clean | 283 | 0.505 |
| weighted_voting | outdoor_dwr_windbreaker | 0 | ambiguous | 175 | 0.446 |
| weighted_voting | outdoor_dwr_windbreaker | 0 | clean | 269 | 0.535 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | ambiguous | 177 | 0.480 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | clean | 269 | 0.472 |
| weighted_voting | outdoor_dwr_windbreaker | 2 | ambiguous | 175 | 0.423 |
| weighted_voting | outdoor_dwr_windbreaker | 2 | clean | 272 | 0.445 |
| weighted_voting | winter_warm_midlayer | 0 | ambiguous | 134 | 0.396 |
| weighted_voting | winter_warm_midlayer | 0 | clean | 283 | 0.541 |
| weighted_voting | winter_warm_midlayer | 1 | ambiguous | 135 | 0.444 |
| weighted_voting | winter_warm_midlayer | 1 | clean | 291 | 0.488 |
| weighted_voting | winter_warm_midlayer | 2 | ambiguous | 137 | 0.423 |
| weighted_voting | winter_warm_midlayer | 2 | clean | 286 | 0.521 |
| zero_shot | outdoor_dwr_windbreaker | 0 | ambiguous | 187 | 0.631 |
| zero_shot | outdoor_dwr_windbreaker | 0 | clean | 296 | 0.666 |
| zero_shot | outdoor_dwr_windbreaker | 1 | ambiguous | 179 | 0.553 |
| zero_shot | outdoor_dwr_windbreaker | 1 | clean | 296 | 0.652 |
| zero_shot | outdoor_dwr_windbreaker | 2 | ambiguous | 182 | 0.593 |
| zero_shot | outdoor_dwr_windbreaker | 2 | clean | 297 | 0.630 |
| zero_shot | winter_warm_midlayer | 0 | ambiguous | 138 | 0.572 |
| zero_shot | winter_warm_midlayer | 0 | clean | 287 | 0.624 |
| zero_shot | winter_warm_midlayer | 1 | ambiguous | 146 | 0.644 |
| zero_shot | winter_warm_midlayer | 1 | clean | 289 | 0.651 |
| zero_shot | winter_warm_midlayer | 2 | ambiguous | 139 | 0.554 |
| zero_shot | winter_warm_midlayer | 2 | clean | 291 | 0.680 |

#### Constraint Violation Rate (must_fail chosen)

| Strategy | Scenario | Repeat | N | Violations | Rate |
|----------|----------|--------|---|------------|------|
| borda | outdoor_dwr_windbreaker | 0 | 450 | 116 | 0.258 |
| borda | outdoor_dwr_windbreaker | 1 | 457 | 123 | 0.269 |
| borda | outdoor_dwr_windbreaker | 2 | 454 | 105 | 0.231 |
| borda | winter_warm_midlayer | 0 | 433 | 78 | 0.180 |
| borda | winter_warm_midlayer | 1 | 416 | 87 | 0.209 |
| borda | winter_warm_midlayer | 2 | 425 | 94 | 0.221 |
| cot_few_shot | outdoor_dwr_windbreaker | 0 | 499 | 16 | 0.032 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 340 | 11 | 0.032 |
| cot_few_shot | outdoor_dwr_windbreaker | 2 | 498 | 23 | 0.046 |
| cot_few_shot | winter_warm_midlayer | 0 | 500 | 14 | 0.028 |
| cot_few_shot | winter_warm_midlayer | 1 | 499 | 16 | 0.032 |
| cot_few_shot | winter_warm_midlayer | 2 | 500 | 17 | 0.034 |
| fashionprompt | outdoor_dwr_windbreaker | 0 | 500 | 0 | 0.000 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 488 | 0 | 0.000 |
| fashionprompt | outdoor_dwr_windbreaker | 2 | 500 | 0 | 0.000 |
| fashionprompt | winter_warm_midlayer | 0 | 500 | 0 | 0.000 |
| fashionprompt | winter_warm_midlayer | 1 | 500 | 0 | 0.000 |
| fashionprompt | winter_warm_midlayer | 2 | 500 | 0 | 0.000 |
| few_shot | outdoor_dwr_windbreaker | 0 | 499 | 0 | 0.000 |
| few_shot | outdoor_dwr_windbreaker | 1 | 500 | 0 | 0.000 |
| few_shot | outdoor_dwr_windbreaker | 2 | 500 | 0 | 0.000 |
| few_shot | winter_warm_midlayer | 0 | 498 | 0 | 0.000 |
| few_shot | winter_warm_midlayer | 1 | 494 | 1 | 0.002 |
| few_shot | winter_warm_midlayer | 2 | 498 | 0 | 0.000 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 0 | 442 | 106 | 0.240 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 436 | 87 | 0.200 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 2 | 427 | 83 | 0.194 |
| garmentagents_adaptive | winter_warm_midlayer | 0 | 397 | 85 | 0.214 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 405 | 107 | 0.264 |
| garmentagents_adaptive | winter_warm_midlayer | 2 | 427 | 108 | 0.253 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 0 | 453 | 112 | 0.247 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 445 | 94 | 0.211 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 2 | 438 | 116 | 0.265 |
| garmentagents_fixed | winter_warm_midlayer | 0 | 421 | 90 | 0.214 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 414 | 97 | 0.234 |
| garmentagents_fixed | winter_warm_midlayer | 2 | 406 | 87 | 0.214 |
| self_reflection | outdoor_dwr_windbreaker | 0 | 500 | 1 | 0.002 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 476 | 0 | 0.000 |
| self_reflection | outdoor_dwr_windbreaker | 2 | 500 | 0 | 0.000 |
| self_reflection | winter_warm_midlayer | 0 | 498 | 0 | 0.000 |
| self_reflection | winter_warm_midlayer | 1 | 499 | 0 | 0.000 |
| self_reflection | winter_warm_midlayer | 2 | 498 | 2 | 0.004 |
| voting | outdoor_dwr_windbreaker | 0 | 445 | 119 | 0.267 |
| voting | outdoor_dwr_windbreaker | 1 | 453 | 114 | 0.252 |
| voting | outdoor_dwr_windbreaker | 2 | 448 | 113 | 0.252 |
| voting | winter_warm_midlayer | 0 | 423 | 101 | 0.239 |
| voting | winter_warm_midlayer | 1 | 424 | 99 | 0.233 |
| voting | winter_warm_midlayer | 2 | 416 | 100 | 0.240 |
| weighted_voting | outdoor_dwr_windbreaker | 0 | 444 | 100 | 0.225 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 446 | 119 | 0.267 |
| weighted_voting | outdoor_dwr_windbreaker | 2 | 447 | 124 | 0.277 |
| weighted_voting | winter_warm_midlayer | 0 | 417 | 102 | 0.245 |
| weighted_voting | winter_warm_midlayer | 1 | 426 | 99 | 0.232 |
| weighted_voting | winter_warm_midlayer | 2 | 423 | 83 | 0.196 |
| zero_shot | outdoor_dwr_windbreaker | 0 | 483 | 13 | 0.027 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 475 | 16 | 0.034 |
| zero_shot | outdoor_dwr_windbreaker | 2 | 479 | 18 | 0.038 |
| zero_shot | winter_warm_midlayer | 0 | 425 | 30 | 0.071 |
| zero_shot | winter_warm_midlayer | 1 | 435 | 31 | 0.071 |
| zero_shot | winter_warm_midlayer | 2 | 430 | 19 | 0.044 |


- **来源**: `outputs/figs_ablation/ablation_report.md`


## 附录：消融 CSV 明细（可复核）

### ablation_a1_no_early_stop.csv

- **来源**: `outputs/figs_ablation/ablation_a1_no_early_stop.csv`  
- **行数**: 12  
- **列数**: 7

| variant | scenario | repeat_idx | n | correct | accuracy | avg_calls |
| --- | --- | --- | --- | --- | --- | --- |
| adaptive_no_early_stop | outdoor_dwr_windbreaker | 0 | 500 | 188 | 0.376 | 5.00 |
| adaptive_no_early_stop | outdoor_dwr_windbreaker | 1 | 500 | 215 | 0.430 | 5.00 |
| adaptive_no_early_stop | outdoor_dwr_windbreaker | 2 | 500 | 206 | 0.412 | 5.00 |
| adaptive_no_early_stop | winter_warm_midlayer | 0 | 500 | 189 | 0.378 | 5.00 |
| adaptive_no_early_stop | winter_warm_midlayer | 1 | 500 | 172 | 0.344 | 5.00 |
| adaptive_no_early_stop | winter_warm_midlayer | 2 | 500 | 192 | 0.384 | 5.00 |
| adaptive_default | outdoor_dwr_windbreaker | 0 | 500 | 188 | 0.376 | 3.65 |
| adaptive_default | outdoor_dwr_windbreaker | 1 | 500 | 215 | 0.430 | 3.63 |
| adaptive_default | outdoor_dwr_windbreaker | 2 | 500 | 206 | 0.412 | 3.63 |
| adaptive_default | winter_warm_midlayer | 0 | 500 | 189 | 0.378 | 3.88 |
| adaptive_default | winter_warm_midlayer | 1 | 500 | 172 | 0.344 | 3.86 |
| adaptive_default | winter_warm_midlayer | 2 | 500 | 192 | 0.384 | 3.73 |

### ablation_a2_static_routing.csv

- **来源**: `outputs/figs_ablation/ablation_a2_static_routing.csv`  
- **行数**: 12  
- **列数**: 6

| variant | scenario | repeat_idx | n | accuracy | avg_calls |
| --- | --- | --- | --- | --- | --- |
| static_routing_early_stop | outdoor_dwr_windbreaker | 0 | 500 | 0.352 | 4.03 |
| adaptive_routing_early_stop | outdoor_dwr_windbreaker | 0 | 500 | 0.376 | 3.65 |
| static_routing_early_stop | outdoor_dwr_windbreaker | 1 | 500 | 0.402 | 4.08 |
| adaptive_routing_early_stop | outdoor_dwr_windbreaker | 1 | 500 | 0.430 | 3.63 |
| static_routing_early_stop | outdoor_dwr_windbreaker | 2 | 500 | 0.402 | 4.06 |
| adaptive_routing_early_stop | outdoor_dwr_windbreaker | 2 | 500 | 0.412 | 3.63 |
| static_routing_early_stop | winter_warm_midlayer | 0 | 500 | 0.364 | 4.13 |
| adaptive_routing_early_stop | winter_warm_midlayer | 0 | 500 | 0.378 | 3.88 |
| static_routing_early_stop | winter_warm_midlayer | 1 | 500 | 0.360 | 4.08 |
| adaptive_routing_early_stop | winter_warm_midlayer | 1 | 500 | 0.344 | 3.86 |
| static_routing_early_stop | winter_warm_midlayer | 2 | 500 | 0.370 | 4.04 |
| adaptive_routing_early_stop | winter_warm_midlayer | 2 | 500 | 0.384 | 3.73 |

### ablation_a3_threshold_sweep.csv

- **来源**: `outputs/figs_ablation/ablation_a3_threshold_sweep.csv`  
- **行数**: 36  
- **列数**: 7

| scenario | repeat_idx | top1_thresh | gap_thresh | n | accuracy | avg_calls |
| --- | --- | --- | --- | --- | --- | --- |
| outdoor_dwr_windbreaker | 0 | 0.50 | 0.15 | 500 | 0.364 | 3.50 |
| outdoor_dwr_windbreaker | 0 | 0.60 | 0.20 | 500 | 0.376 | 3.65 |
| outdoor_dwr_windbreaker | 0 | 0.70 | 0.25 | 500 | 0.376 | 3.65 |
| outdoor_dwr_windbreaker | 0 | 0.80 | 0.30 | 500 | 0.376 | 3.75 |
| outdoor_dwr_windbreaker | 0 | 0.90 | 0.35 | 500 | 0.376 | 3.84 |
| outdoor_dwr_windbreaker | 0 | 1.00 | 1.00 | 500 | 0.376 | 4.16 |
| outdoor_dwr_windbreaker | 1 | 0.50 | 0.15 | 500 | 0.430 | 3.47 |
| outdoor_dwr_windbreaker | 1 | 0.60 | 0.20 | 500 | 0.430 | 3.63 |
| outdoor_dwr_windbreaker | 1 | 0.70 | 0.25 | 500 | 0.430 | 3.63 |
| outdoor_dwr_windbreaker | 1 | 0.80 | 0.30 | 500 | 0.430 | 3.72 |
| outdoor_dwr_windbreaker | 1 | 0.90 | 0.35 | 500 | 0.430 | 3.82 |
| outdoor_dwr_windbreaker | 1 | 1.00 | 1.00 | 500 | 0.430 | 4.08 |
| outdoor_dwr_windbreaker | 2 | 0.50 | 0.15 | 500 | 0.402 | 3.48 |
| outdoor_dwr_windbreaker | 2 | 0.60 | 0.20 | 500 | 0.412 | 3.63 |
| outdoor_dwr_windbreaker | 2 | 0.70 | 0.25 | 500 | 0.412 | 3.63 |
| outdoor_dwr_windbreaker | 2 | 0.80 | 0.30 | 500 | 0.412 | 3.72 |
| outdoor_dwr_windbreaker | 2 | 0.90 | 0.35 | 500 | 0.412 | 3.84 |
| outdoor_dwr_windbreaker | 2 | 1.00 | 1.00 | 500 | 0.412 | 4.07 |
| winter_warm_midlayer | 0 | 0.50 | 0.15 | 500 | 0.370 | 3.62 |
| winter_warm_midlayer | 0 | 0.60 | 0.20 | 500 | 0.378 | 3.88 |
| winter_warm_midlayer | 0 | 0.70 | 0.25 | 500 | 0.378 | 3.88 |
| winter_warm_midlayer | 0 | 0.80 | 0.30 | 500 | 0.378 | 4.14 |
| winter_warm_midlayer | 0 | 0.90 | 0.35 | 500 | 0.378 | 4.14 |
| winter_warm_midlayer | 0 | 1.00 | 1.00 | 500 | 0.378 | 4.25 |
| winter_warm_midlayer | 1 | 0.50 | 0.15 | 500 | 0.332 | 3.61 |
| winter_warm_midlayer | 1 | 0.60 | 0.20 | 500 | 0.344 | 3.86 |
| winter_warm_midlayer | 1 | 0.70 | 0.25 | 500 | 0.344 | 3.86 |
| winter_warm_midlayer | 1 | 0.80 | 0.30 | 500 | 0.344 | 4.06 |
| winter_warm_midlayer | 1 | 0.90 | 0.35 | 500 | 0.344 | 4.06 |
| winter_warm_midlayer | 1 | 1.00 | 1.00 | 500 | 0.344 | 4.18 |
| winter_warm_midlayer | 2 | 0.50 | 0.15 | 500 | 0.378 | 3.47 |
| winter_warm_midlayer | 2 | 0.60 | 0.20 | 500 | 0.384 | 3.73 |
| winter_warm_midlayer | 2 | 0.70 | 0.25 | 500 | 0.384 | 3.73 |
| winter_warm_midlayer | 2 | 0.80 | 0.30 | 500 | 0.384 | 3.96 |
| winter_warm_midlayer | 2 | 0.90 | 0.35 | 500 | 0.384 | 3.96 |
| winter_warm_midlayer | 2 | 1.00 | 1.00 | 500 | 0.384 | 4.06 |

### ablation_b1_aggregator.csv

- **来源**: `outputs/figs_ablation/ablation_b1_aggregator.csv`  
- **行数**: 24  
- **列数**: 5

| aggregator | scenario | repeat_idx | n | accuracy |
| --- | --- | --- | --- | --- |
| majority | outdoor_dwr_windbreaker | 0 | 500 | 0.448 |
| weighted | outdoor_dwr_windbreaker | 0 | 500 | 0.404 |
| borda | outdoor_dwr_windbreaker | 0 | 500 | 0.398 |
| confidence | outdoor_dwr_windbreaker | 0 | 500 | 0.448 |
| majority | outdoor_dwr_windbreaker | 1 | 500 | 0.440 |
| weighted | outdoor_dwr_windbreaker | 1 | 500 | 0.410 |
| borda | outdoor_dwr_windbreaker | 1 | 500 | 0.408 |
| confidence | outdoor_dwr_windbreaker | 1 | 500 | 0.440 |
| majority | outdoor_dwr_windbreaker | 2 | 500 | 0.396 |
| weighted | outdoor_dwr_windbreaker | 2 | 500 | 0.356 |
| borda | outdoor_dwr_windbreaker | 2 | 500 | 0.348 |
| confidence | outdoor_dwr_windbreaker | 2 | 500 | 0.396 |
| majority | winter_warm_midlayer | 0 | 500 | 0.428 |
| weighted | winter_warm_midlayer | 0 | 500 | 0.424 |
| borda | winter_warm_midlayer | 0 | 500 | 0.424 |
| confidence | winter_warm_midlayer | 0 | 500 | 0.428 |
| majority | winter_warm_midlayer | 1 | 500 | 0.386 |
| weighted | winter_warm_midlayer | 1 | 500 | 0.392 |
| borda | winter_warm_midlayer | 1 | 500 | 0.388 |
| confidence | winter_warm_midlayer | 1 | 500 | 0.386 |
| majority | winter_warm_midlayer | 2 | 500 | 0.404 |
| weighted | winter_warm_midlayer | 2 | 500 | 0.398 |
| borda | winter_warm_midlayer | 2 | 500 | 0.398 |
| confidence | winter_warm_midlayer | 2 | 500 | 0.404 |

### ablation_b2_agents_sweep.csv

- **来源**: `outputs/figs_ablation/ablation_b2_agents_sweep.csv`  
- **行数**: 30  
- **列数**: 6

| k_agents | scenario | repeat_idx | n | accuracy | roles |
| --- | --- | --- | --- | --- | --- |
| 1 | outdoor_dwr_windbreaker | 0 | 500 | 0.204 | textile |
| 2 | outdoor_dwr_windbreaker | 0 | 500 | 0.326 | textile,compliance |
| 3 | outdoor_dwr_windbreaker | 0 | 500 | 0.376 | textile,compliance,technical |
| 4 | outdoor_dwr_windbreaker | 0 | 500 | 0.414 | textile,compliance,technical,product |
| 5 | outdoor_dwr_windbreaker | 0 | 500 | 0.448 | textile,compliance,technical,product,sourcing |
| 1 | outdoor_dwr_windbreaker | 1 | 500 | 0.204 | textile |
| 2 | outdoor_dwr_windbreaker | 1 | 500 | 0.278 | textile,compliance |
| 3 | outdoor_dwr_windbreaker | 1 | 500 | 0.386 | textile,compliance,technical |
| 4 | outdoor_dwr_windbreaker | 1 | 500 | 0.408 | textile,compliance,technical,product |
| 5 | outdoor_dwr_windbreaker | 1 | 500 | 0.440 | textile,compliance,technical,product,sourcing |
| 1 | outdoor_dwr_windbreaker | 2 | 500 | 0.162 | textile |
| 2 | outdoor_dwr_windbreaker | 2 | 500 | 0.246 | textile,compliance |
| 3 | outdoor_dwr_windbreaker | 2 | 500 | 0.300 | textile,compliance,technical |
| 4 | outdoor_dwr_windbreaker | 2 | 500 | 0.360 | textile,compliance,technical,product |
| 5 | outdoor_dwr_windbreaker | 2 | 500 | 0.396 | textile,compliance,technical,product,sourcing |
| 1 | winter_warm_midlayer | 0 | 500 | 0.204 | textile |
| 2 | winter_warm_midlayer | 0 | 500 | 0.316 | textile,technical |
| 3 | winter_warm_midlayer | 0 | 500 | 0.376 | textile,technical,product |
| 4 | winter_warm_midlayer | 0 | 500 | 0.402 | textile,technical,product,sourcing |
| 5 | winter_warm_midlayer | 0 | 500 | 0.428 | textile,technical,product,sourcing,compliance |
| 1 | winter_warm_midlayer | 1 | 500 | 0.232 | textile |
| 2 | winter_warm_midlayer | 1 | 500 | 0.318 | textile,technical |
| 3 | winter_warm_midlayer | 1 | 500 | 0.364 | textile,technical,product |
| 4 | winter_warm_midlayer | 1 | 500 | 0.370 | textile,technical,product,sourcing |
| 5 | winter_warm_midlayer | 1 | 500 | 0.386 | textile,technical,product,sourcing,compliance |
| 1 | winter_warm_midlayer | 2 | 500 | 0.190 | textile |
| 2 | winter_warm_midlayer | 2 | 500 | 0.300 | textile,technical |
| 3 | winter_warm_midlayer | 2 | 500 | 0.352 | textile,technical,product |
| 4 | winter_warm_midlayer | 2 | 500 | 0.378 | textile,technical,product,sourcing |
| 5 | winter_warm_midlayer | 2 | 500 | 0.404 | textile,technical,product,sourcing,compliance |

### ablation_c1_role_dropout.csv

- **来源**: `outputs/figs_ablation/ablation_c1_role_dropout.csv`  
- **行数**: 36  
- **列数**: 5

| dropped_role | scenario | repeat_idx | n | accuracy |
| --- | --- | --- | --- | --- |
| none | outdoor_dwr_windbreaker | 0 | 500 | 0.404 |
| textile | outdoor_dwr_windbreaker | 0 | 500 | 0.422 |
| technical | outdoor_dwr_windbreaker | 0 | 500 | 0.386 |
| sourcing | outdoor_dwr_windbreaker | 0 | 500 | 0.374 |
| product | outdoor_dwr_windbreaker | 0 | 500 | 0.370 |
| compliance | outdoor_dwr_windbreaker | 0 | 500 | 0.364 |
| none | outdoor_dwr_windbreaker | 1 | 500 | 0.410 |
| textile | outdoor_dwr_windbreaker | 1 | 500 | 0.402 |
| technical | outdoor_dwr_windbreaker | 1 | 500 | 0.380 |
| sourcing | outdoor_dwr_windbreaker | 1 | 500 | 0.370 |
| product | outdoor_dwr_windbreaker | 1 | 500 | 0.382 |
| compliance | outdoor_dwr_windbreaker | 1 | 500 | 0.386 |
| none | outdoor_dwr_windbreaker | 2 | 500 | 0.356 |
| textile | outdoor_dwr_windbreaker | 2 | 500 | 0.374 |
| technical | outdoor_dwr_windbreaker | 2 | 500 | 0.326 |
| sourcing | outdoor_dwr_windbreaker | 2 | 500 | 0.332 |
| product | outdoor_dwr_windbreaker | 2 | 500 | 0.310 |
| compliance | outdoor_dwr_windbreaker | 2 | 500 | 0.338 |
| none | winter_warm_midlayer | 0 | 500 | 0.424 |
| textile | winter_warm_midlayer | 0 | 500 | 0.384 |
| technical | winter_warm_midlayer | 0 | 500 | 0.364 |
| sourcing | winter_warm_midlayer | 0 | 500 | 0.390 |
| product | winter_warm_midlayer | 0 | 500 | 0.382 |
| compliance | winter_warm_midlayer | 0 | 500 | 0.396 |
| none | winter_warm_midlayer | 1 | 500 | 0.392 |
| textile | winter_warm_midlayer | 1 | 500 | 0.336 |
| technical | winter_warm_midlayer | 1 | 500 | 0.362 |
| sourcing | winter_warm_midlayer | 1 | 500 | 0.370 |
| product | winter_warm_midlayer | 1 | 500 | 0.376 |
| compliance | winter_warm_midlayer | 1 | 500 | 0.378 |
| none | winter_warm_midlayer | 2 | 500 | 0.398 |
| textile | winter_warm_midlayer | 2 | 500 | 0.352 |
| technical | winter_warm_midlayer | 2 | 500 | 0.348 |
| sourcing | winter_warm_midlayer | 2 | 500 | 0.380 |
| product | winter_warm_midlayer | 2 | 500 | 0.358 |
| compliance | winter_warm_midlayer | 2 | 500 | 0.382 |

### ablation_constraint_violation.csv

- **来源**: `outputs/figs_ablation/ablation_constraint_violation.csv`  
- **行数**: 60  
- **列数**: 6

| strategy | scenario | repeat_idx | n | must_violations | violation_rate |
| --- | --- | --- | --- | --- | --- |
| zero_shot | outdoor_dwr_windbreaker | 0 | 483 | 13 | 0.027 |
| zero_shot | outdoor_dwr_windbreaker | 1 | 475 | 16 | 0.034 |
| zero_shot | outdoor_dwr_windbreaker | 2 | 479 | 18 | 0.038 |
| few_shot | outdoor_dwr_windbreaker | 0 | 499 | 0 | 0 |
| few_shot | outdoor_dwr_windbreaker | 1 | 500 | 0 | 0 |
| few_shot | outdoor_dwr_windbreaker | 2 | 500 | 0 | 0 |
| cot_few_shot | outdoor_dwr_windbreaker | 0 | 499 | 16 | 0.032 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | 340 | 11 | 0.032 |
| cot_few_shot | outdoor_dwr_windbreaker | 2 | 498 | 23 | 0.046 |
| self_reflection | outdoor_dwr_windbreaker | 0 | 500 | 1 | 0.002 |
| self_reflection | outdoor_dwr_windbreaker | 1 | 476 | 0 | 0 |
| self_reflection | outdoor_dwr_windbreaker | 2 | 500 | 0 | 0 |
| fashionprompt | outdoor_dwr_windbreaker | 0 | 500 | 0 | 0 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | 488 | 0 | 0 |
| fashionprompt | outdoor_dwr_windbreaker | 2 | 500 | 0 | 0 |
| voting | outdoor_dwr_windbreaker | 0 | 445 | 119 | 0.267 |
| voting | outdoor_dwr_windbreaker | 1 | 453 | 114 | 0.252 |
| voting | outdoor_dwr_windbreaker | 2 | 448 | 113 | 0.252 |
| weighted_voting | outdoor_dwr_windbreaker | 0 | 444 | 100 | 0.225 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | 446 | 119 | 0.267 |
| weighted_voting | outdoor_dwr_windbreaker | 2 | 447 | 124 | 0.277 |
| borda | outdoor_dwr_windbreaker | 0 | 450 | 116 | 0.258 |
| borda | outdoor_dwr_windbreaker | 1 | 457 | 123 | 0.269 |
| borda | outdoor_dwr_windbreaker | 2 | 454 | 105 | 0.231 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 0 | 453 | 112 | 0.247 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | 445 | 94 | 0.211 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 2 | 438 | 116 | 0.265 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 0 | 442 | 106 | 0.240 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | 436 | 87 | 0.200 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 2 | 427 | 83 | 0.194 |
| zero_shot | winter_warm_midlayer | 0 | 425 | 30 | 0.071 |
| zero_shot | winter_warm_midlayer | 1 | 435 | 31 | 0.071 |
| zero_shot | winter_warm_midlayer | 2 | 430 | 19 | 0.044 |
| few_shot | winter_warm_midlayer | 0 | 498 | 0 | 0 |
| few_shot | winter_warm_midlayer | 1 | 494 | 1 | 0.002 |
| few_shot | winter_warm_midlayer | 2 | 498 | 0 | 0 |
| cot_few_shot | winter_warm_midlayer | 0 | 500 | 14 | 0.028 |
| cot_few_shot | winter_warm_midlayer | 1 | 499 | 16 | 0.032 |
| cot_few_shot | winter_warm_midlayer | 2 | 500 | 17 | 0.034 |
| self_reflection | winter_warm_midlayer | 0 | 498 | 0 | 0 |
| self_reflection | winter_warm_midlayer | 1 | 499 | 0 | 0 |
| self_reflection | winter_warm_midlayer | 2 | 498 | 2 | 0.004 |
| fashionprompt | winter_warm_midlayer | 0 | 500 | 0 | 0 |
| fashionprompt | winter_warm_midlayer | 1 | 500 | 0 | 0 |
| fashionprompt | winter_warm_midlayer | 2 | 500 | 0 | 0 |
| voting | winter_warm_midlayer | 0 | 423 | 101 | 0.239 |
| voting | winter_warm_midlayer | 1 | 424 | 99 | 0.233 |
| voting | winter_warm_midlayer | 2 | 416 | 100 | 0.240 |
| weighted_voting | winter_warm_midlayer | 0 | 417 | 102 | 0.245 |
| weighted_voting | winter_warm_midlayer | 1 | 426 | 99 | 0.232 |
| weighted_voting | winter_warm_midlayer | 2 | 423 | 83 | 0.196 |
| borda | winter_warm_midlayer | 0 | 433 | 78 | 0.180 |
| borda | winter_warm_midlayer | 1 | 416 | 87 | 0.209 |
| borda | winter_warm_midlayer | 2 | 425 | 94 | 0.221 |
| garmentagents_fixed | winter_warm_midlayer | 0 | 421 | 90 | 0.214 |
| garmentagents_fixed | winter_warm_midlayer | 1 | 414 | 97 | 0.234 |
| garmentagents_fixed | winter_warm_midlayer | 2 | 406 | 87 | 0.214 |
| garmentagents_adaptive | winter_warm_midlayer | 0 | 397 | 85 | 0.214 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | 405 | 107 | 0.264 |
| garmentagents_adaptive | winter_warm_midlayer | 2 | 427 | 108 | 0.253 |

### ablation_d1_clean_vs_ambiguous.csv

- **来源**: `outputs/figs_ablation/ablation_d1_clean_vs_ambiguous.csv`  
- **行数**: 120  
- **列数**: 7

<details>
<summary>展开表格（120 行）</summary>

| strategy | scenario | repeat_idx | subset | n | correct | accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| zero_shot | outdoor_dwr_windbreaker | 0 | clean | 296 | 197 | 0.666 |
| zero_shot | outdoor_dwr_windbreaker | 0 | ambiguous | 187 | 118 | 0.631 |
| zero_shot | outdoor_dwr_windbreaker | 1 | clean | 296 | 193 | 0.652 |
| zero_shot | outdoor_dwr_windbreaker | 1 | ambiguous | 179 | 99 | 0.553 |
| zero_shot | outdoor_dwr_windbreaker | 2 | clean | 297 | 187 | 0.630 |
| zero_shot | outdoor_dwr_windbreaker | 2 | ambiguous | 182 | 108 | 0.593 |
| few_shot | outdoor_dwr_windbreaker | 0 | clean | 306 | 244 | 0.797 |
| few_shot | outdoor_dwr_windbreaker | 0 | ambiguous | 193 | 134 | 0.694 |
| few_shot | outdoor_dwr_windbreaker | 1 | clean | 307 | 237 | 0.772 |
| few_shot | outdoor_dwr_windbreaker | 1 | ambiguous | 193 | 131 | 0.679 |
| few_shot | outdoor_dwr_windbreaker | 2 | clean | 307 | 242 | 0.788 |
| few_shot | outdoor_dwr_windbreaker | 2 | ambiguous | 193 | 135 | 0.699 |
| cot_few_shot | outdoor_dwr_windbreaker | 0 | clean | 306 | 210 | 0.686 |
| cot_few_shot | outdoor_dwr_windbreaker | 0 | ambiguous | 193 | 109 | 0.565 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | clean | 307 | 198 | 0.645 |
| cot_few_shot | outdoor_dwr_windbreaker | 1 | ambiguous | 33 | 19 | 0.576 |
| cot_few_shot | outdoor_dwr_windbreaker | 2 | clean | 305 | 195 | 0.639 |
| cot_few_shot | outdoor_dwr_windbreaker | 2 | ambiguous | 193 | 118 | 0.611 |
| self_reflection | outdoor_dwr_windbreaker | 0 | clean | 307 | 225 | 0.733 |
| self_reflection | outdoor_dwr_windbreaker | 0 | ambiguous | 193 | 125 | 0.648 |
| self_reflection | outdoor_dwr_windbreaker | 1 | clean | 283 | 222 | 0.784 |
| self_reflection | outdoor_dwr_windbreaker | 1 | ambiguous | 193 | 129 | 0.668 |
| self_reflection | outdoor_dwr_windbreaker | 2 | clean | 307 | 229 | 0.746 |
| self_reflection | outdoor_dwr_windbreaker | 2 | ambiguous | 193 | 121 | 0.627 |
| fashionprompt | outdoor_dwr_windbreaker | 0 | clean | 307 | 236 | 0.769 |
| fashionprompt | outdoor_dwr_windbreaker | 0 | ambiguous | 193 | 129 | 0.668 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | clean | 296 | 231 | 0.780 |
| fashionprompt | outdoor_dwr_windbreaker | 1 | ambiguous | 192 | 129 | 0.672 |
| fashionprompt | outdoor_dwr_windbreaker | 2 | clean | 307 | 230 | 0.749 |
| fashionprompt | outdoor_dwr_windbreaker | 2 | ambiguous | 193 | 133 | 0.689 |
| voting | outdoor_dwr_windbreaker | 0 | clean | 268 | 133 | 0.496 |
| voting | outdoor_dwr_windbreaker | 0 | ambiguous | 177 | 82 | 0.463 |
| voting | outdoor_dwr_windbreaker | 1 | clean | 275 | 137 | 0.498 |
| voting | outdoor_dwr_windbreaker | 1 | ambiguous | 178 | 70 | 0.393 |
| voting | outdoor_dwr_windbreaker | 2 | clean | 271 | 125 | 0.461 |
| voting | outdoor_dwr_windbreaker | 2 | ambiguous | 177 | 71 | 0.401 |
| weighted_voting | outdoor_dwr_windbreaker | 0 | clean | 269 | 144 | 0.535 |
| weighted_voting | outdoor_dwr_windbreaker | 0 | ambiguous | 175 | 78 | 0.446 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | clean | 269 | 127 | 0.472 |
| weighted_voting | outdoor_dwr_windbreaker | 1 | ambiguous | 177 | 85 | 0.480 |
| weighted_voting | outdoor_dwr_windbreaker | 2 | clean | 272 | 121 | 0.445 |
| weighted_voting | outdoor_dwr_windbreaker | 2 | ambiguous | 175 | 74 | 0.423 |
| borda | outdoor_dwr_windbreaker | 0 | clean | 275 | 124 | 0.451 |
| borda | outdoor_dwr_windbreaker | 0 | ambiguous | 175 | 69 | 0.394 |
| borda | outdoor_dwr_windbreaker | 1 | clean | 278 | 121 | 0.435 |
| borda | outdoor_dwr_windbreaker | 1 | ambiguous | 179 | 75 | 0.419 |
| borda | outdoor_dwr_windbreaker | 2 | clean | 279 | 135 | 0.484 |
| borda | outdoor_dwr_windbreaker | 2 | ambiguous | 175 | 69 | 0.394 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 0 | clean | 277 | 125 | 0.451 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 0 | ambiguous | 176 | 77 | 0.438 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | clean | 275 | 129 | 0.469 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 1 | ambiguous | 170 | 76 | 0.447 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 2 | clean | 267 | 113 | 0.423 |
| garmentagents_fixed | outdoor_dwr_windbreaker | 2 | ambiguous | 171 | 65 | 0.380 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 0 | clean | 278 | 123 | 0.442 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 0 | ambiguous | 164 | 65 | 0.396 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | clean | 264 | 133 | 0.504 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 1 | ambiguous | 172 | 82 | 0.477 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 2 | clean | 261 | 139 | 0.533 |
| garmentagents_adaptive | outdoor_dwr_windbreaker | 2 | ambiguous | 166 | 67 | 0.404 |
| zero_shot | winter_warm_midlayer | 0 | clean | 287 | 179 | 0.624 |
| zero_shot | winter_warm_midlayer | 0 | ambiguous | 138 | 79 | 0.572 |
| zero_shot | winter_warm_midlayer | 1 | clean | 289 | 188 | 0.651 |
| zero_shot | winter_warm_midlayer | 1 | ambiguous | 146 | 94 | 0.644 |
| zero_shot | winter_warm_midlayer | 2 | clean | 291 | 198 | 0.680 |
| zero_shot | winter_warm_midlayer | 2 | ambiguous | 139 | 77 | 0.554 |
| few_shot | winter_warm_midlayer | 0 | clean | 334 | 290 | 0.868 |
| few_shot | winter_warm_midlayer | 0 | ambiguous | 164 | 118 | 0.720 |
| few_shot | winter_warm_midlayer | 1 | clean | 332 | 286 | 0.861 |
| few_shot | winter_warm_midlayer | 1 | ambiguous | 162 | 119 | 0.735 |
| few_shot | winter_warm_midlayer | 2 | clean | 335 | 294 | 0.878 |
| few_shot | winter_warm_midlayer | 2 | ambiguous | 163 | 110 | 0.675 |
| cot_few_shot | winter_warm_midlayer | 0 | clean | 335 | 266 | 0.794 |
| cot_few_shot | winter_warm_midlayer | 0 | ambiguous | 165 | 88 | 0.533 |
| cot_few_shot | winter_warm_midlayer | 1 | clean | 334 | 253 | 0.757 |
| cot_few_shot | winter_warm_midlayer | 1 | ambiguous | 165 | 105 | 0.636 |
| cot_few_shot | winter_warm_midlayer | 2 | clean | 335 | 265 | 0.791 |
| cot_few_shot | winter_warm_midlayer | 2 | ambiguous | 165 | 97 | 0.588 |
| self_reflection | winter_warm_midlayer | 0 | clean | 333 | 282 | 0.847 |
| self_reflection | winter_warm_midlayer | 0 | ambiguous | 165 | 120 | 0.727 |
| self_reflection | winter_warm_midlayer | 1 | clean | 335 | 267 | 0.797 |
| self_reflection | winter_warm_midlayer | 1 | ambiguous | 164 | 108 | 0.659 |
| self_reflection | winter_warm_midlayer | 2 | clean | 333 | 266 | 0.799 |
| self_reflection | winter_warm_midlayer | 2 | ambiguous | 165 | 111 | 0.673 |
| fashionprompt | winter_warm_midlayer | 0 | clean | 335 | 268 | 0.800 |
| fashionprompt | winter_warm_midlayer | 0 | ambiguous | 165 | 109 | 0.661 |
| fashionprompt | winter_warm_midlayer | 1 | clean | 335 | 272 | 0.812 |
| fashionprompt | winter_warm_midlayer | 1 | ambiguous | 165 | 111 | 0.673 |
| fashionprompt | winter_warm_midlayer | 2 | clean | 335 | 271 | 0.809 |
| fashionprompt | winter_warm_midlayer | 2 | ambiguous | 165 | 106 | 0.642 |
| voting | winter_warm_midlayer | 0 | clean | 293 | 152 | 0.519 |
| voting | winter_warm_midlayer | 0 | ambiguous | 130 | 59 | 0.454 |
| voting | winter_warm_midlayer | 1 | clean | 292 | 147 | 0.503 |
| voting | winter_warm_midlayer | 1 | ambiguous | 132 | 57 | 0.432 |
| voting | winter_warm_midlayer | 2 | clean | 283 | 143 | 0.505 |
| voting | winter_warm_midlayer | 2 | ambiguous | 133 | 51 | 0.383 |
| weighted_voting | winter_warm_midlayer | 0 | clean | 283 | 153 | 0.541 |
| weighted_voting | winter_warm_midlayer | 0 | ambiguous | 134 | 53 | 0.396 |
| weighted_voting | winter_warm_midlayer | 1 | clean | 291 | 142 | 0.488 |
| weighted_voting | winter_warm_midlayer | 1 | ambiguous | 135 | 60 | 0.444 |
| weighted_voting | winter_warm_midlayer | 2 | clean | 286 | 149 | 0.521 |
| weighted_voting | winter_warm_midlayer | 2 | ambiguous | 137 | 58 | 0.423 |
| borda | winter_warm_midlayer | 0 | clean | 289 | 151 | 0.522 |
| borda | winter_warm_midlayer | 0 | ambiguous | 144 | 67 | 0.465 |
| borda | winter_warm_midlayer | 1 | clean | 289 | 147 | 0.509 |
| borda | winter_warm_midlayer | 1 | ambiguous | 127 | 62 | 0.488 |
| borda | winter_warm_midlayer | 2 | clean | 284 | 136 | 0.479 |
| borda | winter_warm_midlayer | 2 | ambiguous | 141 | 61 | 0.433 |
| garmentagents_fixed | winter_warm_midlayer | 0 | clean | 286 | 153 | 0.535 |
| garmentagents_fixed | winter_warm_midlayer | 0 | ambiguous | 135 | 59 | 0.437 |
| garmentagents_fixed | winter_warm_midlayer | 1 | clean | 282 | 138 | 0.489 |
| garmentagents_fixed | winter_warm_midlayer | 1 | ambiguous | 132 | 58 | 0.439 |
| garmentagents_fixed | winter_warm_midlayer | 2 | clean | 275 | 142 | 0.516 |
| garmentagents_fixed | winter_warm_midlayer | 2 | ambiguous | 131 | 57 | 0.435 |
| garmentagents_adaptive | winter_warm_midlayer | 0 | clean | 270 | 130 | 0.481 |
| garmentagents_adaptive | winter_warm_midlayer | 0 | ambiguous | 127 | 59 | 0.465 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | clean | 273 | 120 | 0.440 |
| garmentagents_adaptive | winter_warm_midlayer | 1 | ambiguous | 132 | 52 | 0.394 |
| garmentagents_adaptive | winter_warm_midlayer | 2 | clean | 290 | 137 | 0.472 |
| garmentagents_adaptive | winter_warm_midlayer | 2 | ambiguous | 137 | 55 | 0.401 |

</details>

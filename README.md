# 项目名称

## 项目简介
本项目旨在通过日志、指标和调用链分析来定位系统问题的根因。它包含多个智能体和工具，用于分析数据并生成结构化的根因分析报告。

## 文件结构
```
main.py
README.md
requirements.txt
agents/
	__init__.py
	base_agent.py
	log_agent.py
	metric_agent.py
	report_agent.py
	trace_agent.py
data/
	case_1/
		ground_truth.json
		inject_time.txt
		logs.csv
		metrics.csv
		traces.csv
	case_2/
		ground_truth.json
		inject_time.txt
		logs.csv
		metrics.csv
		traces.csv
	case_3/
		ground_truth.json
		inject_time.txt
		logs.csv
		metrics.csv
		traces.csv
result/
	agent_result.txt
	final_result.txt
	function_result.txt
tools/
	__init__.py
	log_utils.py
	metric_utils.py
	root_cause_analysis_report.md
	trace_utils.py
workflow/
	__init__.py
	consensus_coordinator.py
```

## 使用方法
1. 将数据集放入 `data/` 文件夹中。
2. 运行 `main.py` 来启动分析流程。
3. 查看生成的报告文件 `result/root_cause_analysis_report.md`。

## 依赖
请确保安装以下依赖：
- Python 3.10
- pandas
- numpy
- matplotlib

可以通过以下命令安装依赖：
```bash
pip install -r requirements.txt
```

## 贡献
欢迎提交问题和贡献代码！

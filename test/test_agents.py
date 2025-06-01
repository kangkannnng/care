import unittest
from unittest.mock import patch
from agents.log_agent import LogAgent
from agents.trace_agent import TraceAgent
from agents.metric_agent import MetricAgent
from agents.report_agent import ReportAgent
from config import api_type, model

class TestAgents(unittest.TestCase):
    def setUp(self):
        """初始化智能体"""
        llm_config = {
            "api_type": api_type,
            "model": model
        }
        self.log_agent = LogAgent(llm_config=llm_config)
        self.trace_agent = TraceAgent(llm_config=llm_config)
        self.metric_agent = MetricAgent(llm_config=llm_config)
        self.report_agent = ReportAgent(llm_config=llm_config)

    @patch('agents.log_agent.LogAgent.analyze_logs')
    def test_log_agent(self, mock_analyze_logs):
        """测试日志智能体"""
        mock_analyze_logs.return_value = "对案例 case_1 的日志分析总结"
        result = self.log_agent.analyze_logs("case_1")
        self.assertIsInstance(result, str)
        self.assertIn("日志分析", result)
        mock_analyze_logs.assert_called_once_with("case_1")

    @patch('agents.trace_agent.TraceAgent.initiate_analysis')
    def test_trace_agent(self, mock_initiate_analysis):
        """测试调用链智能体"""
        mock_initiate_analysis.return_value = "对案例 case_1 的调用链分析总结"
        result = self.trace_agent.initiate_analysis("case_1", None, "日志分析结果")
        self.assertIsInstance(result, str)
        self.assertIn("调用链分析", result)
        mock_initiate_analysis.assert_called_once_with("case_1", None, "日志分析结果")

    @patch('agents.metric_agent.MetricAgent.initiate_analysis')
    def test_metric_agent(self, mock_initiate_analysis):
        """测试指标智能体"""
        mock_initiate_analysis.return_value = "对案例 case_1 的指标分析总结"
        result = self.metric_agent.initiate_analysis("case_1", None, "调用链分析结果")
        self.assertIsInstance(result, str)
        self.assertIn("指标分析", result)
        mock_initiate_analysis.assert_called_once_with("case_1", None, "调用链分析结果")

    @patch('agents.report_agent.ReportAgent.generate_report')
    def test_report_agent(self, mock_generate_report):
        """测试报告智能体"""
        mock_generate_report.return_value = "# 根因分析报告 - 案例 case_1\\n详细的分析内容..."
        report = self.report_agent.generate_report("用户查询", "case_1", "日志分析", "调用链分析", "指标分析")
        self.assertIsInstance(report, str)
        self.assertIn("根因分析报告", report)
        mock_generate_report.assert_called_once_with("用户查询", "case_1", "日志分析", "调用链分析", "指标分析")

if __name__ == "__main__":
    unittest.main()

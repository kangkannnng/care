import unittest
from unittest.mock import patch
from agents.log_agent import LogAgent
from agents.trace_agent import TraceAgent
from agents.metric_agent import MetricAgent
from agents.report_agent import ReportAgent
from config import api_type, model

class TestAgents(unittest.TestCase):
    def setUp(self):
        """
        初始化智能体
        """
        llm_config = {
            "api_type": api_type,
            "model": model
        }
        self.log_agent = LogAgent(llm_config=llm_config)
        self.trace_agent = TraceAgent(llm_config=llm_config)
        self.metric_agent = MetricAgent(llm_config=llm_config)
        self.report_agent = ReportAgent(llm_config=llm_config)

    @patch('agents.log_agent.LogAgent.analyze_logs')
    def test_log_agent_analyze_logs(self, mock_analyze_logs):
        """
        测试 LogAgent 的日志分析功能
        """
        mock_analyze_logs.return_value = "日志分析结果"
        result = self.log_agent.analyze_logs("case_1")
        self.assertEqual(result, "日志分析结果")

    @patch('agents.trace_agent.TraceAgent.initiate_analysis')
    def test_trace_agent_initiate_analysis(self, mock_initiate_analysis):
        """
        测试 TraceAgent 的调用链分析功能
        """
        mock_initiate_analysis.return_value = "调用链分析结果"
        result = self.trace_agent.initiate_analysis("case_1", None, "日志分析结果")
        self.assertEqual(result, "调用链分析结果")

    @patch('agents.metric_agent.MetricAgent.initiate_analysis')
    def test_metric_agent_initiate_analysis(self, mock_initiate_analysis):
        """
        测试 MetricAgent 的指标分析功能
        """
        mock_initiate_analysis.return_value = "指标分析结果"
        result = self.metric_agent.initiate_analysis("case_1", None, "调用链分析结果")
        self.assertEqual(result, "指标分析结果")

    @patch('agents.report_agent.ReportAgent.generate_report')
    def test_report_agent_generate_report(self, mock_generate_report):
        """
        测试 ReportAgent 的报告生成功能
        """
        mock_generate_report.return_value = "最终报告内容"
        result = self.report_agent.generate_report("用户查询", "case_1", "日志分析结果", "调用链分析结果", "指标分析结果")
        self.assertEqual(result, "最终报告内容")

    @patch('agents.log_agent.LogAgent.analyze_logs')
    def test_log_agent_analysis(self, mock_analyze_logs):
        """
        测试 LogAgent 的日志分析结果是否符合预期
        """
        mock_analyze_logs.return_value = {
            "log_summary": "Summary for logs in case 1",
            "total_logs": 64,
            "services": ["cart", "payment", "order", "shipping", "frontend"],
            "log_levels": {"INFO": 51, "ERROR": 13},
            "anomalies": {
                "error_count": 13,
                "warn_count": 0,
                "error_services": ["cart"],
                "warn_services": [],
                "error_time_range": {
                    "start": "2025-05-13 08:12:21",
                    "end": "2025-05-13 08:16:36"
                }
            }
        }
        result = self.log_agent.analyze_logs("case_1")
        self.assertEqual(result["log_summary"], "Summary for logs in case 1")
        self.assertEqual(result["total_logs"], 64)
        self.assertIn("cart", result["services"])

    @patch('agents.trace_agent.TraceAgent.initiate_analysis')
    def test_trace_agent_analysis(self, mock_initiate_analysis):
        """
        测试 TraceAgent 的调用链分析结果是否符合预期
        """
        mock_initiate_analysis.return_value = {
            "trace_summary": "Summary for traces in case 1",
            "trace_count": 10,
            "services": ["frontend", "cart", "payment", "shipping", "order"],
            "trace_analysis": {
                "avg_spans_per_trace": 5.0,
                "max_spans_per_trace": 5,
                "min_spans_per_trace": 5
            }
        }
        result = self.trace_agent.initiate_analysis("case_1", None, "日志分析结果")
        self.assertEqual(result["trace_summary"], "Summary for traces in case 1")
        self.assertEqual(result["trace_count"], 10)
        self.assertIn("frontend", result["services"])

    @patch('agents.metric_agent.MetricAgent.initiate_analysis')
    def test_metric_agent_analysis(self, mock_initiate_analysis):
        """
        测试 MetricAgent 的指标分析结果是否符合预期
        """
        mock_initiate_analysis.return_value = {
            "metric_summary": "Summary for metrics in case 1",
            "total_data_points": 100,
            "services": ["cart", "payment", "order", "shipping", "frontend"],
            "service_analysis": {
                "cart": {"mean": 84.0, "max": 100, "std": 33.73},
                "frontend": {"mean": 50.0, "max": 50, "std": 0.0}
            }
        }
        result = self.metric_agent.initiate_analysis("case_1", None, "调用链分析结果")
        self.assertEqual(result["metric_summary"], "Summary for metrics in case 1")
        self.assertEqual(result["total_data_points"], 100)
        self.assertIn("cart", result["services"])

    @patch('agents.report_agent.ReportAgent.generate_report')
    def test_report_agent_generation(self, mock_generate_report):
        """
        测试 ReportAgent 的报告生成结果是否符合预期
        """
        mock_generate_report.return_value = {
            "success": True,
            "formatted_text": "最终报告内容"
        }
        result = self.report_agent.generate_report(
            "用户查询", "case_1", "日志分析结果", "调用链分析结果", "指标分析结果"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["formatted_text"], "最终报告内容")

    def test_log_agent_real_analysis(self):
        """
        测试 LogAgent 的日志分析功能（真实调用）
        """
        result = self.log_agent.analyze_logs("1")
        self.assertIsInstance(result, str)
        self.assertIn("日志分析", result)

    def test_trace_agent_real_analysis(self):
        """
        测试 TraceAgent 的调用链分析功能（真实调用）
        """
        result = self.trace_agent.initiate_analysis("1", None, "日志分析结果")
        self.assertIsInstance(result, str)
        self.assertIn("调用链分析", result)

    def test_metric_agent_real_analysis(self):
        """
        测试 MetricAgent 的指标分析功能（真实调用）
        """
        result = self.metric_agent.initiate_analysis("1", None, "调用链分析结果")
        self.assertIsInstance(result, str)
        self.assertIn("指标分析", result)

    def test_report_agent_real_generation(self):
        """
        测试 ReportAgent 的报告生成功能（真实调用）
        """
        result = self.report_agent.generate_report(
            "用户查询", "1", "日志分析结果", "调用链分析结果", "指标分析结果"
        )
        self.assertIsInstance(result, str)
        self.assertIn("最终报告", result)

if __name__ == "__main__":
    unittest.main()

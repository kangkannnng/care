import unittest
from tools.log_utils import analyze_logs
from tools.metric_utils import analyze_metrics
from tools.trace_utils import analyze_traces
from tools.report_utils import generate_final_report

class TestTools(unittest.TestCase):
    def test_analyze_logs(self):
        """测试日志分析工具"""
        result = analyze_logs("1")
        self.assertIsInstance(result, dict)
        self.assertIn("log_summary", result)
        self.assertIn("total_logs", result)
        self.assertIn("services", result)
        self.assertIn("log_levels", result)
        self.assertIn("anomalies", result)

    def test_analyze_metrics(self):
        """测试指标分析工具"""
        result = analyze_metrics("1")
        self.assertIsInstance(result, dict)
        self.assertIn("metric_summary", result)
        self.assertIn("total_data_points", result)
        self.assertIn("services", result)
        self.assertIn("service_analysis", result)
        self.assertIn("time_range", result)

    def test_analyze_traces(self):
        """测试调用链分析工具"""
        result = analyze_traces("1")
        self.assertIsInstance(result, dict)
        self.assertIn("trace_summary", result)
        self.assertIn("total_spans", result)
        self.assertIn("trace_count", result)
        self.assertIn("trace_analysis", result)
        self.assertIn("duration_stats", result)

    def test_generate_final_report(self):
        """测试报告生成工具"""
        report = generate_final_report(
            "case_1", "日志分析", "调用链分析", "指标分析",
            "系统资源瓶颈导致的性能问题", "扩容系统资源，优化代码性能"
        )
        self.assertIsInstance(report, dict)
        self.assertIn("case_id", report["report"])
        self.assertIn("root_cause_analysis", report["report"])

if __name__ == "__main__":
    unittest.main()

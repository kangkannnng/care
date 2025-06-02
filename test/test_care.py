import unittest
from unittest.mock import patch
from main import CARE
from config import api_type, model

class TestCARE(unittest.TestCase):
    def setUp(self):
        """
        初始化测试环境
        """
        llm_config = {
            "api_type": api_type,
            "model": model
        }
        self.care_system = CARE(llm_config=llm_config)

    def test_extract_case_id(self):
        """
        测试案例ID提取
        """
        query = "请分析 case_1 的根因问题"
        self.assertEqual(self.care_system.extract_case_id(query), "case_1")

        query = "帮我分析第2个案例的故障原因"
        self.assertEqual(self.care_system.extract_case_id(query), "case_2")

        query = "case_3发生了什么问题？"
        self.assertEqual(self.care_system.extract_case_id(query), "case_3")

        query = "没有案例ID的查询"
        self.assertIsNone(self.care_system.extract_case_id(query))

    @patch('main.CARE.validate_case_data')
    def test_validate_case_data(self, mock_validate_case_data):
        """
        测试案例数据验证
        """
        mock_validate_case_data.return_value = True
        self.assertTrue(self.care_system.validate_case_data("case_1"))

        mock_validate_case_data.return_value = False
        self.assertFalse(self.care_system.validate_case_data("case_999"))

    @patch('main.CARE.load_ground_truth')
    def test_load_ground_truth(self, mock_load_ground_truth):
        """
        测试加载标准答案
        """
        mock_load_ground_truth.return_value = {"root_cause": "一些预期的根因"}
        ground_truth = self.care_system.load_ground_truth("case_1")
        self.assertIn("root_cause", ground_truth)

    @patch('main.CARE.extract_case_id')
    @patch('main.CARE.validate_case_data')
    @patch('main.CARE.load_ground_truth')
    @patch('agents.log_agent.LogAgent.analyze_logs')
    @patch('agents.trace_agent.TraceAgent.initiate_analysis')
    @patch('agents.metric_agent.MetricAgent.initiate_analysis')
    @patch('agents.report_agent.ReportAgent.generate_report')
    def test_analyze_case(self, mock_generate_report, mock_metric_analysis, mock_trace_analysis, mock_log_analysis, mock_load_ground_truth, mock_validate_case_data, mock_extract_case_id):
        """
        测试案例分析
        """
        query = "请分析 case_1 的根因问题"

        # 配置 mock 返回值
        mock_extract_case_id.return_value = "case_1"
        mock_validate_case_data.return_value = True
        mock_load_ground_truth.return_value = {"root_cause": "一些预期的根因"}
        mock_log_analysis.return_value = "日志分析结果"
        mock_trace_analysis.return_value = "调用链分析结果"
        mock_metric_analysis.return_value = "指标分析结果"
        mock_generate_report.return_value = "最终报告内容"

        result = self.care_system.analyze_case(query)
        self.assertTrue(result["success"])
        self.assertEqual(result["case_id"], "case_1")
        self.assertEqual(result["final_report"], "最终报告内容")

        # 验证 mock 是否被正确调用
        mock_extract_case_id.assert_called_once_with(query)
        mock_validate_case_data.assert_called_once_with("case_1")
        mock_load_ground_truth.assert_called_once_with("case_1")
        mock_log_analysis.assert_called_once()
        mock_trace_analysis.assert_called_once()
        mock_metric_analysis.assert_called_once()
        mock_generate_report.assert_called_once()

if __name__ == "__main__":
    unittest.main()

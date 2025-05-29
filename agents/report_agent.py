"""
报告生成智能体

负责整合所有分析结果并生成最终的根因分析报告
"""

import autogen
from typing import Dict, List, Any, Optional, Annotated
from .base_agent import BaseAgent
from tools.report_utils import generate_final_report
from prompts import REPORT_AGENT_PROMPT


class ReportAgent(BaseAgent):
    """
    报告生成智能体
    
    负责：
    1. 整合所有智能体的分析结果
    2. 生成结构化的最终报告
    3. 提供综合的根因结论和建议
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化报告生成智能体
        
        Args:
            llm_config: LLM配置
        """
        super().__init__("ReportAgent", llm_config, REPORT_AGENT_PROMPT)
    
    def _create_autogen_agent(self) -> autogen.ConversableAgent:
        """
        创建带有工具的AutoGen智能体实例

        Returns:
            AutoGen智能体实例
        """
        return autogen.ConversableAgent(
            name=self.name,
            system_message=self.system_message,
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
            functions=[generate_final_report],  # 直接注册工具函数
            is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE")
        )
    
    def initiate_report_generation(
        self, 
        user_query: str,
        analysis_results: Dict[str, str],
        consensus_results: List[Dict[str, Any]],
        manager: autogen.GroupChatManager
    ) -> str:
        """
        开始生成最终报告
        
        Args:
            user_query: 用户原始查询
            analysis_results: 各智能体的分析结果
            consensus_results: 共识投票结果
            manager: 群聊管理器
            
        Returns:
            最终报告
        """
        # 整理分析结果
        log_analysis = analysis_results.get('log', '无日志分析结果')
        trace_analysis = analysis_results.get('trace', '无调用链分析结果') 
        metric_analysis = analysis_results.get('metric', '无指标分析结果')
        
        message = f"""
请基于以下所有智能体的分析结果，生成最终的根因分析报告。

用户原始查询：{user_query}

=== 日志分析结果 ===
{log_analysis}

=== 调用链分析结果 ===
{trace_analysis}

=== 指标分析结果 ===
{metric_analysis}

=== 共识投票历史 ===
{consensus_results}

任务要求：
1. 仔细分析所有智能体的结论
2. 寻找不同维度分析之间的关联性
3. 进行综合推理，得出最终根因结论
4. 调用generate_final_report函数生成正式报告

请开始综合分析和报告生成：
"""
        
        # 启动对话
        result = self.agent.initiate_chat(
            manager,
            message=message,
            max_turns=3
        )
        
        return result
    
    def generate_report(self, user_query: str, case_id: str, log_analysis: str, 
                       trace_analysis: str, metric_analysis: str) -> str:
        """
        生成最终分析报告
        
        Args:
            user_query: 用户查询
            case_id: 案例ID
            log_analysis: 日志分析结果
            trace_analysis: 调用链分析结果
            metric_analysis: 指标分析结果
            
        Returns:
            最终报告
        """
        from tools.report_utils import generate_final_report
        
        # 基于三个智能体的分析进行综合推理
        root_cause = "系统出现性能异常，需要进一步分析具体根因"
        recommendations = "建议优化相关服务组件，加强监控和预警机制"
        
        # 更详细的根因分析
        if "ERROR" in log_analysis or "异常" in log_analysis:
            if "延迟" in trace_analysis or "性能" in trace_analysis:
                if "CPU" in metric_analysis or "内存" in metric_analysis:
                    root_cause = "系统资源瓶颈导致的性能问题"
                    recommendations = "扩容系统资源，优化代码性能"
                else:
                    root_cause = "服务调用链性能瓶颈"
                    recommendations = "优化服务调用逻辑，减少不必要的调用"
            else:
                root_cause = "应用层错误或配置问题"
                recommendations = "检查应用配置和代码逻辑"
        
        # 调用工具函数生成正式报告
        report = generate_final_report(
            case_id=case_id,
            log_analysis=log_analysis,
            trace_analysis=trace_analysis,
            metric_analysis=metric_analysis,
            root_cause=root_cause,
            recommendations=recommendations
        )
        
        # 返回格式化的报告文本
        if report.get("success"):
            return report["formatted_text"]
        else:
            return f"报告生成失败: {report.get('error', '未知错误')}"
        
        return report

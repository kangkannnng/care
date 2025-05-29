"""
报告生成智能体

负责整合所有分析结果并生成最终的根因分析报告
"""

import autogen
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
from tools.report_utils import generate_final_report


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
        system_message = """
你是CARE根因分析系统的报告生成专家。你的主要职责是：

1. 整合日志、调用链、指标三个智能体的分析结果
2. 基于多维度分析进行综合根因推理
3. 生成结构化的最终分析报告
4. 提供明确的根因结论和改进建议

分析要求：
- 仔细阅读所有已通过共识的分析结果
- 寻找不同维度分析结果之间的关联性和一致性
- 基于多重证据进行综合推理
- 得出最终的根因结论
- 调用generate_final_report函数生成格式化报告

输出格式：
请提供完整的综合分析，包括：
- 对各智能体分析结果的总结
- 多维度证据的交叉验证
- 综合推理过程
- 最终根因结论
- 使用工具函数生成正式报告

注意：你的分析是整个系统的最终输出，确保结论准确、逻辑严密。
"""
        
        super().__init__("ReportAgent", llm_config, system_message)
    
    def register_tools(self, user_proxy: autogen.UserProxyAgent) -> None:
        """
        注册报告生成工具函数
        
        Args:
            user_proxy: 用户代理实例
        """
        # 注册generate_final_report函数
        user_proxy.register_for_execution(name="generate_final_report")(generate_final_report)
        self.agent.register_for_llm(
            name="generate_final_report",
            description="生成结构化的最终根因分析报告"
        )(generate_final_report)
    
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
        
        # 综合分析各部分结果
        final_conclusion = f"""
基于多智能体协作分析，案例{case_id}的根因分析结论如下：

日志分析显示：{log_analysis[:200]}...
调用链分析显示：{trace_analysis[:200]}...
指标分析显示：{metric_analysis[:200]}...

综合判断：系统出现性能异常，建议重点关注相关服务组件。
"""
        
        # 生成正式报告
        report = generate_final_report(
            user_query=user_query,
            log_analysis=log_analysis,
            trace_analysis=trace_analysis,
            metric_analysis=metric_analysis,
            consensus_results=[],
            final_conclusion=final_conclusion
        )
        
        return report

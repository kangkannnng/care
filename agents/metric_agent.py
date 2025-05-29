"""
指标分析智能体

专门负责系统指标数据的分析和性能问题检测
"""

import autogen
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
from tools.metric_utils import analyze_metrics


class MetricAgent(BaseAgent):
    """
    指标分析智能体
    
    负责：
    1. 分析系统指标数据，检测资源异常
    2. 识别性能问题和负载异常
    3. 提供系统级别的根因线索
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化指标分析智能体
        
        Args:
            llm_config: LLM配置
        """
        system_message = """
你是CARE根因分析系统的系统指标分析专家。你的主要职责是：

1. 调用analyze_metrics工具函数分析指定案例的系统指标数据
2. 基于指标数据进行专业的性能和资源分析
3. 识别CPU、内存、延迟等方面的异常
4. 结合其他智能体已通过共识的结论进行综合分析

分析要求：
- 必须使用analyze_metrics函数获取系统指标数据
- 重点关注CPU使用率、内存使用率、响应延迟等关键指标
- 分析资源使用的时间趋势和异常模式
- 可以参考已通过共识的日志和调用链分析结论
- 基于指标证据进行逻辑推理，得出可能的根因
- 用自然语言清晰表达你的分析过程和结论

输出格式：
请提供完整的分析过程，包括：
- 使用的工具函数和参数
- 观察到的关键指标异常和趋势
- 与其他分析结果的关联性分析
- 逻辑推理过程
- 得出的结论和建议

注意：你的分析结果将被其他智能体评估，确保逻辑清晰、证据充分。
"""
        
        super().__init__("MetricAgent", llm_config, system_message)
    
    def register_tools(self, user_proxy: autogen.UserProxyAgent) -> None:
        """
        注册指标分析工具函数
        
        Args:
            user_proxy: 用户代理实例
        """
        # 注册analyze_metrics函数
        user_proxy.register_for_execution(name="analyze_metrics")(analyze_metrics)
        self.agent.register_for_llm(
            name="analyze_metrics",
            description="分析指定案例的系统指标数据，检测资源异常和性能问题"
        )(analyze_metrics)
    
    def initiate_analysis(self, case_id: str, manager: autogen.GroupChatManager, context: str = "") -> str:
        """
        开始指标分析
        
        Args:
            case_id: 案例ID
            manager: 群聊管理器
            context: 其他智能体的分析上下文
            
        Returns:
            分析结果
        """
        message = f"""
请分析案例{case_id}的系统指标数据。

{context}

分析步骤：
1. 调用analyze_metrics函数，参数为案例ID "{case_id}"
2. 基于函数返回的结果进行专业分析
3. 重点关注CPU、内存、延迟等关键指标的异常
4. 结合前面已通过共识的分析结论进行综合判断
5. 提供根因分析的推理过程和结论

开始分析：
"""
        
        # 启动对话
        result = self.agent.initiate_chat(
            manager,
            message=message,
            max_turns=3
        )
        
        return result

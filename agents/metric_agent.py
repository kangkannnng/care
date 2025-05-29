"""
指标分析智能体

专门负责系统指标数据的分析和性能问题检测
"""

import autogen
from typing import Dict, List, Any, Optional, Annotated
from .base_agent import BaseAgent
from tools.metric_utils import analyze_metrics
from prompts import METRIC_AGENT_PROMPT


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
        super().__init__("MetricAgent", llm_config, METRIC_AGENT_PROMPT)
    
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
            functions=[analyze_metrics],  # 直接注册工具函数
            is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE")
        )
    
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

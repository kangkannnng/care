from autogen import ConversableAgent, UserProxyAgent
from typing import Dict, List, Any, Optional
from abc import ABC
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, name: str, llm_config: Dict[str, Any], system_message: str):
        """
        初始化基础智能体

        Args:
            name: 智能体名称
            llm_config: LLM配置
            system_message: 系统提示消息
        """
        self.name = name
        self.llm_config = llm_config
        self.system_message = system_message
        self.analysis_history: List[Dict[str, Any]] = []
        
        # 基于AutoGen创建智能体实例
        self.agent = self._create_autogen_agent()
        
    def _create_autogen_agent(self) -> ConversableAgent:
        """
        创建AutoGen智能体实例

        Returns:
            AutoGen智能体实例
        """
        return ConversableAgent(
            name=self.name,
            system_message=self.system_message,
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
            is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE")
        )
    
    def register_tools(self, user_proxy: UserProxyAgent) -> None:
        """
        注册工具函数到用户代理
        
        Args:
            user_proxy: 用户代理实例
        """
        # 由子类实现具体的工具注册逻辑
        pass
    
    def add_analysis_record(self, analysis: Dict[str, Any]) -> None:
        """
        添加分析记录
        
        Args:
            analysis: 分析结果
        """
        from datetime import datetime
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['agent'] = self.name
        self.analysis_history.append(analysis)
        logger.info(f"{self.name} 添加分析记录")
    
    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的分析结果
        
        Returns:
            最新的分析结果，如果没有则返回None
        """
        if self.analysis_history:
            return self.analysis_history[-1]
        return None

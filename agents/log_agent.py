"""
日志分析智能体

专门负责日志数据的分析和异常检测
"""

import autogen
from typing import Dict, List, Any, Optional, Annotated
from .base_agent import BaseAgent
from tools.log_utils import analyze_logs
from prompts import log_agent_prompt
import os


class LogAgent(BaseAgent):
    """
    日志分析智能体
    
    负责：
    1. 分析日志数据，检测错误和异常模式
    2. 识别故障时间点和影响服务
    3. 提供日志级别的根因线索
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化日志分析智能体
        
        Args:
            llm_config: LLM配置
        """
        super().__init__("LogAgent", llm_config, log_agent_prompt)
    
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
            functions=[analyze_logs],
            is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE")
        )
    
    
    def initiate_analysis(self, case_id: str, manager: autogen.GroupChatManager) -> str:
        """
        开始日志分析
        
        Args:
            case_id: 案例ID
            manager: 群聊管理器
            
        Returns:
            分析结果
        """
        message = f"""
请分析案例{case_id}的日志数据。

分析步骤：
1. 调用analyze_logs函数，参数为案例ID "{case_id}"
2. 基于函数返回的结果进行专业分析
3. 重点关注错误日志、异常模式和时间分布
4. 提供根因分析的推理过程和结论

开始分析：
"""
        
        # 启动对话
        result = self.agent.initiate_chat(
            manager,
            message=message,
            max_turns=3
        )
        
        return result
    
    def set_case_path(self, case_path: str):
        """设置案例数据路径"""
        self.case_path = case_path
    
    def analyze_logs(self, case_path: str) -> str:
        """
        直接分析日志数据
        
        Args:
            case_path: 案例数据路径
            
        Returns:
            分析结果
        """
        from tools.log_utils import analyze_logs as tool_analyze_logs
        
        try:
            # 使用工具函数分析日志
            case_id = os.path.basename(case_path)
            
            # 调用工具函数进行日志分析
            analysis_result = tool_analyze_logs(case_id)
            
            return analysis_result
            
        except Exception as e:
            return f"日志分析失败: {str(e)}"

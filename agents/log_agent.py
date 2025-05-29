"""
日志分析智能体

专门负责日志数据的分析和异常检测
"""

import autogen
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
from tools.log_utils import analyze_logs
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
        system_message = """
你是CARE根因分析系统的日志分析专家。你的主要职责是：

1. 调用analyze_logs工具函数分析指定案例的日志数据
2. 基于日志内容进行专业的根因分析
3. 识别错误模式、异常时间点和问题服务
4. 提供清晰的分析过程和逻辑推理

分析要求：
- 必须使用analyze_logs函数获取日志数据
- 重点关注ERROR和WARN级别的日志
- 分析错误的时间分布和服务分布模式
- 基于日志证据进行逻辑推理，得出可能的根因
- 用自然语言清晰表达你的分析过程和结论

输出格式：
请提供完整的分析过程，包括：
- 使用的工具函数和参数
- 观察到的关键现象和异常
- 逻辑推理过程
- 得出的结论和建议

注意：你的分析结果将被其他智能体评估，确保逻辑清晰、证据充分。
"""
        
        super().__init__("LogAgent", llm_config, system_message)
    
    def register_tools(self, user_proxy: autogen.UserProxyAgent) -> None:
        """
        注册日志分析工具函数
        
        Args:
            user_proxy: 用户代理实例
        """
        # 注册analyze_logs函数
        user_proxy.register_for_execution(name="analyze_logs")(analyze_logs)
        self.agent.register_for_llm(
            name="analyze_logs",
            description="分析指定案例的日志数据，检测异常并进行根因分析"
        )(analyze_logs)
    
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

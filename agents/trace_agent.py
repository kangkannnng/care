"""
调用链分析智能体

专门负责调用链数据的分析和性能瓶颈检测
"""

import autogen
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
from tools.trace_utils import analyze_traces


class TraceAgent(BaseAgent):
    """
    调用链分析智能体
    
    负责：
    1. 分析调用链数据，检测性能瓶颈
    2. 识别异常调用和服务依赖关系
    3. 提供调用链级别的根因线索
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化调用链分析智能体
        
        Args:
            llm_config: LLM配置
        """
        system_message = """
你是CARE根因分析系统的调用链分析专家。你的主要职责是：

1. 调用analyze_traces工具函数分析指定案例的调用链数据
2. 基于调用链数据进行专业的性能分析
3. 识别性能瓶颈、异常调用和服务依赖关系
4. 结合其他智能体已通过共识的结论进行综合分析

分析要求：
- 必须使用analyze_traces函数获取调用链数据
- 重点关注调用时长、异常调用和性能瓶颈
- 分析服务间的调用关系和依赖模式
- 可以参考已通过共识的日志分析结论
- 基于调用链证据进行逻辑推理，得出可能的根因
- 用自然语言清晰表达你的分析过程和结论

输出格式：
请提供完整的分析过程，包括：
- 使用的工具函数和参数
- 观察到的关键性能指标和异常
- 与其他分析结果的关联性分析
- 逻辑推理过程
- 得出的结论和建议

注意：你的分析结果将被其他智能体评估，确保逻辑清晰、证据充分。
"""
        
        super().__init__("TraceAgent", llm_config, system_message)
    
    def register_tools(self, user_proxy: autogen.UserProxyAgent) -> None:
        """
        注册调用链分析工具函数
        
        Args:
            user_proxy: 用户代理实例
        """
        # 注册analyze_traces函数
        user_proxy.register_for_execution(name="analyze_traces")(analyze_traces)
        self.agent.register_for_llm(
            name="analyze_traces",
            description="分析指定案例的调用链数据，检测性能瓶颈和异常调用"
        )(analyze_traces)
    
    def initiate_analysis(self, case_id: str, manager: autogen.GroupChatManager, context: str = "") -> str:
        """
        开始调用链分析
        
        Args:
            case_id: 案例ID
            manager: 群聊管理器
            context: 其他智能体的分析上下文
            
        Returns:
            分析结果
        """
        message = f"""
请分析案例{case_id}的调用链数据。

{context}

分析步骤：
1. 调用analyze_traces函数，参数为案例ID "{case_id}"
2. 基于函数返回的结果进行专业分析
3. 重点关注性能瓶颈、异常调用和服务依赖
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

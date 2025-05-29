"""
Prompts模块初始化文件

导出所有agent的提示词
"""

from .log_agent_prompt import LOG_AGENT_PROMPT
from .metric_agent_prompt import METRIC_AGENT_PROMPT
from .trace_agent_prompt import TRACE_AGENT_PROMPT
from .report_agent_prompt import REPORT_AGENT_PROMPT

__all__ = [
    'LOG_AGENT_PROMPT',
    'METRIC_AGENT_PROMPT', 
    'TRACE_AGENT_PROMPT',
    'REPORT_AGENT_PROMPT'
]

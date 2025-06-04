from autogen import ConversableAgent, LLMConfig
from config import api_type, model
from tool import analyze_logs, analyze_metrics, analyze_traces
from prompt import log_agent_prompt, metric_agent_prompt, trace_agent_prompt, report_agent_prompt


llm_config = LLMConfig(api_type=api_type, model=model)

with llm_config:
    log_agent = ConversableAgent(
        name="log_analyzer",
        system_message=log_agent_prompt,
        functions=[analyze_logs]
    )
    metric_agent = ConversableAgent(
        name="metric_analyzer",
        system_message=metric_agent_prompt,
        functions=[analyze_metrics]
    )
    trace_agent = ConversableAgent(
        name="trace_analyzer",
        system_message=trace_agent_prompt,
        functions=[analyze_traces]
    )
    report_agent = ConversableAgent(
        name="report_generator",
        system_message=report_agent_prompt,
        functions=[]
    )
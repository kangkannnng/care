from autogen import ConversableAgent, LLMConfig
from config import llm_config
from tool import provide_analysis_plan, route_to_agent, get_log, provide_log_result, \
    get_metric, provide_metric_result, get_trace, provide_trace_result, prepare_vote, complete_vote
from prompt import (
    plan_agent_prompt,
    log_agent_prompt, metric_agent_prompt, trace_agent_prompt, report_agent_prompt,
    review_master_prompt, vote_coordinator_prompt,
    logic_validator_prompt, data_consistency_validator_prompt, feasibility_validator_prompt
)


with llm_config:
    plan_agent = ConversableAgent(
        name="plan_agent",
        system_message=plan_agent_prompt,
        functions=[provide_analysis_plan, route_to_agent],
        description="生成并管理待办流程的智能体"
    )
    
    log_agent = ConversableAgent(
        name="log_agent",
        system_message=log_agent_prompt,
        functions=[get_log, provide_log_result],
        description="分析系统日志并提供根因线索。"
    )

    metric_agent = ConversableAgent(
        name="metric_agent",
        system_message=metric_agent_prompt,
        functions=[get_metric, provide_metric_result],
        description="分析系统监控指标并识别资源和性能异常。"
    )

    trace_agent = ConversableAgent(
        name="trace_agent",
        system_message=trace_agent_prompt,
        functions=[get_trace, provide_trace_result],
        description="分析调用链数据并识别性能瓶颈和异常调用。"
    )
    
    review_agent = ConversableAgent(
        name="review_agent",
        system_message=review_master_prompt,
        functions=[prepare_vote],
        description="发起复审并协调投票流程。"
    )

    reviewers = [
        ConversableAgent(
            name="logic_validator", 
            system_message=logic_validator_prompt, 
            description="验证分析推理的逻辑严谨性。"
        ),
        ConversableAgent(
            name="data_consistency_validator", 
            system_message=data_consistency_validator_prompt,
            description="校验分析中数据的一致性和准确性。"
        ),
        ConversableAgent(
            name="feasibility_validator", 
            system_message=feasibility_validator_prompt, 
            description="评估建议措施的实施可行性和风险。"
        )
    ]

    vote_agent = ConversableAgent(
        name="投票管理师",
        system_message=vote_coordinator_prompt,
        functions=[complete_vote],
        description="统计复审投票并判断是否通过。"
    )

    report_agent = ConversableAgent(
        name="报告生成师",
        system_message=report_agent_prompt,
        functions=[],
        description="整合分析结果并生成综合根因分析报告。"
    )

# 用户代理，用于接收用户输入
user_proxy = ConversableAgent(
    name="用户",
    human_input_mode="ALWAYS",
    description="代表用户在对话中提供输入。"
)
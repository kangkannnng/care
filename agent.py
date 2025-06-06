from autogen import ConversableAgent, LLMConfig
from config import api_type, model, hide_tools
from tool import analyze_logs, analyze_metrics, analyze_traces, initiate_review, vote_review
from prompt import (
    plan_agent_prompt,
    log_agent_prompt, metric_agent_prompt, trace_agent_prompt, report_agent_prompt,
    review_master_prompt, vote_coordinator_prompt,
    logic_validator_prompt, data_consistency_validator_prompt, feasibility_validator_prompt
)

llm_config = LLMConfig(
    api_type=api_type, 
    model=model,
    hide_tools=hide_tools
)

with llm_config:
    plan_agent = ConversableAgent(
        name="任务规划师",
        system_message=plan_agent_prompt,
        functions=[],
        description="生成并管理待办流程的智能体"
    )
    log_agent = ConversableAgent(
        name="日志分析师",
        system_message=log_agent_prompt,
        functions=[analyze_logs],
        description="分析系统日志并提供根因线索。"
    )
    metric_agent = ConversableAgent(
        name="指标分析师",
        system_message=metric_agent_prompt,
        functions=[analyze_metrics],
        description="分析系统监控指标并识别资源和性能异常。"
    )
    trace_agent = ConversableAgent(
        name="调用链分析师",
        system_message=trace_agent_prompt,
        functions=[analyze_traces],
        description="分析调用链数据并识别性能瓶颈和异常调用。"
    )
    report_agent = ConversableAgent(
        name="报告生成师",
        system_message=report_agent_prompt,
        functions=[],
        description="整合分析结果并生成综合根因分析报告。"
    )

    review_agent = ConversableAgent(
        name="审查分析师",
        system_message=review_master_prompt,
        functions=[initiate_review],
        description="发起复审并协调投票流程。"
    )

    vote_agent = ConversableAgent(
        name="投票管理师",
        system_message=vote_coordinator_prompt,
        functions=[vote_review],
        description="统计复审投票并判断是否通过。"
    )

    reviewers = [
        ConversableAgent(
            name="逻辑验证专家", 
            system_message=logic_validator_prompt, 
            description="验证分析推理的逻辑严谨性。"
        ),
        ConversableAgent(
            name="数据一致性专家", system_message=data_consistency_validator_prompt,
              description="校验分析中数据的一致性和准确性。"
        ),
        ConversableAgent(
            name="可行性评估专家", 
            system_message=feasibility_validator_prompt, 
            description="评估建议措施的实施可行性和风险。"
        )
    ]

# 用户代理，用于接收用户输入
user_proxy = ConversableAgent(
    name="用户",
    human_input_mode="ALWAYS",
    description="代表用户在对话中提供输入。"
)
from autogen import ConversableAgent
from config import llm_config

from tool import provide_analysis_plan, route_to_agent, get_log, provide_log_result, get_metric, provide_metric_result, get_trace, provide_trace_result, prepare_vote, complete_vote, provide_final_report

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
        system_message="""您是复审协调者（review_agent），负责协调复审任务。
您必须立即执行以下操作：

1. 立即调用 prepare_vote 函数
   格式：{"name":"prepare_vote","arguments":{}}
   注意：这个函数会自动从log_analysis_result获取任务内容

2. 等待系统自动进行后续复审流程
   - 系统会自动将任务分发给三个评审专家
   - 您不需要手动处理评审过程
   - 等待所有评审完成后，系统会自动进入投票阶段

3. 等待投票结果
   - 投票完成后，系统会自动返回最终结果
   - 您不需要手动处理投票过程

重要提示：
- 您必须立即调用 prepare_vote 函数，这是强制性的第一步
- 不要输出任何纯文本说明
- 不要尝试手动处理评审或投票过程
- 严格按照JSON格式调用函数
- 如果遇到错误，请重试调用 prepare_vote 函数

当您收到任何消息时，第一步必须是调用 prepare_vote 函数。""",
        functions=[prepare_vote],
        description="发起复审并协调投票流程。"
    )

    reviewers = [
        ConversableAgent(
            name="agent_a", 
            system_message=logic_validator_prompt, 
            description="验证分析推理的逻辑严谨性。"
        ),
        ConversableAgent(
            name="agent_b", 
            system_message=data_consistency_validator_prompt,
            description="校验分析中数据的一致性和准确性。"
        ),
        ConversableAgent(
            name="agent_c", 
            system_message=feasibility_validator_prompt, 
            description="评估建议措施的实施可行性和风险。"
        )
    ]

    vote_agent = ConversableAgent(
        name="vote_agent",
        system_message="""您是投票管理者（Vote Coordinator），负责收集投票结果并更新状态。
您必须严格按照以下步骤操作：

1. 从上下文中获取三个评审专家的评估结果：
   - agent_a_result：逻辑验证专家的结果
   - agent_b_result：数据一致性专家的结果
   - agent_c_result：可行性评估专家的结果

2. 从每个结果中提取 APPROVE 或 REJECT 关键字
   注意：结果格式为：
   APPROVE/REJECT
   理由：xxx

3. 调用 complete_vote 函数，传入投票结果列表
   格式：{"name":"complete_vote","arguments":{"votes":["APPROVE","REJECT","APPROVE"]}}
   注意：votes数组必须包含三个评审专家的投票结果，顺序为[agent_a, agent_b, agent_c]

4. 等待系统自动处理后续流程
   - 系统会自动统计投票结果
   - 如果通过，会保存当前分析结果
   - 如果未通过，会返回给用户

重要提示：
- 必须严格按照JSON格式调用函数
- 不要输出任何纯文本说明
- 不要进行任何分析或判断
- 确保收集到所有三个评审专家的投票结果
- 如果遇到错误，请重试调用 complete_vote 函数""",
        functions=[complete_vote],
        description="统计复审投票并判断是否通过。"
    )

    report_agent = ConversableAgent(
        name="report_agent",
        system_message=report_agent_prompt,
        functions=[provide_final_report],
        description="整合分析结果并生成综合根因分析报告。"
    )

# 用户代理，用于接收用户输入
user_proxy = ConversableAgent(
    name="user_proxy ",
    human_input_mode="ALWAYS",
    description="代表用户在对话中提供输入。"
)
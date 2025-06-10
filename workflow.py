import os
import pandas as pd
from typing import Dict, Any, Annotated, List

from autogen import ConversableAgent, UserProxyAgent, LLMConfig
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group import ReplyResult, ContextVariables, ExpressionContextCondition, ExpressionAvailableCondition, ContextExpression, OnContextCondition, NestedChatTarget
from autogen.agentchat.group.patterns import DefaultPattern
from autogen.agentchat.group.targets.transition_target import AgentTarget, AgentNameTarget, RevertToUserTarget
from context_variables import context_variables
from agent import log_agent, metric_agent, trace_agent, report_agent, review_agent, vote_agent, reviewers, user_proxy, plan_agent
from tool import extract_task_message, record_agent_response


# plan_agent
plan_agent.register_handoffs(conditions=[
    OnContextCondition(
        target=AgentTarget(log_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'planning'"
            )
        )
    ),
    OnContextCondition(
        target=AgentTarget(metric_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'log_consensus'"
            )
        )
    ),
    OnContextCondition(
        target=AgentTarget(trace_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'metric_consensus'"
            )
        )
    ),
    OnContextCondition(
        target=AgentTarget(report_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'trace_consensus'"
            )
        )
    )
])

# log_agent
log_agent.register_handoffs(conditions=[
    OnContextCondition(
        target=AgentTarget(review_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'log_analysis'"
            )
        )
    )
])

# metric_agent
metric_agent.register_handoffs(conditions=[
    OnContextCondition(
        target=AgentTarget(review_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'metric_analysis'"
            )
        )
    )
])

# trace_agent
trace_agent.register_handoffs(conditions=[
    OnContextCondition(
        target=AgentTarget(review_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'trace_analysis'"
            )
        )
    )
])

# review_agent
nested_chat_queue = []
for reviewer in reviewers:
    nested_chat_queue.append(
        {
            "recipient": reviewer,
            "message": extract_task_message,
            "max_turns": 1,
            "summary_method": record_agent_response,
        }
    )

review_agent.register_handoffs(conditions=[
    OnContextCondition(
        target=NestedChatTarget(nested_chat_config={"chat_queue": nested_chat_queue}),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'log_analysis' or ${workflow_stage} == 'metric_analysis' or ${workflow_stage} == 'trace_analysis'"
            )
        )
    ),
    OnContextCondition(
        target=AgentTarget(vote_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="len(${consensus_votes}) >= 3"
            )
        )
    )
])

# vote_agent
vote_agent.register_handoffs(conditions=[
    OnContextCondition(
        target=AgentTarget(plan_agent),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'log_consensus' or ${workflow_stage} == 'metric_consensus' or ${workflow_stage} == 'trace_consensus'"
            )
        )
    )
])

# report_agent
report_agent.register_handoffs(conditions=[
    OnContextCondition(
        target=RevertToUserTarget(),
        condition=ExpressionContextCondition(
            expression=ContextExpression(
                expression="${workflow_stage} == 'final_report'"
            )
        )
    )
])

agents = [  
    plan_agent,  
    log_agent,  
    metric_agent,   
    trace_agent,  
    review_agent,  
    vote_agent,  
    report_agent  
]  

agent_pattern = DefaultPattern(
    initial_agent=plan_agent,
    agents=agents,
    user_agent=user_proxy,
    context_variables=context_variables,
)

current_task = "Case ID 为1的任务发生异常，请帮我分析故障原因"

chat_result, final_context, last_agent = initiate_group_chat(
    pattern=agent_pattern,
    messages=f"{current_task}",
    max_rounds=10,
)
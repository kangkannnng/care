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

redundant_agent_names = ["agent_a", "agent_b", "agent_c"]

def extract_task_message(recipient: ConversableAgent, messages: list[dict[str, Any]], sender: ConversableAgent, config) -> str:
    """Extracts the task to give to an agent as the task"""
    return sender.context_variables.get("current_task", "There's no task, return UNKNOWN.")

def record_agent_response(sender: ConversableAgent, recipient: ConversableAgent, summary_args: dict) -> str:
    """Record each nested agent's response, track completion, and prepare for evaluation"""
    context_var_key = f"{recipient.name.lower()}_result"
    review_agent.context_variables.set(context_var_key, recipient.chat_messages[sender][-1]["content"])

    task_completed = all(review_agent.context_variables.get(f"{key}_result") is not None
                        for key in redundant_agent_names)

    if not task_completed:
        return ""
    else:
        combined_responses = "\n".join(
            [f"agent_{agent_name}:\n{review_agent.context_variables.get(f'{agent_name}_result')}\n\n---"
             for agent_name in nested_chat_queue]
        )
        return combined_responses

nested_chat_queue = []
for reviewer in reviewers:
    nested_chat = {
        "recipient": reviewer,
        "message": extract_task_message,
        "max_turns": 1,
        "summary_method": record_agent_response,
    }
    nested_chat_queue.append(nested_chat)

review_agent.handoffs.add_context_conditions([
    OnContextCondition(
        target=NestedChatTarget(
            nested_chat_config={
                "chat_queue": nested_chat_queue
            }
        ),
        condition=ExpressionContextCondition(
            ContextExpression("len(${agent_a_result}) == 0 or len(${agent_b_result}) == 0 or len(${agent_c_result}) == 0"
            )
        )
    ),
    OnContextCondition(
        target=AgentNameTarget("vote_agent"),
        condition=ExpressionContextCondition(
            ContextExpression("len(${agent_a_result}) != 0 and len(${agent_b_result}) != 0 and len(${agent_c_result}) != 0")
        )
    )
])

review_agent.handoffs.set_after_work(RevertToUserTarget())
vote_agent.handoffs.set_after_work(RevertToUserTarget())

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
    max_rounds=15,
)
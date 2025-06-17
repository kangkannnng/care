from autogen import ConversableAgent
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group import ExpressionContextCondition, ContextExpression, OnContextCondition, NestedChatTarget
from autogen.agentchat.group.patterns import DefaultPattern
from autogen.agentchat.group.targets.transition_target import AgentNameTarget
from context_variables import context_variables
from agent import log_agent, metric_agent, trace_agent, report_agent, review_agent, vote_agent, reviewers, user_proxy, plan_agent

redundant_agent_names = ["agent_a", "agent_b", "agent_c"]

def extract_task_message(recipient: ConversableAgent, messages: list, sender: ConversableAgent, config) -> str:
    """从上下文变量中提取任务消息"""
    task = sender.context_variables.get("current_task", "")
    if not task:
        return "There's no task, return UNKNOWN."
    return task

def record_agent_response(sender: ConversableAgent, recipient: ConversableAgent, summary_args: dict) -> str:
    """记录每个嵌套代理的响应"""
    context_var_key = f"{recipient.name.lower()}_result"
    review_agent.context_variables.set(context_var_key, recipient.chat_messages[sender][-1]["content"])

    task_completed = all(review_agent.context_variables.get(f"{key}_result") != ""
                        for key in redundant_agent_names)

    if not task_completed:
        return ""
    else:
        combined_responses = "\n".join(
            [f"{agent_name}:\n{review_agent.context_variables.get(f'{agent_name}_result')}\n\n---"
             for agent_name in redundant_agent_names]
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
            ContextExpression("len(${current_task}) > 0 and (len(${agent_a_result}) == 0 or len(${agent_b_result}) == 0 or len(${agent_c_result}) == 0)")
        )
    ),
    OnContextCondition(
        target=AgentNameTarget("vote_agent"),
        condition=ExpressionContextCondition(
            ContextExpression("len(${current_task}) > 0 and len(${agent_a_result}) != 0 and len(${agent_b_result}) != 0 and len(${agent_c_result}) != 0")
        )
    )
])

vote_agent.handoffs.set_after_work(AgentNameTarget("plan_agent"))

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
    max_rounds=100,
)

print("\n=== Chat Result ===")
print(chat_result)
print("\n=== Final Context ===")
print(final_context)
print("\n=== Last Agent ===")
print(last_agent)
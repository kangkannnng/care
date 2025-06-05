from autogen.agentchat.group.patterns import AutoPattern
from autogen.agentchat import initiate_group_chat

from agent import (
    log_agent, metric_agent, trace_agent, report_agent,
    review_agent, vote_agent, reviewers, user_proxy
)
from autogen.agentchat.group import NestedChatTarget, AgentTarget, OnContextCondition, ExpressionContextCondition, ContextExpression, ExpressionAvailableCondition, RevertToUserTarget, ContextVariables

from prompt import plan_agent_prompt
from agent import llm_config
# 共识上下文
review_context = ContextVariables(data={
    "task_initiated": False,
    "task_completed": False,
    "evaluation_complete": False,
    "current_task": "",
    "votes": [],
    "approve_count": 0,
    "reject_count": 0,
    "final_result": None
})


# 嵌套聊天配置
def setup_review_handoffs():
    nested_queue = []
    def extract_task(agent, messages, sender, config):
        return review_context.get("current_task") or ""

    def record_vote(sender, recipient, summary_args):
        vote = recipient.chat_messages[sender][-1]["content"].strip().upper()
        votes = review_context.get("votes") or []
        votes.append(vote)
        review_context.set("votes", votes)
        if len(votes) == len(reviewers):
            review_context.set("task_completed", True)
        return ""

    for reviewer in reviewers:
        nested_queue.append({
            "recipient": reviewer,
            "message": extract_task,
            "max_turns": 1,
            "summary_method": record_vote
        })

    review_agent.handoffs.clear()
    review_agent.handoffs.add_context_conditions([
        OnContextCondition(
            target=NestedChatTarget(nested_chat_config={"chat_queue": nested_queue}),
            condition=ExpressionContextCondition(ContextExpression("len(${votes}) < 3")),
            available=ExpressionAvailableCondition(ContextExpression("${task_initiated} == True and ${evaluation_complete} == False"))
        ),
        OnContextCondition(
            target=AgentTarget(vote_agent),
            condition=ExpressionContextCondition(ContextExpression("${task_completed} == True and ${evaluation_complete} == False")),
            available=ExpressionAvailableCondition(ContextExpression("${task_initiated} == True"))
        ),
    ])
    review_agent.handoffs.set_after_work(RevertToUserTarget())
    vote_agent.handoffs.set_after_work(RevertToUserTarget())


# 主入口
def run_workflow():
    # 每次运行时重新配置共识部分的逻辑
    setup_review_handoffs()
    agents = [
        log_agent,
        review_agent,
        vote_agent,
        metric_agent,
        trace_agent,
        report_agent
    ]
    pattern = AutoPattern(
        initial_agent=log_agent,
        agents=agents,
        context_variables=review_context,
        user_agent=user_proxy,
        group_manager_args={
            "llm_config": llm_config,
            "name": "任务规划师",
            "description": "负责整个多智能体工作流的群组管理和任务调度",
            "system_message": plan_agent_prompt},
    )
    prompt = "开始根因分析，案例ID: 1"
    result, ctx, last = initiate_group_chat(pattern=pattern, messages=prompt)
    print("最终报告:", result.summary)
    
if __name__ == "__main__":
    run_workflow()
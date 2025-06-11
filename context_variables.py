from autogen.agentchat.group import ContextVariables

# 状态管理上下文
context_variables = ContextVariables(data={
    # 工作流阶段：planning->log_analysis->log_consensus->metric_analysis->metric_consensus->trace_analysis->trace_consensus->final_report
    "workflow_stage": "planning",

    # 各阶段的分析结果
    "plan_result": "",
    "log_analysis_result": "",
    "metric_analysis_result": "",
    "trace_analysis_result": "",

    # 投票相关变量
    "current_task": "",
    "agent_a_result": "",
    "agent_b_result": "",
    "agent_c_result": "",
    "consensus_votes": [],
    "approve_count": 0,
    "reject_count": 0,
    "final_result": "",

    # 最终结果
    "final_log_analysis_result": "",
    "final_metric_analysis_result": "",
    "final_trace_analysis_result": "",
    "final_report": ""
})
from autogen.agentchat.contrib.swarm_agent import (
    initiate_swarm_chat,
    register_hand_off,
    OnContextCondition,
    ContextExpression,
    AfterWork,
    AfterWorkOption
)

from autogen.agentchat.group import (
    ContextExpression,
    ContextStr,
)
from agent import (
    llm_config, log_agent, metric_agent, trace_agent, report_agent,
    review_agent, vote_agent, reviewers, user_proxy,
    plan_agent
)

# 状态管理上下文 - 添加到共享上下文中 
context_variables = {  
    # 工作流状态  
    "workflow_stage": "planning",  
    "current_analysis_agent": None,  
      
    # 使用布尔标志替代列表  
    "log_analysis_completed": False,  
    "metric_analysis_completed": False,   
    "trace_analysis_completed": False,  
      
    # 共识机制状态  
    "consensus_needed": False,  
    "consensus_task": "",  
    "consensus_votes": [],  
    "consensus_result": None,  
    "approved_conclusions": [],  
      
    # 分析结果存储  
    "log_analysis_result": None,  
    "metric_analysis_result": None,   
    "trace_analysis_result": None,  
    "final_report": None  
}   
  
def setup_workflow_handoffs():  
    """配置所有智能体的条件转换"""  
      
    # Plan Agent: 启动后转到第一个分析智能体  
    register_hand_off(  
        agent=plan_agent,  
        hand_to=[  
            OnContextCondition(  
                target=log_agent,  
                condition=ContextExpression("${workflow_stage} == 'planning'"),  
                available=ContextExpression("${workflow_stage} == 'planning'")  
            ),  
            AfterWork(AfterWorkOption.STAY)  
        ]  
    )  
      
    # Log Agent: 完成分析后触发共识  
    register_hand_off(  
        agent=log_agent,  
        hand_to=[  
            OnContextCondition(  
                target=review_agent,  
                condition=ContextExpression("${workflow_stage} == 'log_analysis' and ${consensus_needed} == True"),  
                available=ContextExpression("${workflow_stage} == 'log_analysis'")  
            ),  
            AfterWork(AfterWorkOption.STAY)  
        ]  
    )  
      
    # Metric Agent: 完成分析后触发共识  
    register_hand_off(  
        agent=metric_agent,  
        hand_to=[  
            OnContextCondition(  
                target=review_agent,  
                condition=ContextExpression("${workflow_stage} == 'metric_analysis' and ${consensus_needed} == True"),  
                available=ContextExpression("${workflow_stage} == 'metric_analysis'")  
            ),  
            AfterWork(AfterWorkOption.STAY)  
        ]  
    )  
      
    # Trace Agent: 完成分析后触发共识  
    register_hand_off(  
        agent=trace_agent,  
        hand_to=[  
            OnContextCondition(  
                target=review_agent,  
                condition=ContextExpression("${workflow_stage} == 'trace_analysis' and ${consensus_needed} == True"),  
                available=ContextExpression("${workflow_stage} == 'trace_analysis'")  
            ),  
            AfterWork(AfterWorkOption.STAY)  
        ]  
    )  
      
    # Review Agent: 收集投票后转到投票统计  
    register_hand_off(  
        agent=review_agent,  
        hand_to=[  
            OnContextCondition(  
                target=vote_agent,  
                condition=ContextExpression("len(${consensus_votes}) >= 3"),
                available=ContextExpression("(${workflow_stage} == 'log_analysis' or ${workflow_stage} == 'metric_analysis' or ${workflow_stage} == 'trace_analysis') and ${consensus_needed} == True")  
            ),  
            AfterWork(AfterWorkOption.STAY)  
        ]  
    )  
      
    # Vote Agent: 统计投票后决定下一步  
    register_hand_off(  
        agent=vote_agent,  
        hand_to=[  
            # 如果还有分析未完成，转到下一个分析智能体  
            OnContextCondition(  
                target=metric_agent,  
                condition=ContextExpression("${log_analysis_completed} == True and ${metric_analysis_completed} == False"),  
                available=ContextExpression("${consensus_result} == 'approved'")  
            ),  
            OnContextCondition(  
                target=trace_agent,  
                condition=ContextExpression("${metric_analysis_completed} == True and ${trace_analysis_completed} == False"),  
                available=ContextExpression("${consensus_result} == 'approved'")  
            ),  
            # 如果所有分析都完成，转到报告生成  
            OnContextCondition(  
                target=report_agent,  
                condition=ContextExpression("${log_analysis_completed} == True and ${metric_analysis_completed} == True and ${trace_analysis_completed} == True"),  
                available=ContextExpression("${consensus_result} == 'approved'")  
            ),  
            AfterWork(AfterWorkOption.STAY)  
        ]  
    )
      
    # Report Agent: 生成最终报告后结束  
    register_hand_off(  
        agent=report_agent,  
        hand_to=[  
            AfterWork(AfterWorkOption.TERMINATE)  
        ]  
    )  
  
def create_analysis_functions():  
    """为分析智能体创建状态更新函数"""  
      
    def update_workflow_stage(agent_name: str, result: str):  
        """更新工作流状态的辅助函数"""  
        def _update_stage(context_variables: dict):  
            context_variables["current_analysis_agent"] = agent_name  
            context_variables["consensus_needed"] = True  
            context_variables["consensus_task"] = f"评估{agent_name}的分析结果: {result}"  
            context_variables[f"{agent_name.lower()}_analysis_result"] = result  
            return context_variables  
        return _update_stage  
      
    # 为每个分析智能体添加结果更新函数  
    # 这些函数需要在智能体完成分析后调用来更新上下文  
      
def create_consensus_functions():  
    """为共识智能体创建投票函数"""  
      
    def collect_vote(reviewer_name: str, vote: str):  
        """收集投票的函数"""  
        def _collect_vote(context_variables: dict):  
            votes = context_variables.get("consensus_votes", [])  
            votes.append({"reviewer": reviewer_name, "vote": vote})  
            context_variables["consensus_votes"] = votes  
            return context_variables  
        return _collect_vote  
      
    def finalize_consensus():  
        """统计投票结果的函数"""  
        def _finalize(context_variables: dict):  
            votes = context_variables.get("consensus_votes", [])  
            approve_count = sum(1 for v in votes if v["vote"].upper() in ["APPROVE", "同意"])  
            
            if approve_count >= 2:  # 2/3通过  
                context_variables["consensus_result"] = "approved"  
                # 根据当前阶段标记对应分析为完成  
                current_stage = context_variables["workflow_stage"]  
                if current_stage == "log_analysis":  
                    context_variables["log_analysis_completed"] = True  
                elif current_stage == "metric_analysis":  
                    context_variables["metric_analysis_completed"] = True  
                elif current_stage == "trace_analysis":  
                    context_variables["trace_analysis_completed"] = True  
                    
                # 将分析结果添加到已批准结论中  
                result_key = f"{current_stage}_result"  
                if result_key in context_variables:  
                    context_variables["approved_conclusions"].append(context_variables[result_key])  
            else:  
                context_variables["consensus_result"] = "rejected"  
            
            # 重置投票状态  
            context_variables["consensus_votes"] = []  
            context_variables["consensus_needed"] = False  
            
            # 更新工作流阶段  
            if not context_variables["log_analysis_completed"]:  
                context_variables["workflow_stage"] = "log_analysis"  
            elif not context_variables["metric_analysis_completed"]:  
                context_variables["workflow_stage"] = "metric_analysis"  
            elif not context_variables["trace_analysis_completed"]:  
                context_variables["workflow_stage"] = "trace_analysis"  
            else:  
                context_variables["workflow_stage"] = "reporting"  
                
            return context_variables  
        return _finalize
  
def run_workflow():  
    """主工作流入口"""  
      
    # 设置智能体转换条件  
    setup_workflow_handoffs()  
      
    # 创建辅助函数  
    create_analysis_functions()  
    create_consensus_functions()  
      
    # 智能体列表  
    agents = [  
        plan_agent,  
        log_agent,  
        metric_agent,   
        trace_agent,  
        review_agent,  
        vote_agent,  
        report_agent  
    ]  
      
    # 启动Swarm聊天  
    chat_result, final_context, last_speaker = initiate_swarm_chat(  
        initial_agent=plan_agent,  
        agents=agents,  
        context_variables=context_variables,  
        messages="开始根因分析，案例ID: 1",  
        user_agent=user_proxy,  
        max_rounds=50,  # 设置最大轮数防止无限循环  
        after_work=AfterWorkOption.TERMINATE  
    )  
      
    print("最终报告:", final_context.get("final_report", "未生成报告"))  
    print("工作流状态:", final_context.get("workflow_stage", "未知"))  
    print("已批准的结论:", final_context.get("approved_conclusions", []))  
      
    return chat_result, final_context  
  
if __name__ == "__main__":  
    run_workflow()
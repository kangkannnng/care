import os
import pandas as pd
from typing import Dict, Any, Annotated
from config import dataset_path
from context_variables import context_variables
from autogen.agentchat.group import ContextVariables, ReplyResult, RevertToUserTarget
from typing import List, Annotated
from autogen import ConversableAgent
from autogen.agentchat.group.targets.transition_target import AgentNameTarget, RevertToUserTarget, NestedChatTarget

def provide_analysis_plan(
        analysis_plan: Annotated[str, "分析计划内容"],
        context_variables: ContextVariables
) -> ReplyResult:
    """
    提供日志分析计划
    """
    context_variables['workflow_stage'] = 'planning'
    context_variables['plan_result'] = analysis_plan
    return ReplyResult(
        message=f"分析计划已提供: {analysis_plan}",
        context_variables=context_variables
    )

def route_to_agent(
        context_variables: ContextVariables
) -> ReplyResult:
    """
    路由到具体分析代理
    """
    if context_variables["workflow_stage"] == "planning":
        return ReplyResult(
            message="已完成工作流规划，请继续进行日志分析。",
            target=AgentNameTarget("log_agent")
        )
    elif context_variables["workflow_stage"] == "log_consensus":
        return ReplyResult(
            message="已完成日志分析，请继续进行系统指标分析。",
            target=AgentNameTarget("metric_agent")
        )
    elif context_variables["workflow_stage"] == "metric_consensus":
        return ReplyResult(
            message="已完成系统指标分析，请继续进行调用链分析。",
            target=AgentNameTarget("trace_agent")
        )
    elif context_variables["workflow_stage"] == "trace_consensus":
        return ReplyResult(
            message="已完成调用链分析，请继续进行最终报告生成。",
            target=AgentNameTarget("report_agent")
        )
    elif context_variables["workflow_stage"] == "final_report":
        return ReplyResult(
            message="已完成最终报告生成，分析结束。",
            target=RevertToUserTarget()
        )
    else:
        return ReplyResult(
            message="当前工作流阶段不明确，请检查上下文变量。",
            target=RevertToUserTarget()
        )

def get_log(case_id: Annotated[str, "案例ID，如 '1', '2', '3'"]) -> ReplyResult:
    """
    获取指定案例的日志数据
    """
    # 构建数据文件路径
    base_path = dataset_path
    case_path = os.path.join(base_path, f"case_{case_id}")
    logs_file = os.path.join(case_path, "logs.csv")
    
    if not os.path.exists(logs_file):
        return {"error": f"找不到案例{case_id}的日志文件"}
    
    # 读取日志数据
    df = pd.read_csv(logs_file)
    
    # 转换时间戳
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    # 基础统计信息
    total_logs = len(df)
    services = df['service'].unique()
    log_levels = df['level'].value_counts().to_dict()
    
    # 异常检测
    error_logs = df[df['level'] == 'ERROR']
    warn_logs = df[df['level'] == 'WARN']
    
    anomalies = {
        "error_count": len(error_logs),
        "warn_count": len(warn_logs),
        "error_services": error_logs['service'].unique().tolist() if len(error_logs) > 0 else [],
        "warn_services": warn_logs['service'].unique().tolist() if len(warn_logs) > 0 else [],
        "error_time_range": {
            "start": error_logs['datetime'].min() if len(error_logs) > 0 else None,
            "end": error_logs['datetime'].max() if len(error_logs) > 0 else None
        }
    }
    
    # 时间线分析
    df['time_bucket'] = df['datetime'].dt.floor('5s')
    timeline = df.groupby(['time_bucket', 'level']).size().unstack(fill_value=0)
    
    if 'ERROR' in timeline.columns:
        error_timeline = timeline['ERROR']
        mean_errors = error_timeline.mean()
        std_errors = error_timeline.std()
        anomaly_threshold = mean_errors + 2 * std_errors
        
        anomaly_periods = timeline[timeline['ERROR'] > anomaly_threshold]
        
        timeline_analysis = {
            'total_periods': len(timeline),
            'anomaly_periods': len(anomaly_periods),
            'peak_error_time': error_timeline.idxmax() if len(error_timeline) > 0 else None,
            'peak_error_count': error_timeline.max() if len(error_timeline) > 0 else 0
        }
    else:
        timeline_analysis = {'total_periods': len(timeline), 'anomaly_periods': 0}
    
    # 服务级别分析
    service_analysis = {}
    for service in services:
        service_logs = df[df['service'] == service]
        service_errors = service_logs[service_logs['level'] == 'ERROR']
        service_analysis[service] = {
            "total_logs": len(service_logs),
            "error_logs": len(service_errors),
            "error_time_range": {
                "start": service_errors['datetime'].min() if len(service_errors) > 0 else None,
                "end": service_errors['datetime'].max() if len(service_errors) > 0 else None
            }
        }
    
    return ReplyResult(
        message=f"案例 {case_id} 的日志信息如下：\n"
                f"总日志数：{total_logs}\n"
                f"服务数量：{len(services)}\n"
                f"日志级别分布：{log_levels}\n"
                f"异常检测：{anomalies}\n"
                f"时间线分析：{timeline_analysis}\n"
                f"服务级别分析：{service_analysis}"
    )
    
def provide_log_result(
    analysis_result: Annotated[str, "日志分析结果"],
    context_variables: ContextVariables
) -> ReplyResult:
    """
    提供日志分析结果，并更新上下文变量
    """
    # 更新上下文变量
    context_variables["log_analysis_result"] = analysis_result
    context_variables["workflow_stage"] = "log_analysis"
    
    return ReplyResult(
        message=f"日志分析结果已保存：{analysis_result}",
        context_variables=context_variables,
        target=AgentNameTarget("review_agent")
    )


def get_trace(case_id: Annotated[str, "案例ID，如 '1', '2', '3'"]) -> ReplyResult:
    """
    获取指定案例的系统指标数据
    """
    # 构建数据文件路径
    base_path = dataset_path
    case_path = os.path.join(base_path, f"case_{case_id}")
    traces_file = os.path.join(case_path, "traces.csv")
    
    if not os.path.exists(traces_file):
        return ReplyResult(message=f"找不到案例{case_id}的调用链文件")
    
    # 读取调用链数据
    df = pd.read_csv(traces_file)
    
    # 转换时间戳
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('datetime')
    
    # 基础统计信息
    total_spans = len(df)
    trace_count = df['trace_id'].nunique()
    time_range = {
        "开始时间": df['datetime'].min(),
        "结束时间": df['datetime'].max(),
        "持续时间（秒）": (df['datetime'].max() - df['datetime'].min()).total_seconds()
    }
    
    # 服务和操作类型
    services = df['service'].unique().tolist()
    operations = df['operation'].unique().tolist()
    
    # 性能统计
    duration_stats = {
        "平均耗时": df['duration'].mean(),
        "最大耗时": df['duration'].max(),
        "最小耗时": df['duration'].min(),
        "标准差": df['duration'].std(),
        "P90": df['duration'].quantile(0.9),
        "P95": df['duration'].quantile(0.95)
    }
    
    # 服务级别性能分析
    service_analysis = df.groupby('service')['duration'].agg(['count', 'mean', 'max', 'std']).round(2).to_dict('index')
    
    # trace模式分析
    trace_spans = df.groupby('trace_id').size()
    trace_analysis = {
        "平均调用链跨度": trace_spans.mean(),
        "最大调用链跨度": trace_spans.max(),
        "最小调用链跨度": trace_spans.min()
    }
    
    return ReplyResult(
        message=f"案例 {case_id} 的调用链信息如下：\n"
                f"总跨度数：{total_spans}\n"
                f"调用链数量：{trace_count}\n"
                f"时间范围：{time_range}\n"
                f"服务列表：{services}\n"
                f"操作类型：{operations}\n"
                f"性能统计：{duration_stats}\n"
                f"服务级别分析：{service_analysis}\n"
                f"调用链分析：{trace_analysis}"
    )

def provide_trace_result(
    analysis_result: Annotated[str, "指标分析结果"],
    context_variables: ContextVariables
) -> ReplyResult:
    """
    提供调用链分析结果，并更新上下文变量
    """
    # 更新上下文变量
    context_variables["trace_analysis_result"] = analysis_result
    context_variables["workflow_stage"] = "trace_analysis"
    
    return ReplyResult(
        message=f"调用链分析结果已保存：{analysis_result}",
        context_variables=context_variables,
        target=AgentNameTarget("review_agent")
    )


def get_metric(case_id: Annotated[str, "案例ID，如 '1', '2', '3'"]) -> ReplyResult:
    """
    获取指定案例的系统指标数据
    """
    # 构建数据文件路径
    base_path = dataset_path
    case_path = os.path.join(base_path, f"case_{case_id}")
    metrics_file = os.path.join(case_path, "metrics.csv")
    
    if not os.path.exists(metrics_file):
        return ReplyResult(message=f"找不到案例{case_id}的指标文件")
    
    # 读取指标数据
    df = pd.read_csv(metrics_file)
    
    # 转换时间戳
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('datetime')
    
    # 提取服务名称和指标类型
    services = []
    metric_types = ['cpu', 'mem', 'latency']
    
    for col in df.columns:
        if any(metric in col for metric in metric_types):
            service = col.split('_')[0]
            if service not in services:
                services.append(service)
    
    # 基础统计信息
    total_data_points = len(df)
    time_range = {
        "开始时间": df['datetime'].min(),
        "结束时间": df['datetime'].max(),
        "持续时间（秒）": round((df['datetime'].max() - df['datetime'].min()).total_seconds(), 2)
    }
    
    # 服务指标分析
    service_analysis = {}
    for service in services:
        cpu_col = f"{service}_cpu"
        mem_col = f"{service}_mem"
        latency_col = f"{service}_latency"
        
        service_analysis[service] = {}
        
        # CPU分析
        if cpu_col in df.columns:
            cpu_data = df[cpu_col]
            service_analysis[service]['CPU'] = {
                '平均值': round(float(cpu_data.mean()), 2),
                '最大值': round(float(cpu_data.max()), 2),
                '最小值': round(float(cpu_data.min()), 2),
                '标准差': round(float(cpu_data.std()), 2),
                'P95': round(float(cpu_data.quantile(0.95)), 2),
                '异常值': [round(float(value), 2) for value in cpu_data[cpu_data > cpu_data.mean() + 2 * cpu_data.std()]]
            }
        
        # 内存分析
        if mem_col in df.columns:
            mem_data = df[mem_col]
            service_analysis[service]['内存'] = {
                '平均值': round(float(mem_data.mean()), 2),
                '最大值': round(float(mem_data.max()), 2),
                '最小值': round(float(mem_data.min()), 2),
                '标准差': round(float(mem_data.std()), 2),
                'P95': round(float(mem_data.quantile(0.95)), 2),
                '异常值': [round(float(value), 2) for value in mem_data[mem_data > mem_data.mean() + 2 * mem_data.std()]]
            }
        
        # 延迟分析
        if latency_col in df.columns:
            latency_data = df[latency_col]
            service_analysis[service]['延迟'] = {
                '平均值': round(float(latency_data.mean()), 2),
                '最大值': round(float(latency_data.max()), 2),
                '最小值': round(float(latency_data.min()), 2),
                '标准差': round(float(latency_data.std()), 2),
                'P95': round(float(latency_data.quantile(0.95)), 2),
                '异常值': [round(float(value), 2) for value in latency_data[latency_data > latency_data.mean() + 2 * latency_data.std()]]
            }
    
    # 趋势分析：计算时间序列中的高峰期
    peak_analysis = {}
    for service in services:
        cpu_col = f"{service}_cpu"
        if cpu_col in df.columns:
            peak_times = df[df[cpu_col] > df[cpu_col].mean() + 2 * df[cpu_col].std()]['datetime'].tolist()
            peak_analysis[service] = {
                "高峰时间": peak_times,
                "高峰次数": len(peak_times)
            }
    
    return ReplyResult(
        message=f"案例 {case_id} 的系统指标信息如下：\n"
                f"总数据点数：{total_data_points}\n"
                f"时间范围：{time_range}\n"
                f"服务列表：{services}\n"
                f"服务指标分析：{service_analysis}\n"
                f"趋势分析：{peak_analysis}"
    )

def provide_metric_result(
    analysis_result: Annotated[str, "指标分析结果"],
    context_variables: ContextVariables
) -> ReplyResult:
    """
    提供系统指标分析结果，并更新上下文变量
    """
    # 更新上下文变量
    context_variables["metric_analysis_result"] = analysis_result
    context_variables["workflow_stage"] = "metric_analysis"
    
    return ReplyResult(
        message=f"系统指标分析结果已保存：{analysis_result}",
        context_variables=context_variables,
        target=AgentNameTarget("review_agent")
    )


def prepare_vote(context_variables: ContextVariables) -> ReplyResult:
    """
    准备投票任务，初始化上下文变量
    """
    # 直接从analysis_result获取任务内容
    if context_variables["workflow_stage"] == "log_analysis":
        task = context_variables.get("log_analysis_result", "无日志分析结果")
    elif context_variables["workflow_stage"] == "metric_analysis":
        task = context_variables.get("metric_analysis_result", "无系统指标分析结果")
    elif context_variables["workflow_stage"] == "trace_analysis":
        task = context_variables.get("trace_analysis_result", "无调用链分析结果")
    

    context_variables["current_task"] = task
    context_variables["agent_a_result"] = ""
    context_variables["agent_b_result"] = ""
    context_variables["agent_c_result"] = ""
    context_variables["consensus_votes"] = []
    context_variables["approve_count"] = 0
    context_variables["reject_count"] = 0
    context_variables["final_result"] = ""

    return ReplyResult(
        message=f"任务初始化完毕：{task}",
        context_variables=context_variables,
    )


def complete_vote(votes: List[str], context_variables: ContextVariables) -> ReplyResult:
    """
    完成投票统计，根据结果更新上下文变量
    """
    try:
        # 更新投票结果
        context_variables["consensus_votes"] = votes
        
        # 统计投票结果
        approve_count = sum(1 for v in votes if v.upper() == "APPROVE")
        reject_count = sum(1 for v in votes if v.upper() == "REJECT")
        passed = approve_count >= 2
        
        # 更新投票相关变量
        context_variables["approve_count"] = approve_count
        context_variables["reject_count"] = reject_count
        context_variables["final_result"] = "APPROVE" if passed else "REJECT"
        
        # 如果通过，保存当前分析结果
        if passed:
            if context_variables.get("log_analysis_result"):
                context_variables["final_log_analysis_result"] = context_variables["log_analysis_result"]
                context_variables["workflow_stage"] = "log_consensus"
            if context_variables.get("metric_analysis_result"):
                context_variables["final_metric_analysis_result"] = context_variables["metric_analysis_result"]
                context_variables["workflow_stage"] = "metric_consensus"
            if context_variables.get("trace_analysis_result"):
                context_variables["final_trace_analysis_result"] = context_variables["trace_analysis_result"]
                context_variables["workflow_stage"] = "trace_consensus"
        
        context_variables["current_task"] = ""
        context_variables["agent_a_result"] = ""
        context_variables["agent_b_result"] = ""
        context_variables["agent_c_result"] = ""
        context_variables["consensus_votes"] = []
        context_variables["approve_count"] = 0
        context_variables["reject_count"] = 0
        context_variables["final_result"] = ""
        
        return ReplyResult(
            message=f"投票统计结果：\n- 赞成票数：{approve_count}\n- 反对票数：{reject_count}\n- 最终结果：{'通过' if passed else '不通过'}",
            context_variables=context_variables
        )
    except Exception as e:
        return ReplyResult(
            message=f"投票统计出错: {str(e)}",
            context_variables=context_variables
        )
    
def provide_final_report(
    final_report: Annotated[str, "最终分析报告"],
    context_variables: ContextVariables
) -> ReplyResult:
    """
    提供最终分析报告，并更新上下文变量
    """
    # 更新上下文变量
    context_variables["final_report"] = final_report
    context_variables["workflow_stage"] = "final_report"
    
    return ReplyResult(
        message=f"最终分析报告已生成：{final_report}",
        context_variables=context_variables,
        target=RevertToUserTarget()
    )
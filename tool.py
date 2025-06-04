import os
import pandas as pd
from typing import Dict, Any, Annotated
from config import dataset_path

def analyze_logs(case_id: Annotated[str, "案例ID，如 '1', '2', '3'"]) -> Dict[str, Any]:
    """
    分析指定案例的日志数据，检测异常并提供全面信息
    
    Args:
        case_id: 案例ID，如 "1", "2", "3"
        
    Returns:
        包含日志分析信息的字典
    """
    try:
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
        
        return {
            "log_summary": f"Summary for logs in case {case_id}",
            "total_logs": total_logs,
            "services": services.tolist(),
            "log_levels": log_levels,
            "anomalies": anomalies,
            "timeline_analysis": timeline_analysis,
            "service_analysis": service_analysis
        }
        
    except Exception as e:
        return {"error": f"日志分析过程中发生错误：{str(e)}"}

def analyze_traces(case_id: Annotated[str, "案例ID，如 '1', '2', '3'"]) -> Dict[str, Any]:
    """
    分析指定案例的调用链数据，检测性能瓶颈和异常调用
    
    Args:
        case_id: 案例ID，如 "1", "2", "3"
        
    Returns:
        包含调用链分析信息的字典
    """
    try:
        # 构建数据文件路径
        base_path = dataset_path
        case_path = os.path.join(base_path, f"case_{case_id}")
        traces_file = os.path.join(case_path, "traces.csv")
        
        if not os.path.exists(traces_file):
            return {"error": f"找不到案例{case_id}的调用链文件"}
        
        # 读取调用链数据
        df = pd.read_csv(traces_file)
        
        # 转换时间戳
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values('datetime')
        
        # 基础统计信息
        total_spans = len(df)
        trace_count = df['trace_id'].nunique()
        time_range = {
            "start": df['datetime'].min(),
            "end": df['datetime'].max(),
            "duration_seconds": (df['datetime'].max() - df['datetime'].min()).total_seconds()
        }
        
        # 服务和操作类型
        services = df['service'].unique().tolist()
        operations = df['operation'].unique().tolist()
        
        # 性能统计
        duration_stats = {
            "mean": df['duration'].mean(),
            "max": df['duration'].max(),
            "min": df['duration'].min(),
            "std": df['duration'].std(),
            "p90": df['duration'].quantile(0.9),
            "p95": df['duration'].quantile(0.95)
        }
        
        # 服务级别性能分析
        service_analysis = df.groupby('service')['duration'].agg(['count', 'mean', 'max', 'std']).round(2).to_dict('index')
        
        # trace模式分析
        trace_spans = df.groupby('trace_id').size()
        trace_analysis = {
            "avg_spans_per_trace": trace_spans.mean(),
            "max_spans_per_trace": trace_spans.max(),
            "min_spans_per_trace": trace_spans.min()
        }
        
        return {
            "trace_summary": f"Summary for traces in case {case_id}",
            "total_spans": total_spans,
            "trace_count": trace_count,
            "time_range": time_range,
            "services": services,
            "operations": operations,
            "duration_stats": duration_stats,
            "service_analysis": service_analysis,
            "trace_analysis": trace_analysis
        }
        
    except Exception as e:
        return {"error": f"调用链分析过程中发生错误：{str(e)}"}

def analyze_metrics(case_id: Annotated[str, "案例ID，如 '1', '2', '3'"]) -> Dict[str, Any]:
    """
    分析指定案例的系统指标数据，检测资源异常和性能问题
    
    Args:
        case_id: 案例ID，如 "1", "2", "3"
        
    Returns:
        包含系统指标分析信息的字典
    """
    try:
        # 构建数据文件路径
        base_path = dataset_path
        case_path = os.path.join(base_path, f"case_{case_id}")
        metrics_file = os.path.join(case_path, "metrics.csv")
        
        if not os.path.exists(metrics_file):
            return {"error": f"找不到案例{case_id}的指标文件"}
        
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
            "start": df['datetime'].min(),
            "end": df['datetime'].max(),
            "duration_seconds": round((df['datetime'].max() - df['datetime'].min()).total_seconds(), 2)
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
                service_analysis[service]['cpu'] = {
                    'mean': round(float(cpu_data.mean()), 2),
                    'max': round(float(cpu_data.max()), 2),
                    'min': round(float(cpu_data.min()), 2),
                    'std': round(float(cpu_data.std()), 2),
                    'p95': round(float(cpu_data.quantile(0.95)), 2),
                    'anomalies': [round(float(value), 2) for value in cpu_data[cpu_data > cpu_data.mean() + 2 * cpu_data.std()]]
                }
            
            # 内存分析
            if mem_col in df.columns:
                mem_data = df[mem_col]
                service_analysis[service]['mem'] = {
                    'mean': round(float(mem_data.mean()), 2),
                    'max': round(float(mem_data.max()), 2),
                    'min': round(float(mem_data.min()), 2),
                    'std': round(float(mem_data.std()), 2),
                    'p95': round(float(mem_data.quantile(0.95)), 2),
                    'anomalies': [round(float(value), 2) for value in mem_data[mem_data > mem_data.mean() + 2 * mem_data.std()]]
                }
            
            # 延迟分析
            if latency_col in df.columns:
                latency_data = df[latency_col]
                service_analysis[service]['latency'] = {
                    'mean': round(float(latency_data.mean()), 2),
                    'max': round(float(latency_data.max()), 2),
                    'min': round(float(latency_data.min()), 2),
                    'std': round(float(latency_data.std()), 2),
                    'p95': round(float(latency_data.quantile(0.95)), 2),
                    'anomalies': [round(float(value), 2) for value in latency_data[latency_data > latency_data.mean() + 2 * latency_data.std()]]
                }
        
        # 趋势分析：计算时间序列中的高峰期
        peak_analysis = {}
        for service in services:
            cpu_col = f"{service}_cpu"
            if cpu_col in df.columns:
                peak_times = df[df[cpu_col] > df[cpu_col].mean() + 2 * df[cpu_col].std()]['datetime'].tolist()
                peak_analysis[service] = {
                    "peak_times": peak_times,
                    "peak_count": len(peak_times)
                }
        
        return {
            "metric_summary": f"Summary for metrics in case {case_id}",
            "total_data_points": total_data_points,
            "time_range": time_range,
            "services": services,
            "service_analysis": service_analysis,
            "peak_analysis": peak_analysis
        }
        
    except Exception as e:
        return {"error": f"指标分析过程中发生错误：{str(e)}"}
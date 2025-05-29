"""
调用链分析工具函数

提供调用链数据的读取、分析和性能瓶颈检测功能
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np


def analyze_traces(case_id: str) -> str:
    """
    分析指定案例的调用链数据，检测性能瓶颈和异常调用
    
    Args:
        case_id: 案例ID，如 "1", "2", "3"
        
    Returns:
        分析结果的自然语言描述
    """
    try:
        # 构建数据文件路径
        base_path = "/home/kangkang/code/care/data"
        case_path = os.path.join(base_path, f"case_{case_id}")
        traces_file = os.path.join(case_path, "traces.csv")
        
        if not os.path.exists(traces_file):
            return f"错误：找不到案例{case_id}的调用链文件"
        
        # 读取调用链数据
        df = pd.read_csv(traces_file)
        
        # 转换时间戳
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values('datetime')
        
        # 基础统计
        total_spans = len(df)
        services = df['service'].unique()
        operations = df['operation'].unique()
        trace_count = df['trace_id'].nunique()
        
        analysis_result = f"""
=== 调用链分析报告 ===

1. 基础统计信息：
   - 总调用数：{total_spans}
   - 独立trace数：{trace_count}
   - 涉及服务：{', '.join(services)}
   - 操作类型：{', '.join(operations)}

2. 时间范围分析：
   - 开始时间：{df['datetime'].min()}
   - 结束时间：{df['datetime'].max()}
   - 时间跨度：{(df['datetime'].max() - df['datetime'].min()).total_seconds():.1f}秒

3. 性能分析："""
        
        # 性能统计
        duration_stats = df['duration'].describe()
        analysis_result += f"""
   - 平均调用时长：{duration_stats['mean']:.2f}ms
   - 最大调用时长：{duration_stats['max']:.2f}ms
   - 最小调用时长：{duration_stats['min']:.2f}ms
   - 90%分位数：{df['duration'].quantile(0.9):.2f}ms"""
        
        # 检测异常缓慢的调用
        p95_duration = df['duration'].quantile(0.95)
        slow_calls = df[df['duration'] > p95_duration]
        
        if len(slow_calls) > 0:
            analysis_result += f"""

4. 异常检测结果：
   - 发现 {len(slow_calls)} 次异常缓慢的调用（超过95%分位数：{p95_duration:.2f}ms）"""
            
            # 按服务分析慢调用
            slow_by_service = slow_calls['service'].value_counts()
            analysis_result += f"""
   - 慢调用分布："""
            for service, count in slow_by_service.items():
                avg_slow_duration = slow_calls[slow_calls['service'] == service]['duration'].mean()
                analysis_result += f"""
     * {service}服务：{count}次，平均时长{avg_slow_duration:.2f}ms"""
        
        # 服务级别性能分析
        analysis_result += """

5. 服务级别性能分析："""
        
        service_stats = df.groupby('service')['duration'].agg(['count', 'mean', 'max', 'std']).round(2)
        
        for service in services:
            stats = service_stats.loc[service]
            analysis_result += f"""
   - {service}服务：
     * 调用次数：{stats['count']}
     * 平均时长：{stats['mean']:.2f}ms
     * 最大时长：{stats['max']:.2f}ms
     * 时长标准差：{stats['std']:.2f}ms"""
            
            # 判断服务是否有性能问题
            if stats['max'] > 2 * stats['mean']:
                analysis_result += f" [异常：存在时长波动较大的调用]"
        
        # 调用链路分析
        analysis_result += """

6. 调用链路分析："""
        
        # 分析trace的完整性和调用模式
        trace_analysis = _analyze_trace_patterns(df)
        
        analysis_result += f"""
   - 平均每个trace的调用数：{trace_analysis['avg_spans_per_trace']:.1f}
   - 最大trace调用数：{trace_analysis['max_spans_per_trace']}
   - 最小trace调用数：{trace_analysis['min_spans_per_trace']}"""
        
        if trace_analysis['incomplete_traces'] > 0:
            analysis_result += f"""
   - 发现 {trace_analysis['incomplete_traces']} 个可能不完整的trace"""
        
        # 服务依赖分析
        dependencies = _analyze_service_dependencies(df)
        if dependencies:
            analysis_result += f"""
   - 服务调用关系：{dependencies}"""
        
        # 根因推理
        analysis_result += """

7. 根因分析推理："""
        
        # 找出性能最差的服务
        worst_performing_service = service_stats['mean'].idxmax()
        worst_avg_duration = service_stats.loc[worst_performing_service, 'mean']
        
        # 找出调用时长最不稳定的服务
        most_unstable_service = service_stats['std'].idxmax()
        most_unstable_std = service_stats.loc[most_unstable_service, 'std']
        
        analysis_result += f"""
   - 性能最差的服务：{worst_performing_service}（平均时长{worst_avg_duration:.2f}ms）
   - 最不稳定的服务：{most_unstable_service}（标准差{most_unstable_std:.2f}ms）"""
        
        # 根据异常检测结果推理
        if len(slow_calls) > 0:
            most_affected_service = slow_calls['service'].value_counts().index[0]
            analysis_result += f"""
   - {most_affected_service}服务出现了最多的异常缓慢调用
   - 这可能表明{most_affected_service}服务存在性能瓶颈或资源不足"""
            
            # 检查时间模式
            slow_calls_timeline = slow_calls['datetime'].dt.floor('10S').value_counts().sort_index()
            if len(slow_calls_timeline) > 0:
                peak_time = slow_calls_timeline.idxmax()
                analysis_result += f"""
   - 慢调用集中出现在：{peak_time}
   - 建议检查该时间段的资源使用情况"""
        
        analysis_result += """

8. 结论：
   基于调用链分析，建议重点关注性能最差和最不稳定的服务，检查其资源配置和依赖关系。"""
        
        return analysis_result
        
    except Exception as e:
        return f"调用链分析过程中发生错误：{str(e)}"


def _analyze_trace_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析trace的调用模式
    
    Args:
        df: 调用链DataFrame
        
    Returns:
        trace模式分析结果
    """
    trace_spans = df.groupby('trace_id').size()
    
    # 检测可能不完整的trace（调用数明显少于正常）
    avg_spans = trace_spans.mean()
    std_spans = trace_spans.std()
    threshold = avg_spans - std_spans
    incomplete_traces = len(trace_spans[trace_spans < threshold])
    
    return {
        'avg_spans_per_trace': avg_spans,
        'max_spans_per_trace': trace_spans.max(),
        'min_spans_per_trace': trace_spans.min(),
        'incomplete_traces': incomplete_traces
    }


def _analyze_service_dependencies(df: pd.DataFrame) -> str:
    """
    分析服务间的调用依赖关系
    
    Args:
        df: 调用链DataFrame
        
    Returns:
        依赖关系描述
    """
    try:
        # 通过parent_id分析调用关系
        dependencies = []
        
        for trace_id in df['trace_id'].unique():
            trace_data = df[df['trace_id'] == trace_id]
            
            # 找到根span（没有parent_id的）
            root_spans = trace_data[trace_data['parent_id'].isna() | (trace_data['parent_id'] == '')]
            if len(root_spans) > 0:
                root_service = root_spans.iloc[0]['service']
                
                # 找到被根服务调用的服务
                child_spans = trace_data[trace_data['parent_id'].notna() & (trace_data['parent_id'] != '')]
                if len(child_spans) > 0:
                    called_services = child_spans['service'].unique()
                    called_services = [s for s in called_services if s != root_service]
                    
                    if called_services:
                        dependency = f"{root_service} → {', '.join(called_services)}"
                        if dependency not in dependencies:
                            dependencies.append(dependency)
        
        return '; '.join(dependencies) if dependencies else "无明确依赖关系"
        
    except Exception:
        return "依赖关系分析失败"


def _detect_performance_anomalies(df: pd.DataFrame) -> Dict[str, Any]:
    """
    检测性能异常
    
    Args:
        df: 调用链DataFrame
        
    Returns:
        异常检测结果
    """
    anomalies = {
        'slow_services': [],
        'unstable_services': [],
        'timeout_services': []
    }
    
    # 按服务分组分析
    for service in df['service'].unique():
        service_data = df[df['service'] == service]
        durations = service_data['duration']
        
        # 检测缓慢服务（平均时长超过整体95%分位数）
        overall_p95 = df['duration'].quantile(0.95)
        if durations.mean() > overall_p95:
            anomalies['slow_services'].append(service)
        
        # 检测不稳定服务（标准差/均值 > 1）
        if durations.std() / durations.mean() > 1:
            anomalies['unstable_services'].append(service)
        
        # 检测可能的超时（存在明显的异常高值）
        if durations.max() > 3 * durations.mean():
            anomalies['timeout_services'].append(service)
    
    return anomalies

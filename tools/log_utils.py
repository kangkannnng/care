"""
日志分析工具函数

提供日志数据的读取、分析和异常检测功能
"""

import pandas as pd
import os
from datetime import datetime
import re
from typing import Dict, List, Any, Optional


def analyze_logs(case_id: str) -> str:
    """
    分析指定案例的日志数据，检测异常并进行根因分析
    
    Args:
        case_id: 案例ID，如 "1", "2", "3"
        
    Returns:
        分析结果的自然语言描述
    """
    try:
        # 构建数据文件路径
        base_path = "/home/kangkang/code/care/data"
        case_path = os.path.join(base_path, f"case_{case_id}")
        logs_file = os.path.join(case_path, "logs.csv")
        
        if not os.path.exists(logs_file):
            return f"错误：找不到案例{case_id}的日志文件"
        
        # 读取日志数据
        df = pd.read_csv(logs_file)
        
        # 转换时间戳
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values('datetime')
        
        # 基础统计
        total_logs = len(df)
        services = df['service'].unique()
        log_levels = df['level'].value_counts()
        
        analysis_result = f"""
=== 日志分析报告 ===

1. 基础统计信息：
   - 总日志条数：{total_logs}
   - 涉及服务：{', '.join(services)}
   - 日志级别分布：{dict(log_levels)}

2. 时间范围分析：
   - 开始时间：{df['datetime'].min()}
   - 结束时间：{df['datetime'].max()}
   - 时间跨度：{(df['datetime'].max() - df['datetime'].min()).total_seconds():.1f}秒

3. 异常检测结果："""
        
        # 检测ERROR和WARN级别的日志
        error_logs = df[df['level'] == 'ERROR']
        warn_logs = df[df['level'] == 'WARN']
        
        if len(error_logs) > 0:
            analysis_result += f"""
   - 发现 {len(error_logs)} 条ERROR级别日志
   - 涉及服务：{', '.join(error_logs['service'].unique())}
   - 错误时间段：{error_logs['datetime'].min()} 到 {error_logs['datetime'].max()}"""
            
            # 分析错误消息模式
            error_messages = error_logs['message'].tolist()
            common_errors = _extract_error_patterns(error_messages)
            if common_errors:
                analysis_result += f"""
   - 主要错误类型：{', '.join(common_errors)}"""
        
        if len(warn_logs) > 0:
            analysis_result += f"""
   - 发现 {len(warn_logs)} 条WARN级别日志
   - 涉及服务：{', '.join(warn_logs['service'].unique())}"""
        
        # 服务级别分析
        analysis_result += """

4. 服务级别分析："""
        
        for service in services:
            service_logs = df[df['service'] == service]
            service_errors = service_logs[service_logs['level'] == 'ERROR']
            
            analysis_result += f"""
   - {service}服务：共{len(service_logs)}条日志"""
            
            if len(service_errors) > 0:
                analysis_result += f"，其中{len(service_errors)}条ERROR"
                
                # 分析错误集中的时间段
                if len(service_errors) > 1:
                    time_diff = (service_errors['datetime'].max() - service_errors['datetime'].min()).total_seconds()
                    analysis_result += f"，错误集中在{time_diff:.1f}秒内"
        
        # 根因推理
        analysis_result += """

5. 根因分析推理："""
        
        if len(error_logs) > 0:
            # 找出错误最多的服务
            error_by_service = error_logs['service'].value_counts()
            most_error_service = error_by_service.index[0]
            most_error_count = error_by_service.iloc[0]
            
            analysis_result += f"""
   - 根据日志分析，{most_error_service}服务出现了最多的错误（{most_error_count}条）
   - 错误时间模式显示问题可能起始于：{error_logs['datetime'].min()}
   - 推测{most_error_service}服务可能是问题的根源或受影响最严重的组件"""
            
            # 检查错误是否有传播模式
            if len(error_by_service) > 1:
                analysis_result += f"""
   - 错误影响了多个服务：{', '.join(error_by_service.index.tolist())}
   - 这表明可能存在服务间的错误传播"""
        else:
            analysis_result += """
   - 未发现明显的ERROR级别日志
   - 需要结合其他数据源（如指标、调用链）进行进一步分析"""
        
        analysis_result += """

6. 结论：
   基于日志分析，建议重点关注错误较多的服务，并结合指标数据验证资源使用情况。"""
        
        return analysis_result
        
    except Exception as e:
        return f"日志分析过程中发生错误：{str(e)}"


def _extract_error_patterns(error_messages: List[str]) -> List[str]:
    """
    从错误消息中提取常见模式
    
    Args:
        error_messages: 错误消息列表
        
    Returns:
        常见错误类型列表
    """
    patterns = []
    
    for message in error_messages:
        message_lower = message.lower()
        
        if 'timeout' in message_lower or 'time out' in message_lower:
            if 'timeout' not in patterns:
                patterns.append('timeout')
        elif 'connection' in message_lower and ('refuse' in message_lower or 'fail' in message_lower):
            if 'connection_error' not in patterns:
                patterns.append('connection_error')
        elif 'memory' in message_lower or 'oom' in message_lower:
            if 'memory_error' not in patterns:
                patterns.append('memory_error')
        elif 'cpu' in message_lower and 'high' in message_lower:
            if 'cpu_high' not in patterns:
                patterns.append('cpu_high')
        elif '500' in message or 'internal server error' in message_lower:
            if 'server_error' not in patterns:
                patterns.append('server_error')
    
    return patterns


def _analyze_log_timeline(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析日志的时间线模式
    
    Args:
        df: 日志DataFrame
        
    Returns:
        时间线分析结果
    """
    # 按5秒间隔聚合日志
    df['time_bucket'] = df['datetime'].dt.floor('5S')
    timeline = df.groupby(['time_bucket', 'level']).size().unstack(fill_value=0)
    
    # 检测异常时间段（ERROR日志突增）
    if 'ERROR' in timeline.columns:
        error_timeline = timeline['ERROR']
        mean_errors = error_timeline.mean()
        std_errors = error_timeline.std()
        anomaly_threshold = mean_errors + 2 * std_errors
        
        anomaly_periods = timeline[timeline['ERROR'] > anomaly_threshold]
        
        return {
            'total_periods': len(timeline),
            'anomaly_periods': len(anomaly_periods),
            'peak_error_time': error_timeline.idxmax() if len(error_timeline) > 0 else None,
            'peak_error_count': error_timeline.max() if len(error_timeline) > 0 else 0
        }
    
    return {'total_periods': len(timeline), 'anomaly_periods': 0}

"""
日志分析工具函数

提供日志数据的读取、分析和异常检测功能
"""

import pandas as pd
import os
from datetime import datetime
import re
from typing import Dict, List, Any, Optional


def analyze_logs(case_id: str) -> Dict[str, Any]:
    """
    分析指定案例的日志数据，检测异常并提供全面信息
    
    Args:
        case_id: 案例ID，如 "1", "2", "3"
        
    Returns:
        包含日志分析信息的字典
    """
    try:
        # 构建数据文件路径
        base_path = "/home/kangkang/code/care/data"
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
        timeline_analysis = _analyze_log_timeline(df)
        
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
            "total_logs": total_logs,
            "services": services.tolist(),
            "log_levels": log_levels,
            "anomalies": anomalies,
            "timeline_analysis": timeline_analysis,
            "service_analysis": service_analysis
        }
        
    except Exception as e:
        return {"error": f"日志分析过程中发生错误：{str(e)}"}


def _analyze_log_timeline(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析日志的时间线模式
    
    Args:
        df: 日志DataFrame
        
    Returns:
        时间线分析结果
    """
    # 按5秒间隔聚合日志
    df['time_bucket'] = df['datetime'].dt.floor('5s')
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

# Example usage:
if __name__ == "__main__":
    case_id = "1"  # 示例案例ID
    result = analyze_logs(case_id)
    print(result)

"""
指标分析工具函数

提供系统指标数据的读取、分析和异常检测功能
"""

import pandas as pd
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Annotated
import numpy as np

# 添加项目根目录到Python路径，以便导入config模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from config import dataset_path


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
            "duration_seconds": (df['datetime'].max() - df['datetime'].min()).total_seconds()
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
                    'mean': cpu_data.mean(),
                    'max': cpu_data.max(),
                    'min': cpu_data.min(),
                    'std': cpu_data.std()
                }
            
            # 内存分析
            if mem_col in df.columns:
                mem_data = df[mem_col]
                service_analysis[service]['mem'] = {
                    'mean': mem_data.mean(),
                    'max': mem_data.max(),
                    'min': mem_data.min(),
                    'std': mem_data.std()
                }
            
            # 延迟分析
            if latency_col in df.columns:
                latency_data = df[latency_col]
                service_analysis[service]['latency'] = {
                    'mean': latency_data.mean(),
                    'max': latency_data.max(),
                    'min': latency_data.min(),
                    'std': latency_data.std()
                }
        
        return {
            "metric_summary": f"Summary for metrics in case {case_id}",
            "total_data_points": total_data_points,
            "time_range": time_range,
            "services": services,
            "service_analysis": service_analysis
        }
        
    except Exception as e:
        return {"error": f"指标分析过程中发生错误：{str(e)}"}

# Example usage:
if __name__ == "__main__":
    case_id = "1"  # 示例案例ID
    result = analyze_metrics(case_id)
    print(result)

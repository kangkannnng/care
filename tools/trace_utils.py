"""
调用链分析工具函数

提供调用链数据的读取、分析和性能瓶颈检测功能
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


# Example usage:
if __name__ == "__main__":
    case_id = "1"  # 示例案例ID
    result = analyze_traces(case_id)
    print(result)

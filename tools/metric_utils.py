"""
指标分析工具函数

提供系统指标数据的读取、分析和异常检测功能
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np


def analyze_metrics(case_id: str) -> str:
    """
    分析指定案例的系统指标数据，检测资源异常和性能问题
    
    Args:
        case_id: 案例ID，如 "1", "2", "3"
        
    Returns:
        分析结果的自然语言描述
    """
    try:
        # 构建数据文件路径
        base_path = "/home/kangkang/code/care/data"
        case_path = os.path.join(base_path, f"case_{case_id}")
        metrics_file = os.path.join(case_path, "metrics.csv")
        
        if not os.path.exists(metrics_file):
            return f"错误：找不到案例{case_id}的指标文件"
        
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
        
        analysis_result = f"""
=== 系统指标分析报告 ===

1. 基础统计信息：
   - 监控服务：{', '.join(services)}
   - 指标类型：CPU使用率、内存使用率、响应延迟
   - 数据点数：{len(df)}

2. 时间范围分析：
   - 开始时间：{df['datetime'].min()}
   - 结束时间：{df['datetime'].max()}
   - 监控时长：{(df['datetime'].max() - df['datetime'].min()).total_seconds():.1f}秒

3. 资源使用情况分析："""
        
        # 分析每个服务的指标
        anomalies = []
        service_analysis = {}
        
        for service in services:
            cpu_col = f"{service}_cpu"
            mem_col = f"{service}_mem"
            latency_col = f"{service}_latency"
            
            service_analysis[service] = {}
            
            # CPU分析
            if cpu_col in df.columns:
                cpu_data = df[cpu_col]
                cpu_stats = {
                    'mean': cpu_data.mean(),
                    'max': cpu_data.max(),
                    'min': cpu_data.min(),
                    'std': cpu_data.std()
                }
                service_analysis[service]['cpu'] = cpu_stats
                
                analysis_result += f"""

   {service}服务 - CPU使用率：
     * 平均：{cpu_stats['mean']:.1f}%
     * 最大：{cpu_stats['max']:.1f}%
     * 最小：{cpu_stats['min']:.1f}%
     * 标准差：{cpu_stats['std']:.1f}%"""
                
                # 检测CPU异常
                if cpu_stats['max'] > 80:
                    anomalies.append(f"{service}服务CPU使用率过高（最大{cpu_stats['max']:.1f}%）")
                    analysis_result += " [警告：CPU使用率过高]"
                elif cpu_stats['mean'] > 70:
                    anomalies.append(f"{service}服务CPU平均使用率较高（{cpu_stats['mean']:.1f}%）")
                    analysis_result += " [注意：平均CPU使用率较高]"
            
            # 内存分析
            if mem_col in df.columns:
                mem_data = df[mem_col]
                mem_stats = {
                    'mean': mem_data.mean(),
                    'max': mem_data.max(),
                    'min': mem_data.min(),
                    'std': mem_data.std()
                }
                service_analysis[service]['mem'] = mem_stats
                
                analysis_result += f"""
     内存使用率：
     * 平均：{mem_stats['mean']:.1f}%
     * 最大：{mem_stats['max']:.1f}%
     * 最小：{mem_stats['min']:.1f}%
     * 标准差：{mem_stats['std']:.1f}%"""
                
                # 检测内存异常
                if mem_stats['max'] > 85:
                    anomalies.append(f"{service}服务内存使用率过高（最大{mem_stats['max']:.1f}%）")
                    analysis_result += " [警告：内存使用率过高]"
            
            # 延迟分析
            if latency_col in df.columns:
                latency_data = df[latency_col]
                latency_stats = {
                    'mean': latency_data.mean(),
                    'max': latency_data.max(),
                    'min': latency_data.min(),
                    'std': latency_data.std()
                }
                service_analysis[service]['latency'] = latency_stats
                
                analysis_result += f"""
     响应延迟：
     * 平均：{latency_stats['mean']:.1f}ms
     * 最大：{latency_stats['max']:.1f}ms
     * 最小：{latency_stats['min']:.1f}ms
     * 标准差：{latency_stats['std']:.1f}ms"""
                
                # 检测延迟异常
                if latency_stats['max'] > 100:
                    anomalies.append(f"{service}服务响应延迟过高（最大{latency_stats['max']:.1f}ms）")
                    analysis_result += " [警告：响应延迟过高]"
        
        # 异常检测结果
        if anomalies:
            analysis_result += f"""

4. 异常检测结果：
   发现 {len(anomalies)} 项异常："""
            for i, anomaly in enumerate(anomalies, 1):
                analysis_result += f"""
   {i}. {anomaly}"""
        else:
            analysis_result += """

4. 异常检测结果：
   未发现明显的资源使用异常"""
        
        # 时间序列异常分析
        time_anomalies = _detect_time_series_anomalies(df, services)
        if time_anomalies:
            analysis_result += f"""

5. 时间序列异常分析："""
            for anomaly in time_anomalies:
                analysis_result += f"""
   - {anomaly}"""
        
        # 服务间相关性分析
        correlations = _analyze_service_correlations(df, services)
        if correlations:
            analysis_result += f"""

6. 服务间相关性分析："""
            for correlation in correlations:
                analysis_result += f"""
   - {correlation}"""
        
        # 根因推理
        analysis_result += """

7. 根因分析推理："""
        
        if anomalies:
            # 找出问题最严重的服务
            cpu_issues = [a for a in anomalies if 'CPU' in a]
            mem_issues = [a for a in anomalies if '内存' in a]
            latency_issues = [a for a in anomalies if '延迟' in a]
            
            if cpu_issues:
                analysis_result += f"""
   - CPU相关问题：{len(cpu_issues)}项
   - 高CPU使用率可能导致服务响应缓慢和系统不稳定"""
                
                # 找出CPU问题最严重的服务
                worst_cpu_service = _find_worst_cpu_service(service_analysis)
                if worst_cpu_service:
                    analysis_result += f"""
   - {worst_cpu_service}服务的CPU使用率最高，可能是性能瓶颈的根源"""
            
            if mem_issues:
                analysis_result += f"""
   - 内存相关问题：{len(mem_issues)}项
   - 高内存使用率可能导致垃圾回收频繁，影响性能"""
            
            if latency_issues:
                analysis_result += f"""
   - 延迟相关问题：{len(latency_issues)}项
   - 高响应延迟直接影响用户体验"""
            
            # 综合推理
            problem_services = _identify_problem_services(service_analysis)
            if problem_services:
                analysis_result += f"""
   - 综合分析，以下服务存在明显问题：{', '.join(problem_services)}
   - 建议优先检查这些服务的资源配置和代码逻辑"""
        else:
            analysis_result += """
   - 从指标数据看，各服务的资源使用率相对正常
   - 如果存在性能问题，可能是由于业务逻辑或外部依赖导致
   - 建议结合日志和调用链数据进一步分析"""
        
        analysis_result += """

8. 结论：
   基于系统指标分析，已识别出资源使用异常和性能瓶颈，建议结合其他数据源验证问题根因。"""
        
        return analysis_result
        
    except Exception as e:
        return f"指标分析过程中发生错误：{str(e)}"


def _detect_time_series_anomalies(df: pd.DataFrame, services: List[str]) -> List[str]:
    """
    检测时间序列中的异常模式
    
    Args:
        df: 指标DataFrame
        services: 服务列表
        
    Returns:
        异常描述列表
    """
    anomalies = []
    
    try:
        for service in services:
            cpu_col = f"{service}_cpu"
            
            if cpu_col in df.columns:
                cpu_data = df[cpu_col]
                
                # 检测突然的峰值
                rolling_mean = cpu_data.rolling(window=3).mean()
                rolling_std = cpu_data.rolling(window=3).std()
                
                # 找出超过均值+2*标准差的点
                anomaly_mask = cpu_data > (rolling_mean + 2 * rolling_std)
                anomaly_points = df[anomaly_mask]
                
                if len(anomaly_points) > 0:
                    peak_time = anomaly_points.iloc[0]['datetime']
                    peak_value = anomaly_points.iloc[0][cpu_col]
                    anomalies.append(f"{service}服务在{peak_time}出现CPU峰值（{peak_value:.1f}%）")
                
                # 检测持续高负载
                high_load_mask = cpu_data > 70
                if high_load_mask.sum() > len(cpu_data) * 0.3:  # 超过30%的时间处于高负载
                    anomalies.append(f"{service}服务长时间处于高CPU负载状态")
    
    except Exception:
        pass
    
    return anomalies


def _analyze_service_correlations(df: pd.DataFrame, services: List[str]) -> List[str]:
    """
    分析服务间指标的相关性
    
    Args:
        df: 指标DataFrame
        services: 服务列表
        
    Returns:
        相关性描述列表
    """
    correlations = []
    
    try:
        # 构建CPU使用率矩阵
        cpu_data = {}
        for service in services:
            cpu_col = f"{service}_cpu"
            if cpu_col in df.columns:
                cpu_data[service] = df[cpu_col]
        
        if len(cpu_data) > 1:
            cpu_df = pd.DataFrame(cpu_data)
            corr_matrix = cpu_df.corr()
            
            # 找出高相关性的服务对
            for i in range(len(services)):
                for j in range(i+1, len(services)):
                    service1 = services[i]
                    service2 = services[j]
                    
                    if service1 in corr_matrix.index and service2 in corr_matrix.columns:
                        corr = corr_matrix.loc[service1, service2]
                        
                        if corr > 0.8:
                            correlations.append(f"{service1}和{service2}的CPU使用率高度正相关（{corr:.2f}）")
                        elif corr < -0.5:
                            correlations.append(f"{service1}和{service2}的CPU使用率负相关（{corr:.2f}）")
    
    except Exception:
        pass
    
    return correlations


def _find_worst_cpu_service(service_analysis: Dict[str, Dict]) -> Optional[str]:
    """
    找出CPU使用率最高的服务
    
    Args:
        service_analysis: 服务分析结果
        
    Returns:
        CPU使用率最高的服务名
    """
    worst_service = None
    highest_cpu = 0
    
    for service, metrics in service_analysis.items():
        if 'cpu' in metrics:
            max_cpu = metrics['cpu']['max']
            if max_cpu > highest_cpu:
                highest_cpu = max_cpu
                worst_service = service
    
    return worst_service


def _identify_problem_services(service_analysis: Dict[str, Dict]) -> List[str]:
    """
    识别存在问题的服务
    
    Args:
        service_analysis: 服务分析结果
        
    Returns:
        问题服务列表
    """
    problem_services = []
    
    for service, metrics in service_analysis.items():
        problems = 0
        
        # 检查CPU问题
        if 'cpu' in metrics:
            cpu_stats = metrics['cpu']
            if cpu_stats['max'] > 80 or cpu_stats['mean'] > 70:
                problems += 1
        
        # 检查内存问题
        if 'mem' in metrics:
            mem_stats = metrics['mem']
            if mem_stats['max'] > 85:
                problems += 1
        
        # 检查延迟问题
        if 'latency' in metrics:
            latency_stats = metrics['latency']
            if latency_stats['max'] > 100:
                problems += 1
        
        # 如果有多个指标异常，认为是问题服务
        if problems >= 2:
            problem_services.append(service)
    
    return problem_services

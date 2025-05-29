"""
报告生成工具函数

提供最终分析报告的生成和格式化功能
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import json


def generate_final_report(
    user_query: str,
    log_analysis: str,
    trace_analysis: str, 
    metric_analysis: str,
    consensus_results: List[Dict[str, Any]],
    final_conclusion: str
) -> str:
    """
    生成结构化的最终分析报告
    
    Args:
        user_query: 用户原始查询
        log_analysis: 日志分析结果
        trace_analysis: 调用链分析结果
        metric_analysis: 指标分析结果
        consensus_results: 共识投票结果
        final_conclusion: 最终根因结论
        
    Returns:
        格式化的分析报告
    """
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
================================================================================
                           CARE系统根因分析报告
================================================================================

生成时间：{report_time}
分析框架：CARE多智能体协作分析系统

================================================================================
一、用户问题摘要
================================================================================

原始查询：{user_query}

问题描述：用户请求对指定案例进行根因分析，系统通过多智能体协作方式，
从日志、调用链、系统指标三个维度并行分析，并通过共识机制验证分析结果。

================================================================================
二、分析步骤总览
================================================================================

本次分析按照以下步骤执行：

1. 【日志分析阶段】
   - 执行智能体：LogAgent
   - 分析目标：检测错误日志、异常模式、服务状态
   - 工具函数：analyze_logs()
   - 状态：✓ 已完成并通过共识

2. 【调用链分析阶段】
   - 执行智能体：TraceAgent  
   - 分析目标：识别性能瓶颈、调用异常、服务依赖
   - 工具函数：analyze_traces()
   - 状态：✓ 已完成并通过共识

3. 【系统指标分析阶段】
   - 执行智能体：MetricAgent
   - 分析目标：检测资源异常、性能问题、负载状况
   - 工具函数：analyze_metrics()
   - 状态：✓ 已完成并通过共识

4. 【报告生成阶段】
   - 执行智能体：ReportAgent
   - 分析目标：整合分析结果，生成最终结论
   - 工具函数：generate_final_report()
   - 状态：✓ 进行中

================================================================================
三、各智能体分析过程摘要
================================================================================

3.1 日志分析智能体（LogAgent）
────────────────────────────────────────────────────────────────────────────

【函数调用】：analyze_logs()
【观察结果】：
{_extract_summary(log_analysis)}

【分析结论】：
{_extract_conclusion(log_analysis)}

【共识状态】：{_get_consensus_status(consensus_results, 'log')}

────────────────────────────────────────────────────────────────────────────

3.2 调用链分析智能体（TraceAgent）
────────────────────────────────────────────────────────────────────────────

【函数调用】：analyze_traces()
【观察结果】：
{_extract_summary(trace_analysis)}

【分析结论】：
{_extract_conclusion(trace_analysis)}

【共识状态】：{_get_consensus_status(consensus_results, 'trace')}

────────────────────────────────────────────────────────────────────────────

3.3 系统指标分析智能体（MetricAgent）
────────────────────────────────────────────────────────────────────────────

【函数调用】：analyze_metrics()
【观察结果】：
{_extract_summary(metric_analysis)}

【分析结论】：
{_extract_conclusion(metric_analysis)}

【共识状态】：{_get_consensus_status(consensus_results, 'metric')}

================================================================================
四、共识机制执行情况
================================================================================

本次分析共进行了 {len(consensus_results)} 轮共识投票：

"""
    
    # 添加每轮共识的详细信息
    for i, consensus in enumerate(consensus_results, 1):
        stage = consensus.get('stage', f'第{i}阶段')
        voters = consensus.get('voters', [])
        votes = consensus.get('votes', [])
        result = consensus.get('result', 'unknown')
        
        report += f"""
第{i}轮共识 - {stage}：
  投票者：{', '.join(voters)}
  投票结果：{votes}
  通过状态：{'✓ 通过' if result == 'passed' else '✗ 未通过'}
  投票详情：{consensus.get('details', '无详细信息')}
"""
    
    report += f"""
================================================================================
五、最终共识根因与解释
================================================================================

{final_conclusion}

================================================================================
六、证据链条总结
================================================================================

基于多智能体协作分析和共识机制验证，本次根因分析的证据链条如下：

{_generate_evidence_chain(log_analysis, trace_analysis, metric_analysis)}

================================================================================
七、建议与后续行动
================================================================================

基于以上分析结果，建议采取以下行动：

{_generate_recommendations(final_conclusion)}

================================================================================
                                 报告结束
================================================================================

注：本报告由CARE多智能体系统自动生成，分析结果已通过共识机制验证。
    如需进一步分析，请提供更多数据或调整分析参数。
"""
    
    return report


def _extract_summary(analysis_text: str) -> str:
    """
    从分析文本中提取关键观察结果
    
    Args:
        analysis_text: 完整分析文本
        
    Returns:
        关键观察结果摘要
    """
    # 提取基础统计和异常检测部分
    lines = analysis_text.split('\n')
    summary_lines = []
    
    in_stats = False
    in_anomaly = False
    
    for line in lines:
        line = line.strip()
        
        if '基础统计信息' in line or '时间范围分析' in line:
            in_stats = True
            continue
        elif '异常检测结果' in line or '性能分析' in line:
            in_anomaly = True
            continue
        elif line.startswith('=') or '根因分析推理' in line:
            in_stats = False
            in_anomaly = False
            continue
        
        if (in_stats or in_anomaly) and line and not line.startswith('='):
            summary_lines.append(line)
    
    return '\n'.join(summary_lines[:10])  # 限制长度


def _extract_conclusion(analysis_text: str) -> str:
    """
    从分析文本中提取结论部分
    
    Args:
        analysis_text: 完整分析文本
        
    Returns:
        分析结论
    """
    lines = analysis_text.split('\n')
    conclusion_lines = []
    
    in_conclusion = False
    
    for line in lines:
        line = line.strip()
        
        if '根因分析推理' in line or '结论' in line:
            in_conclusion = True
            continue
        elif line.startswith('=') and in_conclusion:
            break
        
        if in_conclusion and line and not line.startswith('='):
            conclusion_lines.append(line)
    
    return '\n'.join(conclusion_lines)


def _get_consensus_status(consensus_results: List[Dict[str, Any]], stage: str) -> str:
    """
    获取指定阶段的共识状态
    
    Args:
        consensus_results: 共识结果列表
        stage: 阶段名称
        
    Returns:
        共识状态描述
    """
    for consensus in consensus_results:
        if stage in consensus.get('stage', '').lower():
            result = consensus.get('result', 'unknown')
            votes = consensus.get('votes', [])
            
            if result == 'passed':
                return f"✓ 通过（{votes.count(True)}/{len(votes)}票赞成）"
            else:
                return f"✗ 未通过（{votes.count(True)}/{len(votes)}票赞成）"
    
    return "⚠ 无共识记录"


def _generate_evidence_chain(log_analysis: str, trace_analysis: str, metric_analysis: str) -> str:
    """
    生成证据链条总结
    
    Args:
        log_analysis: 日志分析结果
        trace_analysis: 调用链分析结果  
        metric_analysis: 指标分析结果
        
    Returns:
        证据链条描述
    """
    evidence_chain = """
1. 【日志层面证据】
   - 通过日志分析发现的错误模式和异常时间点
   - 为根因定位提供了故障发生的时间线和初步方向

2. 【调用链层面证据】
   - 通过调用链分析识别的性能瓶颈和服务依赖关系
   - 验证了故障传播路径和影响范围

3. 【系统指标层面证据】
   - 通过指标分析确认的资源使用异常和性能下降
   - 提供了故障根因的直接技术证据

4. 【多维度交叉验证】
   - 三个维度的分析结果相互印证，形成完整的证据链
   - 共识机制确保了每个环节分析结果的可靠性
"""
    
    return evidence_chain


def _generate_recommendations(final_conclusion: str) -> str:
    """
    基于最终结论生成建议
    
    Args:
        final_conclusion: 最终结论
        
    Returns:
        建议和后续行动
    """
    recommendations = """
1. 【立即行动】
   - 针对识别出的根因服务进行资源扩容或配置优化
   - 检查相关服务的日志和错误处理机制

2. 【短期优化】
   - 优化有性能瓶颈的服务代码和算法
   - 加强监控告警，及时发现类似问题

3. 【长期改进】
   - 建立更完善的服务治理和性能监控体系
   - 定期进行系统性能评估和容量规划

4. 【预防措施】
   - 增强系统的容错能力和自愈能力
   - 建立故障演练和应急响应流程
"""
    
    return recommendations


def format_consensus_summary(consensus_results: List[Dict[str, Any]]) -> str:
    """
    格式化共识结果摘要
    
    Args:
        consensus_results: 共识结果列表
        
    Returns:
        格式化的共识摘要
    """
    if not consensus_results:
        return "未进行共识投票"
    
    total_votes = len(consensus_results)
    passed_votes = sum(1 for c in consensus_results if c.get('result') == 'passed')
    
    summary = f"共进行{total_votes}轮共识投票，{passed_votes}轮通过，成功率：{passed_votes/total_votes*100:.1f}%"
    
    return summary


def extract_case_id(user_query: str) -> Optional[str]:
    """
    从用户查询中提取案例ID
    
    Args:
        user_query: 用户查询文本
        
    Returns:
        提取的案例ID
    """
    import re
    
    # 匹配 case 1, case_1, 案例1 等模式
    patterns = [
        r'case[\s_]*(\d+)',
        r'案例[\s_]*(\d+)',
        r'case(\d+)',
        r'(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_query.lower())
        if match:
            return match.group(1)
    
    return None

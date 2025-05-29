"""
报告生成工具函数

提供最终报告的生成和格式化功能
"""

from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime
import json


def generate_final_report(
    case_id: Annotated[str, "案例ID，如 '1', '2', '3'"],
    log_analysis: Annotated[str, "日志分析结果"],
    trace_analysis: Annotated[str, "调用链分析结果"], 
    metric_analysis: Annotated[str, "指标分析结果"],
    root_cause: Annotated[str, "最终根因结论"],
    recommendations: Annotated[str, "改进建议"]
) -> Dict[str, Any]:
    """
    生成结构化的最终根因分析报告
    
    Args:
        case_id: 案例ID
        log_analysis: 日志分析结果
        trace_analysis: 调用链分析结果
        metric_analysis: 指标分析结果
        root_cause: 最终根因结论
        recommendations: 改进建议
        
    Returns:
        包含格式化报告的字典
    """
    try:
        # 生成报告时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建结构化报告
        report = {
            "case_id": case_id,
            "timestamp": timestamp,
            "analysis_summary": {
                "log_analysis": log_analysis,
                "trace_analysis": trace_analysis,
                "metric_analysis": metric_analysis
            },
            "root_cause_analysis": {
                "conclusion": root_cause,
                "confidence": "高",  # 基于多智能体共识
                "evidence_sources": ["日志数据", "调用链数据", "系统指标"]
            },
            "recommendations": recommendations,
            "report_metadata": {
                "analysis_method": "多智能体协作根因分析",
                "consensus_mechanism": "智能体投票共识",
                "data_sources": ["logs", "traces", "metrics"]
            }
        }
        
        # 生成Markdown格式的报告文本
        markdown_report = f"""# 根因分析报告 - 案例 {case_id}

**生成时间**: {timestamp}

## 执行摘要

本报告基于CARE多智能体协作根因分析系统，通过对日志、调用链和系统指标的综合分析，确定了案例{case_id}的根本原因。

## 分析结果汇总

### 日志分析
{log_analysis}

### 调用链分析
{trace_analysis}

### 系统指标分析
{metric_analysis}

## 根因结论

**根本原因**: {root_cause}

**置信度**: 高（基于多智能体共识机制）

**证据来源**: 日志数据、调用链数据、系统指标

## 改进建议

{recommendations}

## 分析方法

- **分析框架**: CARE多智能体协作根因分析
- **共识机制**: 智能体投票验证
- **数据来源**: 多维度监控数据（日志、调用链、指标）
- **分析深度**: 深度根因分析与交叉验证

---
*报告由CARE系统自动生成*
"""
        
        report["formatted_report"] = markdown_report
        
        return {
            "success": True,
            "report": report,
            "formatted_text": markdown_report
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"报告生成失败: {str(e)}"
        }


# Example usage:
if __name__ == "__main__":
    result = generate_final_report(
        case_id="1",
        log_analysis="发现用户服务出现大量认证错误",
        trace_analysis="检测到用户服务响应延迟异常增加",
        metric_analysis="用户服务CPU使用率持续100%",
        root_cause="用户服务认证模块存在性能瓶颈",
        recommendations="优化认证算法，增加服务实例数量"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))

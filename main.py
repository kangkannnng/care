#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CARE系统主入口

多智能体协作根因分析框架
基于AutoGen实现多源分析、共识机制和解释性报告生成
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
import autogen
from autogen import GroupChat, GroupChatManager

from agents import LogAgent, TraceAgent, MetricAgent, ReportAgent
from workflow.consensus_coordinator import ConsensusCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CARESystem:
    """CARE多智能体协作根因分析系统"""
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化CARE系统
        
        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config
        self.data_path = "/home/kangkang/code/care/data"
        
        # 初始化智能体
        self.log_agent = LogAgent(llm_config=llm_config)
        self.trace_agent = TraceAgent(llm_config=llm_config) 
        self.metric_agent = MetricAgent(llm_config=llm_config)
        self.report_agent = ReportAgent(llm_config=llm_config)
        
        # 初始化用户代理
        self.user_proxy = autogen.UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config={"use_docker": False}
        )
        
        # 初始化共识协调器
        all_agents = [self.log_agent, self.trace_agent, self.metric_agent, self.report_agent]
        self.consensus_coordinator = ConsensusCoordinator(agents=all_agents, llm_config=llm_config)
        
        logger.info("CARE系统初始化完成")
    
    def extract_case_id(self, query: str) -> Optional[str]:
        """
        从用户查询中提取案例ID
        
        Args:
            query: 用户查询
            
        Returns:
            案例ID或None
        """
        # 匹配 case_1, case_2, case_3 等格式
        patterns = [
            r'case[_\s]?(\d+)',
            r'案例[_\s]?(\d+)',
            r'第(\d+)个',
            r'(\d+)号'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                case_num = match.group(1)
                return f"case_{case_num}"
        
        return None
    
    def validate_case_data(self, case_id: str) -> bool:
        """
        验证案例数据是否存在
        
        Args:
            case_id: 案例ID
            
        Returns:
            数据是否完整
        """
        case_path = os.path.join(self.data_path, case_id)
        if not os.path.exists(case_path):
            return False
        
        required_files = ['logs.csv', 'traces.csv', 'metrics.csv', 'ground_truth.json']
        for file in required_files:
            if not os.path.exists(os.path.join(case_path, file)):
                logger.warning(f"缺少文件: {case_id}/{file}")
                return False
        
        return True
    
    def load_ground_truth(self, case_id: str) -> Dict[str, Any]:
        """
        加载标准答案
        
        Args:
            case_id: 案例ID
            
        Returns:
            标准答案数据
        """
        ground_truth_path = os.path.join(self.data_path, case_id, 'ground_truth.json')
        try:
            with open(ground_truth_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载标准答案失败: {e}")
            return {}
    
    def create_group_chat(self, case_id: str, user_query: str) -> GroupChat:
        """
        创建群聊组织智能体交互
        
        Args:
            case_id: 案例ID
            user_query: 用户查询
            
        Returns:
            群聊对象
        """
        # 设置案例路径
        case_path = os.path.join(self.data_path, case_id)
        for agent in [self.log_agent, self.trace_agent, self.metric_agent]:
            agent.set_case_path(case_path)
        
        # 定义严格的发言顺序
        def custom_speaker_selection(last_speaker, groupchat):
            """自定义发言人选择：严格按照 Log → Consensus → Trace → Consensus → Metric → Consensus → Report 顺序"""
            
            messages = groupchat.messages
            if not messages:
                return self.log_agent
            
            # 根据消息历史确定下一个发言人
            if len(messages) == 1:  # 用户查询后
                return self.log_agent
            
            last_msg = messages[-1]
            last_name = last_msg.get('name', '')
            
            # 如果是智能体分析后，进行共识投票
            if last_name == "日志分析师":
                # 进行日志分析共识
                return None  # 触发共识机制
            elif last_name == "调用链分析师":
                # 进行调用链分析共识
                return None  # 触发共识机制
            elif last_name == "指标分析师":
                # 进行指标分析共识
                return None  # 触发共识机制
            elif "共识结果" in last_msg.get('content', ''):
                # 共识完成后，继续下一个分析
                if "日志分析" in last_msg.get('content', ''):
                    return self.trace_agent
                elif "调用链分析" in last_msg.get('content', ''):
                    return self.metric_agent
                elif "指标分析" in last_msg.get('content', ''):
                    return self.report_agent
            
            return None
        
        # 创建群聊
        groupchat = GroupChat(
            agents=[self.log_agent, self.trace_agent, self.metric_agent, self.report_agent],
            messages=[],
            max_round=20,
            speaker_selection_method=custom_speaker_selection,
            allow_repeat_speaker=False
        )
        
        return groupchat
    
    def run_consensus(self, current_agent: Any, stage: str, result: str) -> str:
        """
        运行共识机制
        
        Args:
            current_agent: 当前执行分析的智能体
            stage: 分析阶段
            result: 分析结果
            
        Returns:
            共识结果
        """
        try:
            passed, consensus_result = self.consensus_coordinator.conduct_consensus(
                stage=stage,
                analysis_result=result,
                current_agent=current_agent
            )
            if passed:
                return f"【{stage}共识结果】通过 - {result}"
            else:
                return f"【{stage}共识结果】未通过 - {result}"
        except Exception as e:
            logger.error(f"共识机制运行失败: {e}")
            return f"【{stage}共识结果】{result}"  # 回退到原始结果
    
    def analyze_case(self, user_query: str) -> Dict[str, Any]:
        """
        分析指定案例
        
        Args:
            user_query: 用户查询
            
        Returns:
            分析结果
        """
        # 提取案例ID
        case_id = self.extract_case_id(user_query)
        if not case_id:
            return {
                "success": False,
                "error": "无法从查询中提取案例ID，请指定要分析的案例（如：case_1, case_2, case_3）"
            }
        
        # 验证案例数据
        if not self.validate_case_data(case_id):
            return {
                "success": False,
                "error": f"案例 {case_id} 的数据不完整"
            }
        
        logger.info(f"开始分析案例: {case_id}")
        
        try:
            # 设置案例路径
            case_path = os.path.join(self.data_path, case_id)
            
            # 1. 日志分析
            logger.info("开始日志分析...")
            log_result = self.log_agent.analyze_logs(case_path)
            log_consensus = self.run_consensus(
                self.log_agent,
                "日志分析",
                log_result
            )
            
            # 2. 调用链分析
            logger.info("开始调用链分析...")
            trace_result = self.trace_agent.initiate_analysis(case_id, self.create_temp_manager(), log_consensus)
            trace_consensus = self.run_consensus(
                self.trace_agent,
                "调用链分析", 
                str(trace_result)
            )
            
            # 3. 指标分析
            logger.info("开始指标分析...")
            metric_result = self.metric_agent.initiate_analysis(case_id, self.create_temp_manager(), f"{log_consensus}\n{trace_consensus}")
            metric_consensus = self.run_consensus(
                self.metric_agent,
                "指标分析",
                str(metric_result)
            )
            
            # 4. 生成最终报告
            logger.info("生成最终报告...")
            final_report = self.report_agent.generate_report(
                user_query=user_query,
                case_id=case_id,
                log_analysis=log_consensus,
                trace_analysis=trace_consensus,
                metric_analysis=metric_consensus
            )
            
            # 加载标准答案进行对比
            ground_truth = self.load_ground_truth(case_id)
            
            return {
                "success": True,
                "case_id": case_id,
                "analysis_steps": {
                    "log_analysis": log_result,
                    "log_consensus": log_consensus,
                    "trace_analysis": trace_result,
                    "trace_consensus": trace_consensus,
                    "metric_analysis": metric_result,
                    "metric_consensus": metric_consensus
                },
                "final_report": final_report,
                "ground_truth": ground_truth
            }
            
        except Exception as e:
            logger.error(f"案例分析失败: {e}")
            return {
                "success": False,
                "error": f"案例分析过程中发生错误: {str(e)}"
            }
    
    def run_demo(self):
        """运行演示程序"""
        print("=" * 60)
        print("CARE多智能体协作根因分析系统演示")
        print("=" * 60)
        
        # 测试所有案例
        test_cases = [
            "请分析 case_1 的根因问题",
            "帮我分析第2个案例的故障原因", 
            "case_3发生了什么问题？"
        ]
        
        for i, query in enumerate(test_cases, 1):
            print(f"\n{'='*40}")
            print(f"测试案例 {i}: {query}")
            print(f"{'='*40}")
            
            result = self.analyze_case(query)
            
            if result["success"]:
                print(f"✅ 案例 {result['case_id']} 分析完成")
                print("\n📊 最终报告:")
                print(result["final_report"])
                
                if result["ground_truth"]:
                    print(f"\n🎯 标准答案: {result['ground_truth'].get('root_cause', '未提供')}")
                
            else:
                print(f"❌ 分析失败: {result['error']}")
    
    def interactive_mode(self):
        """交互模式"""
        print("=" * 60)
        print("CARE系统交互模式")
        print("输入查询来分析案例，输入 'quit' 退出")
        print("=" * 60)
        
        while True:
            try:
                query = input("\n请输入查询: ").strip()
                
                if query.lower() in ['quit', 'exit', '退出']:
                    print("感谢使用CARE系统！")
                    break
                
                if not query:
                    continue
                
                print("\n🔄 正在分析...")
                result = self.analyze_case(query)
                
                if result["success"]:
                    print(f"\n✅ 案例 {result['case_id']} 分析完成")
                    print("\n📊 最终报告:")
                    print(result["final_report"])
                else:
                    print(f"\n❌ 分析失败: {result['error']}")
                    
            except KeyboardInterrupt:
                print("\n\n感谢使用CARE系统！")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
    
    def create_temp_manager(self) -> autogen.GroupChatManager:
        """
        创建临时的群聊管理器用于单独的智能体分析
        
        Returns:
            临时的群聊管理器
        """
        # 创建临时群聊，只包含用户代理
        temp_groupchat = autogen.GroupChat(
            agents=[self.user_proxy],
            messages=[],
            max_round=3
        )
        
        temp_manager = autogen.GroupChatManager(
            groupchat=temp_groupchat,
            llm_config=self.llm_config,
            code_execution_config={"use_docker": False}
        )
        
        return temp_manager

def main():
    """主函数"""
    # LLM配置 - 使用本地llama3.1
    llm_config = autogen.LLMConfig(
        api_type="ollama",
        model="llama3.1",
    )
    
    # 创建CARE系统实例
    care_system = CARESystem(llm_config=llm_config)
    
    # 运行演示
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ["demo", "--demo"]:
        care_system.run_demo()
    else:
        care_system.interactive_mode()


if __name__ == "__main__":
    main()

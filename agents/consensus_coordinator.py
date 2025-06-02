"""
共识机制协调器

负责管理多智能体之间的共识投票流程
"""

import autogen
import random
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ConsensusCoordinator:
    """
    共识机制协调器
    
    负责：
    1. 在每个分析阶段后组织共识投票
    2. 从现有智能体中动态选择评审组
    3. 管理投票流程和结果统计
    4. 决定是否通过共识或需要重新分析
    """
    
    def __init__(self, agents: List[Any], llm_config: Dict[str, Any]):
        """
        初始化共识协调器
        
        Args:
            agents: 所有智能体列表
            llm_config: LLM配置
        """
        self.agents = agents
        self.llm_config = llm_config
        self.consensus_history: List[Dict[str, Any]] = []
        
        # 创建用于共识投票的用户代理
        self.consensus_manager = autogen.UserProxyAgent(
            name="ConsensusManager",
            system_message="管理共识投票流程的协调者",
            llm_config=False,  # 不使用LLM
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config={"use_docker": False}
        )
    
    def conduct_consensus(
        self, 
        stage: str, 
        analysis_result: str, 
        current_agent: Any,
        retry_count: int = 0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        执行共识投票
        
        Args:
            stage: 当前分析阶段（log/trace/metric/report）
            analysis_result: 待评估的分析结果
            current_agent: 当前执行分析的智能体
            retry_count: 重试次数
            
        Returns:
            (是否通过共识, 详细投票结果)
        """
        logger.info(f"开始{stage}阶段的共识投票（第{retry_count + 1}次）")
        
        # 选择评审组（排除当前分析智能体）
        reviewers = self._select_reviewers(current_agent)
        
        if len(reviewers) < 3:
            logger.warning("可用评审者不足3人，共识自动通过")
            return True, {
                'stage': stage,
                'voters': [agent.name for agent in reviewers],
                'votes': [True] * len(reviewers),
                'result': 'passed',
                'reason': '评审者不足，自动通过',
                'retry_count': retry_count
            }
        
        # 进行投票
        votes = []
        vote_details = []
        
        for reviewer in reviewers:
            vote, reason = self._get_vote(reviewer, stage, analysis_result)
            votes.append(vote)
            vote_details.append({
                'agent': reviewer.name,
                'vote': vote,
                'reason': reason
            })
            logger.info(f"{reviewer.name} 投票: {'赞成' if vote else '反对'} - {reason}")
        
        # 统计结果（2/3通过）
        approve_count = sum(votes)
        total_count = len(votes)
        passed = approve_count >= (total_count * 2 / 3)
        
        consensus_result = {
            'stage': stage,
            'voters': [agent.name for agent in reviewers],
            'votes': votes,
            'vote_details': vote_details,
            'result': 'passed' if passed else 'failed',
            'approve_count': approve_count,
            'total_count': total_count,
            'retry_count': retry_count,
            'timestamp': self._get_timestamp()
        }
        
        # 记录共识历史
        self.consensus_history.append(consensus_result)
        
        logger.info(f"共识投票结果: {approve_count}/{total_count} {'通过' if passed else '未通过'}")
        
        return passed, consensus_result
    
    def _select_reviewers(self, current_agent: Any) -> List[Any]:
        """
        选择评审组成员
        
        Args:
            current_agent: 当前执行分析的智能体
            
        Returns:
            评审组成员列表
        """
        # 排除当前智能体
        candidates = [agent for agent in self.agents if agent.name != current_agent.name]
        
        # 如果候选者不足3人，返回所有候选者
        if len(candidates) <= 3:
            return candidates
        
        # 随机选择3个评审者
        return random.sample(candidates, 3)
    
    def _get_vote(self, reviewer: Any, stage: str, analysis_result: str) -> Tuple[bool, str]:
        """
        获取单个评审者的投票
        
        Args:
            reviewer: 评审者智能体
            stage: 分析阶段
            analysis_result: 分析结果
            
        Returns:
            (投票结果, 投票理由)
        """
        try:
            # 构建投票提示
            vote_prompt = f"""
请评估以下{stage}阶段的分析结果：

{analysis_result}

评估标准：
1. 分析逻辑是否清晰合理？
2. 证据是否充分支撑结论？
3. 是否遗漏了重要信息？
4. 推理过程是否可信？

请给出你的评估：
- 如果认为分析合理可信，请回复："赞成 - [理由]"
- 如果认为分析有问题，请回复："反对 - [理由]"

你的评估：
"""
            
            # 创建临时群聊进行投票
            temp_groupchat = autogen.GroupChat(
                agents=[reviewer.agent, self.consensus_manager],
                messages=[],
                max_round=2,
                speaker_selection_method='round_robin'  # 添加此行
            )
            temp_manager = autogen.GroupChatManager(
                groupchat=temp_groupchat,
                llm_config=self.llm_config,
                code_execution_config={"use_docker": False}
            )
            
            # 发起投票对话
            chat_result = reviewer.agent.initiate_chat(
                temp_manager,
                message=vote_prompt,
                max_turns=1
            )
            
            # 解析投票结果
            if hasattr(chat_result, 'chat_history') and chat_result.chat_history:
                last_message = chat_result.chat_history[-1].get('content', '')
            else:
                last_message = str(chat_result)
            
            return self._parse_vote_response(last_message)
            
        except Exception as e:
            logger.error(f"获取{reviewer.name}投票时出错: {str(e)}")
            # 出错时默认投赞成票
            return True, f"投票出错，默认赞成: {str(e)}"
    
    def _parse_vote_response(self, response: str) -> Tuple[bool, str]:
        """
        解析投票回复
        
        Args:
            response: 智能体的回复
            
        Returns:
            (投票结果, 理由)
        """
        response_lower = response.lower()
        
        if '赞成' in response or 'approve' in response_lower or '同意' in response:
            # 提取理由
            if ' - ' in response:
                reason = response.split(' - ', 1)[1].strip()
            else:
                reason = "未提供具体理由"
            return True, reason
        elif '反对' in response or 'reject' in response_lower or '不同意' in response:
            # 提取理由
            if ' - ' in response:
                reason = response.split(' - ', 1)[1].strip()
            else:
                reason = "未提供具体理由"
            return False, reason
        else:
            # 无法解析时默认赞成
            return True, f"无法解析投票意图，默认赞成: {response[:100]}"
    
    def get_consensus_summary(self) -> Dict[str, Any]:
        """
        获取共识投票的总结信息
        
        Returns:
            共识总结
        """
        if not self.consensus_history:
            return {
                'total_rounds': 0,
                'passed_rounds': 0,
                'success_rate': 0.0,
                'details': []
            }
        
        total_rounds = len(self.consensus_history)
        passed_rounds = sum(1 for c in self.consensus_history if c['result'] == 'passed')
        success_rate = passed_rounds / total_rounds if total_rounds > 0 else 0
        
        return {
            'total_rounds': total_rounds,
            'passed_rounds': passed_rounds,
            'success_rate': success_rate,
            'details': self.consensus_history
        }
    
    def _get_timestamp(self) -> str:
        """
        获取当前时间戳
        
        Returns:
            格式化的时间戳
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_passed_consensus_summary(self) -> str:
        """
        获取所有通过共识的分析摘要
        
        Returns:
            通过共识的分析摘要
        """
        passed_consensus = [c for c in self.consensus_history if c['result'] == 'passed']
        
        if not passed_consensus:
            return "暂无通过共识的分析结果"
        
        summary = "已通过共识的分析阶段：\n"
        for consensus in passed_consensus:
            stage = consensus['stage']
            approve_count = consensus['approve_count']
            total_count = consensus['total_count']
            summary += f"- {stage}阶段：{approve_count}/{total_count}票通过\n"
        
        return summary

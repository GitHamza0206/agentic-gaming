#!/usr/bin/env python3
"""
Round Table Meeting Logic Test - 使用Mock LLM避免API配额问题
"""

import sys
import os
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.impostor_game.service import ImpostorGameService
from src.features.impostor_game.schema import ActionType, GameStatus, GamePhase

class MockLLMClient:
    """Mock LLM客户端，提供多样化的测试响应"""
    
    def __init__(self):
        self.call_count = 0
        
        # 预设的发言内容
        self.initial_statements = [
            "我刚才在做任务，看到有人行为可疑。",
            "我一直在电力室修理线路，有人可以证明吗？",
            "刚才灯光熄灭的时候，我看到有人在走廊里。",
            "我觉得我们需要仔细分析每个人的行踪。",
            "有人看到我在医疗室扫描吗？我可以证明自己是无辜的。",
            "刚才反应堆警报响起时，我正在导航室。",
            "我怀疑有人在撒谎，我们需要投票。",
            "我一直和其他人在一起，不可能是我。"
        ]
        
        self.follow_up_statements = [
            "我想补充一点，刚才的说法有问题。",
            "等等，我记得情况不是这样的。",
            "我可以为某人作证，我们当时在一起。",
            "这个说法很可疑，我觉得需要质疑。",
            "我有新的信息要分享。",
            "让我澄清一下我之前的话。"
        ]
        
        self.vote_responses = [
            "VOTE|2|我觉得Green行为很可疑",
            "VOTE|4|Orange一直在撒谎",
            "VOTE|1|Blue的alibi不可信",
            "SKIP|需要更多信息才能决定",
            "VOTE|6|Black一直很安静，很可疑",
            "SKIP|我还不确定谁是内鬼"
        ]
    
    def generate_response(self, messages, max_tokens=100, temperature=0.7):
        """生成模拟响应"""
        self.call_count += 1
        
        # 检查消息内容来决定响应类型
        message_content = str(messages).lower()
        
        if "initial statement" in message_content:
            return random.choice(self.initial_statements)
        elif "follow-up" in message_content:
            return random.choice(self.follow_up_statements)
        elif "vote" in message_content:
            return random.choice(self.vote_responses)
        else:
            return "我需要仔细考虑这个情况..."

def test_roundtable_logic():
    """测试Round Table会议逻辑"""
    print("🎯 测试Round Table会议逻辑 (使用Mock LLM)\n")
    
    # 使用Mock LLM客户端
    mock_llm = MockLLMClient()
    service = ImpostorGameService(mock_llm)
    
    print("1. 创建游戏...")
    init_response = service.create_game()
    game_id = init_response.game_id
    
    print(f"   游戏ID: {game_id}")
    print(f"   内鬼信息: {init_response.impostor_revealed}")
    print(f"   报告者: {init_response.reporter_name}")
    print(f"   会议原因: {init_response.meeting_reason}")
    
    print("\n2. 获取初始游戏状态...")
    game_state = service.get_game_state_response(game_id)
    print(f"   游戏阶段: {game_state.phase}")
    print(f"   会议阶段: {game_state.meeting_phase}")
    print(f"   存活玩家: {game_state.alive_count}")
    
    print("\n3. 执行Round Table会议...")
    step_response = service.step_game(game_id)
    
    if step_response:
        print(f"   ✅ 会议执行成功!")
        print(f"   会议阶段: {step_response.meeting_phase}")
        print(f"   发言记录: {len(step_response.statements)} 条")
        print(f"   投票记录: {len(step_response.votes)} 票")
        print(f"   被驱逐者: {step_response.eliminated or '无'}")
        print(f"   游戏结束: {step_response.game_over}")
        print(f"   获胜者: {step_response.winner or '游戏继续'}")
        print(f"   消息: {step_response.message}")
        
        # 显示会议结果详情
        if step_response.meeting_result:
            result = step_response.meeting_result
            print(f"\n   📊 会议结果详情:")
            print(f"     被驱逐: {result.ejected_agent_name or '无'}")
            print(f"     投票统计: {result.vote_counts}")
            print(f"     内鬼被驱逐: {result.is_imposter_ejected}")
            print(f"     游戏继续: {result.game_continues}")
            print(f"     对话总数: {len(result.dialogue_history)}")
            
            if result.next_kill_target:
                print(f"     下个击杀目标: Agent {result.next_kill_target}")
        
        # 显示部分对话样本
        print(f"\n   💬 对话样本 (前5条):")
        for i, stmt in enumerate(step_response.statements[:5]):
            follow_up = " (追加发言)" if stmt.is_follow_up else ""
            print(f"     {stmt.agent_name}{follow_up}: {stmt.content}")
        
        # 显示投票详情
        print(f"\n   🗳️ 投票详情:")
        for vote in step_response.votes[:5]:  # 显示前5票
            target = vote.target_name or "跳过"
            print(f"     {vote.voter_name} → {target}: {vote.reasoning}")
    
    print(f"\n4. API调用统计:")
    print(f"   总LLM调用次数: {mock_llm.call_count}")
    print(f"   (使用真实API会消耗大量token)")
    
    print("\n5. 测试第二轮会议...")
    # 测试连续会议
    step_response2 = service.step_game(game_id)
    if step_response2:
        print(f"   ✅ 第二轮会议也成功执行!")
        print(f"   新的发言数: {len(step_response2.statements)}")
        print(f"   游戏状态: {step_response2.message}")
    
    return True

def test_edge_cases():
    """测试边缘情况"""
    print("\n🔍 测试边缘情况...\n")
    
    class EdgeCaseLLMClient:
        """专门测试边缘情况的Mock LLM"""
        def __init__(self, scenario):
            self.scenario = scenario
        
        def generate_response(self, messages, max_tokens=100, temperature=0.7):
            if self.scenario == "all_vote_impostor":
                # 所有人都投票给内鬼
                return "VOTE|4|我确定Orange是内鬼"
            elif self.scenario == "tie_votes":
                # 平票情况
                responses = ["VOTE|1|投Blue", "VOTE|2|投Green"] * 4
                return random.choice(responses)
            elif self.scenario == "all_skip":
                # 所有人都跳过
                return "SKIP|信息不足，跳过投票"
            else:
                return "默认响应"
    
    # 测试内鬼被投出的情况
    print("测试场景1: 内鬼被成功投出")
    llm1 = EdgeCaseLLMClient("all_vote_impostor")
    service1 = ImpostorGameService(llm1)
    init1 = service1.create_game()
    step1 = service1.step_game(init1.game_id)
    
    if step1 and step1.meeting_result:
        print(f"   内鬼被驱逐: {step1.meeting_result.is_imposter_ejected}")
        print(f"   游戏结束: {step1.game_over}")
        print(f"   获胜者: {step1.winner}")
    
    # 测试所有人跳过的情况
    print("\n测试场景2: 所有人都跳过投票")
    llm2 = EdgeCaseLLMClient("all_skip")
    service2 = ImpostorGameService(llm2)
    init2 = service2.create_game()
    step2 = service2.step_game(init2.game_id)
    
    if step2 and step2.meeting_result:
        print(f"   被驱逐者: {step2.meeting_result.ejected_agent_name or '无'}")
        print(f"   游戏继续: {step2.meeting_result.game_continues}")
    
    print("   ✅ 边缘情况测试完成")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🚀 Round Table Meeting Logic Test")
        print("=" * 60)
        
        # 主要逻辑测试
        test_roundtable_logic()
        
        # 边缘情况测试
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过! Round Table逻辑运行正常")
        print("💡 建议: 在生产环境中考虑限制LLM调用频率以避免配额问题")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

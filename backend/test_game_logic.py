#!/usr/bin/env python3
"""
Among Us Game Logic Test Suite
测试游戏的核心逻辑和AI行为
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.features.impostor_game.service import ImpostorGameService
from src.features.impostor_game.schema import ActionType, GameStatus, GamePhase
from src.features.impostor_game.agents import SupervisorAgent, ContextManager
from src.core.llm_client import LLMClient

def test_game_creation():
    """测试游戏创建功能"""
    print("🎮 Testing Game Creation...")
    
    service = ImpostorGameService()
    init_response = service.create_game()
    
    # 验证基本信息
    assert init_response.game_id is not None
    assert len(init_response.agents) == 8
    assert sum(1 for a in init_response.agents if a.is_impostor) == 1
    
    print(f"✅ Game created successfully!")
    print(f"   Game ID: {init_response.game_id}")
    print(f"   Meeting: {init_response.meeting_reason}")
    print(f"   Impostor: {init_response.impostor_revealed}")
    
    return init_response

def test_agent_behavior():
    """测试AI Agent行为"""
    print("\n🤖 Testing Agent Behavior...")
    
    service = ImpostorGameService()
    init_response = service.create_game()
    game = service.get_game(init_response.game_id)
    
    # 测试SupervisorAgent
    supervisor = SupervisorAgent(service.llm_client)
    actions = supervisor.orchestrate_meeting_step(game, game.agents)
    
    print(f"✅ SupervisorAgent generated {len(actions)} actions")
    for i, action in enumerate(actions):
        agent_name = next(a.name for a in game.agents if a.id == action.agent_id)
        print(f"   {i+1}. {agent_name}: {action.action_type.value} - {action.content[:50]}...")
    
    return init_response.game_id

def test_game_progression():
    """测试游戏进程"""
    print("\n⏭️  Testing Game Progression...")
    
    service = ImpostorGameService()
    init_response = service.create_game()
    game_id = init_response.game_id
    
    # 运行几个游戏步骤
    for step in range(1, 6):
        print(f"\n--- Step {step} ---")
        step_response = service.step_game(game_id)
        
        if not step_response:
            print("❌ Game step failed")
            break
            
        print(f"✅ Step {step_response.step_number} completed")
        print(f"   Actions: {len(step_response.actions)}")
        print(f"   Message: {step_response.message}")
        
        if step_response.game_over:
            print(f"🏆 Game Over! Winner: {step_response.winner}")
            break
            
        # 显示一些行动详情
        for action in step_response.actions[:3]:  # 只显示前3个
            agent_name = next(a.name for a in init_response.agents if a.id == action.agent_id)
            print(f"   • {agent_name}: {action.content[:60]}...")
    
    return game_id

def test_context_manager():
    """测试上下文管理器"""
    print("\n🧠 Testing Context Manager...")
    
    service = ImpostorGameService()
    init_response = service.create_game()
    game = service.get_game(init_response.game_id)
    
    context_manager = ContextManager(service.llm_client)
    
    # 测试卧底和船员的不同上下文
    impostor = next(a for a in game.agents if a.is_impostor)
    crewmate = next(a for a in game.agents if not a.is_impostor)
    
    impostor_context = context_manager.get_agent_context(impostor, game)
    crewmate_context = context_manager.get_agent_context(crewmate, game)
    
    print(f"✅ Context generated successfully")
    print(f"   Impostor context type: {impostor_context['role_type']}")
    print(f"   Impostor strategy: {impostor_context['strategy_hint']}")
    print(f"   Crewmate context type: {crewmate_context['role_type']}")
    print(f"   Crewmate hints: {len(crewmate_context['deduction_hints'])} hints")

def test_voting_mechanism():
    """测试投票机制"""
    print("\n🗳️  Testing Voting Mechanism...")
    
    service = ImpostorGameService()
    init_response = service.create_game()
    game_id = init_response.game_id
    
    # 运行游戏直到有投票
    for step in range(1, 10):
        step_response = service.step_game(game_id)
        if not step_response:
            break
            
        vote_actions = [a for a in step_response.actions if a.action_type == ActionType.VOTE]
        if vote_actions:
            print(f"✅ Found {len(vote_actions)} vote actions in step {step}")
            for vote in vote_actions:
                voter_name = next((a.name for a in init_response.agents if a.id == vote.agent_id), f"Agent{vote.agent_id}")
                
                # Handle cases where target_agent_id might be None or invalid
                if vote.target_agent_id is not None:
                    target_name = next((a.name for a in init_response.agents if a.id == vote.target_agent_id), f"Agent{vote.target_agent_id}")
                    print(f"   • {voter_name} votes for {target_name}: {vote.content[:40]}...")
                else:
                    print(f"   • {voter_name} attempted to vote (no valid target): {vote.content[:40]}...")
            break
        
        if step_response.game_over:
            print(f"🏆 Game ended before voting: {step_response.winner} wins")
            break

def run_full_game_simulation():
    """运行完整游戏模拟"""
    print("\n🎯 Running Full Game Simulation...")
    
    service = ImpostorGameService()
    init_response = service.create_game()
    game_id = init_response.game_id
    
    print(f"🚀 Starting game: {init_response.meeting_reason}")
    print(f"📋 Players: {', '.join(a.name for a in init_response.agents)}")
    print(f"🕵️ Secret: {init_response.impostor_revealed}")
    
    step_count = 0
    while step_count < 15:  # 最多15步
        step_count += 1
        step_response = service.step_game(game_id)
        
        if not step_response:
            print("❌ Game step failed")
            break
            
        print(f"\n--- Step {step_response.step_number} ---")
        print(f"📢 {step_response.message}")
        
        # 显示重要行动
        important_actions = [a for a in step_response.actions 
                           if a.action_type in [ActionType.SPEAK, ActionType.VOTE]]
        
        for action in important_actions[:4]:  # 只显示前4个重要行动
            agent_name = next(a.name for a in init_response.agents if a.id == action.agent_id)
            action_icon = "🗣️" if action.action_type == ActionType.SPEAK else "🗳️"
            print(f"   {action_icon} {agent_name}: {action.content[:70]}...")
        
        if step_response.eliminated:
            print(f"❌ {step_response.eliminated} was eliminated!")
            
        if step_response.game_over:
            print(f"\n🏆 GAME OVER! {step_response.winner} wins!")
            break
    
    return game_id

if __name__ == "__main__":
    print("🎮 Among Us AI Game - Test Suite")
    print("=" * 50)
    
    try:
        # 运行所有测试
        test_game_creation()
        test_agent_behavior()
        test_context_manager()
        test_voting_mechanism()
        test_game_progression()
        
        print("\n" + "=" * 50)
        print("🎯 FULL GAME SIMULATION")
        print("=" * 50)
        run_full_game_simulation()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

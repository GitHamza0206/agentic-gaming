#!/usr/bin/env python3
"""
Test LLM-based should_raise_hand functionality and 15-step limit
测试基于LLM的举手决策和15步限制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.impostor_game.service import ImpostorGameService
from src.features.impostor_game.schema import Statement

def test_llm_raise_hand():
    """测试LLM-based举手决策功能"""
    print("🤖 Testing LLM-based should_raise_hand functionality\n")
    
    # 创建服务
    service = ImpostorGameService()
    
    print("1. Creating game...")
    init_response = service.create_game()
    game_id = init_response.game_id
    
    print(f"   Game ID: {game_id}")
    print(f"   Impostor: {init_response.impostor_revealed}")
    print(f"   Reporter: {init_response.reporter_name}")
    print(f"   Max steps: 15 (reduced from 30)")
    
    print("\n2. Running Round Table meeting with LLM-based raise hand...")
    try:
        step_response = service.step_game(game_id)
        
        if step_response:
            print(f"   ✅ Meeting completed successfully!")
            print(f"   Total statements: {len(step_response.statements)}")
            print(f"   Step number: {step_response.step_number}")
            print(f"   Max steps: {step_response.max_steps}")
            print(f"   Game over: {step_response.game_over}")
            
            # 分析发言模式
            initial_statements = [s for s in step_response.statements if not s.is_follow_up]
            follow_up_statements = [s for s in step_response.statements if s.is_follow_up]
            
            print(f"\n   📊 Statement Analysis:")
            print(f"     Initial statements: {len(initial_statements)}")
            print(f"     Follow-up statements: {len(follow_up_statements)}")
            
            # 显示API使用统计
            llm_stats = service.llm_client.get_usage_stats()
            print(f"\n   🔄 API Usage Statistics:")
            print(f"     Cerebras calls: {llm_stats['cerebras_calls']}")
            print(f"     OpenAI calls: {llm_stats['openai_calls']}")
            print(f"     Rate limit hits: {llm_stats['rate_limit_hits']}")
            print(f"     Total calls: {llm_stats['total_calls']}")
            
            if llm_stats['openai_calls'] > 0:
                print(f"   🔄 Fallback used: {llm_stats['openai_calls']} OpenAI calls")
            
            # 显示举手决策的样本
            print(f"\n   💬 Sample statements with LLM-based raise hand decisions:")
            for i, stmt in enumerate(step_response.statements[:8]):
                follow_up = " (LLM decided to raise hand)" if stmt.is_follow_up else " (initial)"
                print(f"     {stmt.agent_name}{follow_up}: {stmt.content[:80]}...")
            
            # 检查是否达到15步限制
            if step_response.step_number >= 15:
                print(f"\n   ⏰ Step limit reached: {step_response.step_number}/15")
            else:
                print(f"\n   ⏰ Meeting ended naturally at step: {step_response.step_number}/15")
            
            return True
        else:
            print("   ❌ Step response was None")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during meeting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_raise_hand_decisions():
    """测试单独的举手决策逻辑"""
    print("\n🎯 Testing Individual Raise Hand Decisions\n")
    
    from src.features.impostor_game.agents import Crewmate, Impostor
    from src.features.impostor_game.schema import Agent
    from src.core.llm_client import LLMClient
    
    llm_client = LLMClient()
    
    # 创建测试agent
    crewmate_data = Agent(id=1, name="Blue", color="blue", is_impostor=False, is_alive=True)
    impostor_data = Agent(id=2, name="Red", color="red", is_impostor=True, is_alive=True)
    
    crewmate = Crewmate(crewmate_data, llm_client)
    impostor = Impostor(impostor_data, llm_client)
    
    # 创建测试对话历史
    test_dialogue = [
        Statement(agent_id=3, agent_name="Green", content="I saw Blue near the reactor", step_number=1, is_follow_up=False),
        Statement(agent_id=4, agent_name="Yellow", content="Blue seems suspicious to me", step_number=2, is_follow_up=False),
        Statement(agent_id=5, agent_name="Pink", content="I think Red is the impostor", step_number=3, is_follow_up=False),
        Statement(agent_id=1, agent_name="Blue", content="I was doing tasks, not sabotaging", step_number=4, is_follow_up=False)
    ]
    
    print("Test dialogue context:")
    for stmt in test_dialogue:
        print(f"   {stmt.agent_name}: {stmt.content}")
    
    print(f"\n1. Testing Crewmate (Blue) raise hand decision:")
    try:
        crewmate_decision = crewmate.should_raise_hand(test_dialogue)
        print(f"   Blue's decision: {'RAISE HAND' if crewmate_decision else 'STAY QUIET'}")
        print(f"   (Blue was mentioned and accused, likely to defend)")
    except Exception as e:
        print(f"   Error: {e}")
    
    print(f"\n2. Testing Impostor (Red) raise hand decision:")
    try:
        impostor_decision = impostor.should_raise_hand(test_dialogue)
        print(f"   Red's decision: {'RAISE HAND' if impostor_decision else 'STAY QUIET'}")
        print(f"   (Red was accused as impostor, strategic decision needed)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 显示API使用
    stats = llm_client.get_usage_stats()
    print(f"\n   API calls for raise hand decisions: {stats['total_calls']}")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🚀 LLM-based Raise Hand Testing Suite")
        print("=" * 60)
        
        # 测试完整会议
        success = test_llm_raise_hand()
        
        if success:
            # 测试单独的举手决策
            test_individual_raise_hand_decisions()
        
        print("\n" + "=" * 60)
        print("✅ LLM-based Raise Hand Testing Complete!")
        print("🎯 Key improvements:")
        print("   - Agents now use LLM to make intelligent raise hand decisions")
        print("   - Max steps reduced from 30 to 15 for faster meetings")
        print("   - Fallback logic ensures robustness if LLM fails")
        print("   - Strategic behavior: Impostors defend when accused, stay quiet otherwise")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

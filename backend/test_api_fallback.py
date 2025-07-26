#!/usr/bin/env python3
"""
Test API Fallback Functionality
测试Cerebras -> OpenAI API回退机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.llm_client import LLMClient
from src.features.impostor_game.service import ImpostorGameService

def test_llm_client_fallback():
    """测试LLM客户端的回退功能"""
    print("🔄 Testing LLM Client Fallback Functionality\n")
    
    # 创建LLM客户端
    llm_client = LLMClient()
    
    # 测试消息
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in a friendly way."}
    ]
    
    print("1. Testing normal LLM generation...")
    try:
        response = llm_client.generate_response(test_messages, max_tokens=50, temperature=0.7)
        print(f"   ✅ Response: {response}")
        print(f"   📊 Usage stats: {llm_client.get_usage_stats()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return llm_client

def test_roundtable_with_fallback():
    """测试Round Table会议系统的API回退功能"""
    print("\n🎯 Testing Round Table with API Fallback\n")
    
    # 创建服务
    service = ImpostorGameService()
    
    print("1. Creating game...")
    init_response = service.create_game()
    game_id = init_response.game_id
    
    print(f"   Game ID: {game_id}")
    print(f"   Impostor: {init_response.impostor_revealed}")
    print(f"   Reporter: {init_response.reporter_name}")
    
    print("\n2. Running Round Table meeting (with potential fallback)...")
    try:
        step_response = service.step_game(game_id)
        
        if step_response:
            print(f"   ✅ Meeting completed successfully!")
            print(f"   Statements: {len(step_response.statements)}")
            print(f"   Votes: {len(step_response.votes)}")
            print(f"   Eliminated: {step_response.eliminated or 'None'}")
            print(f"   Game over: {step_response.game_over}")
            
            # 显示API使用统计
            llm_stats = service.llm_client.get_usage_stats()
            print(f"\n   📊 API Usage Statistics:")
            print(f"     Cerebras calls: {llm_stats['cerebras_calls']}")
            print(f"     OpenAI calls: {llm_stats['openai_calls']}")
            print(f"     Rate limit hits: {llm_stats['rate_limit_hits']}")
            print(f"     Total calls: {llm_stats['total_calls']}")
            
            if llm_stats['openai_calls'] > 0:
                print(f"   🔄 Fallback was used! OpenAI handled {llm_stats['openai_calls']} calls")
            else:
                print(f"   ✅ Cerebras handled all calls successfully")
            
            # 显示部分对话
            print(f"\n   💬 Sample dialogue:")
            for i, stmt in enumerate(step_response.statements[:3]):
                follow_up = " (follow-up)" if stmt.is_follow_up else ""
                print(f"     {stmt.agent_name}{follow_up}: {stmt.content}")
            
            return True
        else:
            print("   ❌ Step response was None")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during meeting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_meetings():
    """测试多轮会议以验证持续的API回退功能"""
    print("\n🔁 Testing Multiple Meetings for Sustained Fallback\n")
    
    service = ImpostorGameService()
    init_response = service.create_game()
    game_id = init_response.game_id
    
    meeting_count = 0
    max_meetings = 3  # 限制测试轮数
    
    while meeting_count < max_meetings:
        meeting_count += 1
        print(f"Meeting {meeting_count}:")
        
        try:
            step_response = service.step_game(game_id)
            
            if step_response:
                stats = service.llm_client.get_usage_stats()
                print(f"   ✅ Completed - Cerebras: {stats['cerebras_calls']}, OpenAI: {stats['openai_calls']}")
                
                if step_response.game_over:
                    print(f"   🏁 Game ended: {step_response.winner} wins!")
                    break
            else:
                print(f"   ❌ Failed to get step response")
                break
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}...")
            break
    
    # 最终统计
    final_stats = service.llm_client.get_usage_stats()
    print(f"\n📊 Final API Usage Statistics:")
    print(f"   Total meetings: {meeting_count}")
    print(f"   Cerebras calls: {final_stats['cerebras_calls']}")
    print(f"   OpenAI calls: {final_stats['openai_calls']}")
    print(f"   Rate limit hits: {final_stats['rate_limit_hits']}")
    print(f"   Success rate: {((final_stats['total_calls'] - final_stats['rate_limit_hits']) / max(final_stats['total_calls'], 1) * 100):.1f}%")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🚀 API Fallback Testing Suite")
        print("=" * 60)
        
        # 测试基本LLM客户端
        llm_client = test_llm_client_fallback()
        
        # 测试Round Table会议
        success = test_roundtable_with_fallback()
        
        if success:
            # 测试多轮会议
            test_multiple_meetings()
        
        print("\n" + "=" * 60)
        print("✅ API Fallback Testing Complete!")
        print("💡 The system will automatically use OpenAI when Cerebras hits rate limits")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

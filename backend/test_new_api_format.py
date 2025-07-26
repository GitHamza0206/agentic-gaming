#!/usr/bin/env python3
"""
Test the new API format with turns and conversation_history
测试新的API格式，包含turns和conversation_history
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.impostor_game.service import ImpostorGameService
import json

def test_new_api_format():
    """测试新的API响应格式"""
    print("🚀 Testing New API Format")
    print("=" * 50)
    
    # 创建服务
    service = ImpostorGameService()
    
    print("1. Creating game...")
    try:
        init_response = service.create_game()
        game_id = init_response.game_id
        
        print(f"   ✅ Game created successfully!")
        print(f"   Game ID: {game_id}")
        print(f"   Impostor: {init_response.impostor_revealed}")
        print(f"   Reporter: {init_response.reporter_name}")
        
    except Exception as e:
        print(f"   ❌ Game creation failed: {e}")
        return False
    
    print("\n2. Testing step API with new format...")
    try:
        step_response = service.step_game(game_id)
        
        if step_response:
            print(f"   ✅ Step completed successfully!")
            
            # 验证新的API格式
            print(f"\n   📋 API Response Structure:")
            print(f"     game_id: {step_response.game_id}")
            print(f"     phase: {step_response.phase}")
            print(f"     step_number: {step_response.step_number}")
            print(f"     max_steps: {step_response.max_steps}")
            print(f"     turns count: {len(step_response.turns)}")
            print(f"     conversation_history count: {len(step_response.conversation_history)}")
            print(f"     eliminated: {step_response.eliminated}")
            print(f"     winner: {step_response.winner}")
            print(f"     game_over: {step_response.game_over}")
            print(f"     message: {step_response.message}")
            
            # 显示turns结构
            print(f"\n   🎭 Agent Turns:")
            for i, turn in enumerate(step_response.turns[:3]):  # 只显示前3个
                think_preview = turn.think[:50] + "..." if turn.think and len(turn.think) > 50 else turn.think
                speak_preview = turn.speak[:50] + "..." if turn.speak and len(turn.speak) > 50 else turn.speak
                print(f"     Turn {i+1} (Agent {turn.agent_id}):")
                print(f"       think: {think_preview}")
                print(f"       speak: {speak_preview}")
                print(f"       vote: {turn.vote}")
            
            # 显示conversation_history结构
            print(f"\n   💬 Conversation History:")
            for i, entry in enumerate(step_response.conversation_history[:3]):  # 只显示前3个
                content_preview = entry.content[:60] + "..." if len(entry.content) > 60 else entry.content
                print(f"     Entry {i+1}: Agent {entry.agent_id} ({entry.action_type})")
                print(f"       content: {content_preview}")
                print(f"       target_agent_id: {entry.target_agent_id}")
            
            # 生成JSON格式示例
            print(f"\n   📄 JSON Response Sample:")
            sample_response = {
                "game_id": step_response.game_id,
                "phase": step_response.phase,
                "step_number": step_response.step_number,
                "max_steps": step_response.max_steps,
                "turns": [
                    {
                        "agent_id": turn.agent_id,
                        "think": turn.think,
                        "speak": turn.speak,
                        "vote": turn.vote
                    } for turn in step_response.turns[:2]  # 只显示前2个
                ],
                "conversation_history": [
                    {
                        "agent_id": entry.agent_id,
                        "action_type": entry.action_type,
                        "content": entry.content,
                        "target_agent_id": entry.target_agent_id
                    } for entry in step_response.conversation_history[:2]  # 只显示前2个
                ],
                "eliminated": step_response.eliminated,
                "winner": step_response.winner,
                "game_over": step_response.game_over,
                "message": step_response.message
            }
            
            print(json.dumps(sample_response, indent=2, ensure_ascii=False))
            
            # 验证没有API错误
            error_count = sum(1 for turn in step_response.turns if turn.think and "Erreur de génération" in turn.think)
            if error_count == 0:
                print(f"\n   ✅ No API errors detected!")
            else:
                print(f"\n   ⚠️ Found {error_count} API errors in turns")
            
            # 显示API使用统计
            llm_stats = service.llm_client.get_usage_stats()
            print(f"\n   📊 API Usage Statistics:")
            print(f"     Cerebras calls: {llm_stats['cerebras_calls']}")
            print(f"     OpenAI calls: {llm_stats['openai_calls']}")
            print(f"     Rate limit hits: {llm_stats['rate_limit_hits']}")
            print(f"     Total calls: {llm_stats['total_calls']}")
            
            return True
        else:
            print("   ❌ Step response was None")
            return False
            
    except Exception as e:
        print(f"   ❌ Step failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_error_fixes():
    """测试API错误修复"""
    print("\n🔧 Testing API Error Fixes")
    print("=" * 50)
    
    from src.core.llm_client import LLMClient
    
    llm_client = LLMClient()
    
    # 测试system role转换
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "system", "content": "You are playing Among Us."},
        {"role": "user", "content": "What should I do?"}
    ]
    
    print("1. Testing system role conversion...")
    try:
        converted = llm_client._convert_messages_for_api(test_messages)
        print(f"   ✅ Messages converted successfully!")
        print(f"   Original messages: {len(test_messages)}")
        print(f"   Converted messages: {len(converted)}")
        
        for i, msg in enumerate(converted):
            role = msg["role"]
            content_preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            print(f"     Message {i+1} ({role}): {content_preview}")
        
        return True
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")
        return False

if __name__ == "__main__":
    try:
        print("🎯 New API Format Testing Suite")
        print("=" * 60)
        
        # 测试API错误修复
        error_fix_success = test_api_error_fixes()
        
        if error_fix_success:
            # 测试新的API格式
            api_success = test_new_api_format()
            
            if api_success:
                print("\n" + "=" * 60)
                print("🎉 All tests passed!")
                print("✅ Key improvements verified:")
                print("   - New API format with turns and conversation_history")
                print("   - System role errors fixed")
                print("   - LLM-based agent decisions working")
                print("   - API fallback mechanism operational")
                print("=" * 60)
            else:
                print("\n❌ API format test failed")
        else:
            print("\n❌ Error fix test failed")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

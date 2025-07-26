#!/usr/bin/env python3
"""
Quick Among Us Game Test
快速测试游戏核心功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def quick_test():
    print("🎮 Quick Among Us Game Test")
    print("=" * 40)
    
    try:
        # 导入模块
        from src.features.impostor_game.service import ImpostorGameService
        from src.features.impostor_game.schema import ActionType
        print("✅ Modules imported successfully")
        
        # 创建游戏服务
        service = ImpostorGameService()
        print("✅ Game service created")
        
        # 初始化游戏
        print("\n🚀 Initializing game...")
        init_response = service.create_game()
        game_id = init_response.game_id
        
        print(f"✅ Game created: {game_id[:8]}...")
        print(f"📢 {init_response.message}")
        print(f"👥 Players: {', '.join(a.name for a in init_response.agents)}")
        print(f"🕵️ {init_response.impostor_revealed}")
        
        # 运行一步游戏
        print(f"\n⏭️  Running game step...")
        step_response = service.step_game(game_id)
        
        if step_response:
            print(f"✅ Step {step_response.step_number} completed")
            print(f"📝 {len(step_response.actions)} actions taken")
            print(f"💬 {step_response.message}")
            
            # 显示前几个行动
            print(f"\n📋 Sample actions:")
            for i, action in enumerate(step_response.actions[:3]):
                agent_name = next(a.name for a in init_response.agents if a.id == action.agent_id)
                print(f"   {i+1}. {agent_name}: {action.action_type.value}")
                print(f"      Content: {action.content[:60]}...")
        else:
            print("❌ Game step failed")
            return False
        
        # 检查游戏状态
        print(f"\n📊 Checking game state...")
        state_response = service.get_game_state_response(game_id)
        
        if state_response:
            print(f"✅ Game state retrieved")
            print(f"   Status: {state_response.status}")
            print(f"   Phase: {state_response.phase}")
            print(f"   Alive players: {state_response.alive_count}")
            print(f"   Impostor alive: {state_response.impostor_alive}")
        else:
            print("❌ Failed to get game state")
            return False
        
        print(f"\n🎉 All core functions working!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print(f"\n✅ Quick test PASSED! Your game is ready to use.")
        print(f"\n🚀 Next steps:")
        print(f"   1. Start the API server: uvicorn src.main:app --reload")
        print(f"   2. Test API endpoints: python test_api.py")
        print(f"   3. Run full simulation: python test_game_logic.py")
    else:
        print(f"\n❌ Quick test FAILED. Please check the errors above.")

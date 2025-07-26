#!/usr/bin/env python3
"""
Verify Player Count Configuration
验证7个船员+1个卧底的配置
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def verify_player_count():
    print("🔍 Verifying Player Count Configuration")
    print("=" * 45)
    
    try:
        from src.features.impostor_game.service import ImpostorGameService
        
        service = ImpostorGameService()
        
        # 测试多次游戏创建以确保配置正确
        for test_num in range(3):
            print(f"\n🎮 Test Game #{test_num + 1}")
            init_response = service.create_game()
            
            # 统计玩家类型
            total_players = len(init_response.agents)
            crewmates = [a for a in init_response.agents if not a.is_impostor]
            impostors = [a for a in init_response.agents if a.is_impostor]
            
            print(f"   Total Players: {total_players}")
            print(f"   Crewmates: {len(crewmates)}")
            print(f"   Impostors: {len(impostors)}")
            
            # 验证配置
            if total_players == 8 and len(crewmates) == 7 and len(impostors) == 1:
                print(f"   ✅ Configuration correct!")
            else:
                print(f"   ❌ Configuration incorrect!")
                return False
            
            print(f"   📢 {init_response.message}")
            print(f"   🕵️ Impostor: {impostors[0].name} ({impostors[0].color})")
            print(f"   👥 Crewmates: {', '.join(c.name for c in crewmates)}")
        
        print(f"\n✅ All tests passed! Configuration is correct:")
        print(f"   • 8 total players")
        print(f"   • 7 crewmates")
        print(f"   • 1 impostor")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_player_count()
    if success:
        print(f"\n🎉 Player count configuration is working perfectly!")
    else:
        print(f"\n💥 There's an issue with the player count configuration.")

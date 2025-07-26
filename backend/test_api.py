#!/usr/bin/env python3
"""
Among Us API Test Script
测试REST API接口
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/impostor-game"

def test_health_check():
    """测试健康检查接口"""
    print("🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_game_initialization():
    """测试游戏初始化"""
    print("\n🎮 Testing Game Initialization...")
    try:
        response = requests.post(f"{BASE_URL}/init")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Game initialized successfully!")
            print(f"   Game ID: {data['game_id']}")
            print(f"   Message: {data['message']}")
            print(f"   Players: {len(data['agents'])}")
            return data['game_id']
        else:
            print(f"❌ Game initialization failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Game initialization error: {e}")
        return None

def test_game_step(game_id):
    """测试游戏步骤"""
    print(f"\n⏭️  Testing Game Step for {game_id}...")
    try:
        response = requests.post(f"{BASE_URL}/step/{game_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Game step completed!")
            print(f"   Step: {data['step_number']}")
            print(f"   Actions: {len(data['actions'])}")
            print(f"   Message: {data['message']}")
            if data.get('eliminated'):
                print(f"   Eliminated: {data['eliminated']}")
            if data.get('game_over'):
                print(f"   🏆 Game Over! Winner: {data['winner']}")
            return data
        else:
            print(f"❌ Game step failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Game step error: {e}")
        return None

def test_game_state(game_id):
    """测试游戏状态查询"""
    print(f"\n📊 Testing Game State for {game_id}...")
    try:
        response = requests.get(f"{BASE_URL}/game/{game_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Game state retrieved!")
            print(f"   Status: {data['status']}")
            print(f"   Phase: {data['phase']}")
            print(f"   Step: {data['step_number']}/{data['max_steps']}")
            print(f"   Alive: {data['alive_count']}")
            print(f"   Impostor alive: {data['impostor_alive']}")
            return data
        else:
            print(f"❌ Game state failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Game state error: {e}")
        return None

def run_full_api_test():
    """运行完整API测试"""
    print("🌐 Among Us API - Full Test Suite")
    print("=" * 50)
    
    # 1. 健康检查
    if not test_health_check():
        print("❌ Server is not running. Please start the server first.")
        return
    
    # 2. 初始化游戏
    game_id = test_game_initialization()
    if not game_id:
        print("❌ Cannot proceed without game ID")
        return
    
    # 3. 查询初始状态
    test_game_state(game_id)
    
    # 4. 运行几个游戏步骤
    for step in range(1, 6):
        print(f"\n{'='*20} STEP {step} {'='*20}")
        step_data = test_game_step(game_id)
        if not step_data:
            break
        
        # 显示一些行动细节
        if step_data.get('actions'):
            print("\n📝 Recent Actions:")
            for i, action in enumerate(step_data['actions'][:3]):
                print(f"   {i+1}. Agent {action['agent_id']}: {action['action_type']} - {action['content'][:50]}...")
        
        if step_data.get('game_over'):
            print(f"\n🎉 Game completed! Winner: {step_data['winner']}")
            break
        
        # 短暂暂停
        time.sleep(1)
    
    # 5. 最终状态
    print(f"\n{'='*20} FINAL STATE {'='*20}")
    test_game_state(game_id)
    
    print("\n✅ API test completed!")

if __name__ == "__main__":
    run_full_api_test()

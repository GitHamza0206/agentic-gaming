#!/usr/bin/env python3
"""
Test script for the integrated Round Table meeting system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.impostor_game.service import ImpostorGameService
from src.core.llm_client import LLMClient

def test_round_table_integration():
    """Test the full round table meeting integration"""
    print("=== TESTING ROUND TABLE MEETING INTEGRATION ===\n")
    
    # Initialize service with mock LLM client
    class MockLLMClient:
        def generate_response(self, messages, max_tokens=100, temperature=0.7):
            # Return simple placeholder responses for testing
            if "initial statement" in str(messages).lower():
                return "I think we need to be careful and watch for suspicious behavior."
            elif "follow-up" in str(messages).lower():
                return "I agree with what was said earlier."
            elif "vote" in str(messages).lower():
                return "SKIP|Need more information to decide"
            else:
                return "I'm thinking about this situation..."
    
    llm_client = MockLLMClient()
    service = ImpostorGameService(llm_client)
    
    # Create a new game
    print("1. Creating new game...")
    init_response = service.create_game()
    print(f"   Game created: {init_response.game_id}")
    print(f"   Impostor revealed: {init_response.impostor_revealed}")
    print(f"   Reporter: {init_response.reporter_name}")
    print(f"   Reason: {init_response.meeting_reason}")
    
    # Get initial game state
    print("\n2. Getting initial game state...")
    game_state = service.get_game_state_response(init_response.game_id)
    if game_state:
        print(f"   Phase: {game_state.phase}")
        print(f"   Meeting Phase: {game_state.meeting_phase}")
        print(f"   Alive agents: {game_state.alive_count}")
        print(f"   Impostor alive: {game_state.impostor_alive}")
    
    # Execute one step (full round table meeting)
    print("\n3. Executing round table meeting...")
    step_response = service.step_game(init_response.game_id)
    if step_response:
        print(f"   Meeting completed!")
        print(f"   Phase: {step_response.phase}")
        print(f"   Meeting Phase: {step_response.meeting_phase}")
        print(f"   Statements: {len(step_response.statements)}")
        print(f"   Votes: {len(step_response.votes)}")
        print(f"   Eliminated: {step_response.eliminated or 'None'}")
        print(f"   Winner: {step_response.winner or 'Game continues'}")
        print(f"   Game over: {step_response.game_over}")
        print(f"   Message: {step_response.message}")
        
        # Show some dialogue samples
        if step_response.statements:
            print(f"\n   Sample statements:")
            for i, stmt in enumerate(step_response.statements[:3]):
                follow_up = " (follow-up)" if stmt.is_follow_up else ""
                print(f"     {stmt.agent_name}{follow_up}: {stmt.content}")
        
        # Show meeting result if available
        if step_response.meeting_result:
            result = step_response.meeting_result
            print(f"\n   Meeting Result:")
            print(f"     Ejected: {result.ejected_agent_name or 'None'}")
            print(f"     Vote counts: {result.vote_counts}")
            print(f"     Impostor ejected: {result.is_imposter_ejected}")
            print(f"     Game continues: {result.game_continues}")
            if result.next_kill_target:
                print(f"     Next kill target: Agent {result.next_kill_target}")
    
    # Get final game state
    print("\n4. Getting final game state...")
    final_state = service.get_game_state_response(init_response.game_id)
    if final_state:
        print(f"   Final phase: {final_state.phase}")
        print(f"   Final alive count: {final_state.alive_count}")
        print(f"   Final winner: {final_state.winner or 'TBD'}")
        print(f"   Dialogue history: {len(final_state.dialogue_history)} exchanges")
    
    print("\n=== INTEGRATION TEST COMPLETED ===")
    return True

if __name__ == "__main__":
    try:
        test_round_table_integration()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

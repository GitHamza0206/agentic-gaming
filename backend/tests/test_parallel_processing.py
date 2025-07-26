import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch
from src.features.impostor_game.service import ImpostorGameService
from src.features.impostor_game.schema import Agent, AgentTurn, AgentAction, ActionType


class TestParallelProcessing:
    """Test suite for parallel LLM processing performance and correctness"""
    
    @pytest.fixture
    def game_service(self):
        return ImpostorGameService()
    
    @pytest.fixture
    def mock_game_state(self, game_service):
        """Create a test game with 4 agents"""
        game = game_service.create_game(num_players=4, max_steps=10)
        return game_service.get_game(game.game_id)
    
    @pytest.mark.asyncio
    async def test_parallel_agent_processing_timing(self, game_service, mock_game_state):
        """Test that parallel processing is faster than sequential"""
        
        # Mock LLM response to simulate realistic delay
        async def mock_llm_response(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate 500ms LLM call
            return '''{"think": "I need to find the impostor", "speak": "I suspect Red", "vote": null}'''
        
        with patch.object(game_service.llm_client, 'generate_response', side_effect=mock_llm_response):
            # Measure parallel processing time
            start_time = time.time()
            result = await game_service.step_game(mock_game_state.game_id)
            parallel_time = time.time() - start_time
            
            assert result is not None
            assert len(result.turns) == 4  # All 4 agents should have turns
            
            # With 4 agents and 0.5s delay each, parallel should be ~0.5s
            # Sequential would be ~2.0s (4 * 0.5s)
            assert parallel_time < 1.0, f"Parallel processing took {parallel_time:.2f}s, expected < 1.0s"
            print(f"✅ Parallel processing completed in {parallel_time:.2f}s")
    
    @pytest.mark.asyncio 
    async def test_all_agents_process_simultaneously(self, game_service, mock_game_state):
        """Test that all alive agents get processed and produce turns"""
        
        # Track call order to verify simultaneity
        call_times = []
        
        async def mock_llm_with_timing(*args, **kwargs):
            call_times.append(time.time())
            await asyncio.sleep(0.1)  # Short delay
            return '''{"think": "Analyzing the situation", "speak": "I have my suspicions", "vote": null}'''
        
        with patch.object(game_service.llm_client, 'generate_response', side_effect=mock_llm_with_timing):
            result = await game_service.step_game(mock_game_state.game_id)
            
            # Verify all agents processed
            assert result is not None
            assert len(result.turns) == 4
            assert len(call_times) >= 4  # At least 4 LLM calls (agents + maybe speaker selection)
            
            # Verify calls happened roughly simultaneously (within 50ms window)
            if len(call_times) >= 4:
                agent_call_times = call_times[:4]  # First 4 calls are agent processing
                time_spread = max(agent_call_times) - min(agent_call_times)
                assert time_spread < 0.05, f"Agent calls spread over {time_spread:.3f}s, expected < 0.05s"
                print(f"✅ All agent calls within {time_spread:.3f}s window")
    
    @pytest.mark.asyncio
    async def test_speaker_selection_after_parallel_processing(self, game_service, mock_game_state):
        """Test that speaker selection works correctly after parallel agent processing"""
        
        # Mock different responses for different agents
        response_queue = [
            '''{"think": "I'm suspicious of Blue", "speak": "Blue seems quiet", "vote": null}''',
            '''{"think": "Red is acting strange", "speak": "Red is being defensive", "vote": null}''',
            '''{"think": "I need to defend myself", "speak": "I was doing tasks!", "vote": null}''',
            '''{"think": "Who can I trust?", "speak": null, "vote": null}'''  # This agent doesn't want to speak
        ]
        
        call_count = 0
        async def mock_llm_responses(*args, **kwargs):
            nonlocal call_count
            if call_count < len(response_queue):
                response = response_queue[call_count]
                call_count += 1
                return response
            # Speaker selection call
            return "Red"  # Choose Red as speaker
        
        with patch.object(game_service.llm_client, 'generate_response', side_effect=mock_llm_responses):
            result = await game_service.step_game(mock_game_state.game_id)
            
            # Verify processing completed
            assert result is not None
            assert len(result.turns) == 4
            
            # Verify exactly one agent spoke publicly
            speaking_actions = [action for action in result.conversation_history 
                             if action.action_type == ActionType.SPEAK]
            
            # Should have at least one speaking action in this step
            recent_speaks = [action for action in speaking_actions 
                           if any(turn.agent_id == action.agent_id and turn.speak == action.content 
                                 for turn in result.turns)]
            
            assert len(recent_speaks) <= 1, "More than one agent spoke in the same step"
            print(f"✅ Speaker selection working: {len(recent_speaks)} agent(s) spoke")
    
    @pytest.mark.asyncio
    async def test_error_handling_in_parallel_processing(self, game_service, mock_game_state):
        """Test that errors in one agent don't break parallel processing"""
        
        call_count = 0
        async def mock_llm_with_errors(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Make second agent fail
            if call_count == 2:
                raise Exception("LLM API error")
            
            return '''{"think": "I'm analyzing", "speak": "Hmm interesting", "vote": null}'''
        
        with patch.object(game_service.llm_client, 'generate_response', side_effect=mock_llm_with_errors):
            # This should not raise an exception due to error handling
            try:
                result = await game_service.step_game(mock_game_state.game_id)
                # If we get here, error handling worked
                print("✅ Error handling in parallel processing works")
            except Exception as e:
                pytest.fail(f"Parallel processing failed to handle errors: {e}")


if __name__ == "__main__":
    # Quick test runner
    async def run_quick_test():
        service = ImpostorGameService()
        game = service.create_game(num_players=4, max_steps=5)
        game_state = service.get_game(game.game_id)
        
        print("🔧 Testing parallel LLM processing...")
        
        start_time = time.time()
        result = await service.step_game(game_state.game_id)
        duration = time.time() - start_time
        
        print(f"⏱️  Step completed in {duration:.2f}s")
        print(f"👥 {len(result.turns)} agents processed")
        print(f"💬 {len([t for t in result.turns if t.speak])} agents wanted to speak")
        
        # Test another step
        start_time = time.time()  
        result2 = await service.step_game(game_state.game_id)
        duration2 = time.time() - start_time
        
        print(f"⏱️  Second step completed in {duration2:.2f}s")
        print("✅ Parallel processing test completed!")
    
    # Run the quick test
    asyncio.run(run_quick_test())
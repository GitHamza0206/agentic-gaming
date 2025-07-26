import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';

interface Agent {
  id: number;
  name: string;
  color: string;
  is_impostor: boolean;
  is_alive: boolean;
}

interface AgentAction {
  agent_id: number;
  action_type: string;
  content: string;
  target_agent_id?: number;
}

interface AgentTurn {
  agent_id: number;
  think: string;
  speak?: string;
  vote?: number;
}

interface GameData {
  game_id: string;
  agents: Agent[];
  conversation_history: AgentAction[];
  step_number: number;
  max_steps: number;
  game_over: boolean;
  winner?: string;
  message: string;
}

const AmongUsSimulation = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [phase, setPhase] = useState('simulation');
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // API Configuration
  const API_BASE = 'http://localhost:8000';

  // Initialize game
  const initializeGame = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE}/impostor-game/init?num_players=4`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setGameData({
        game_id: data.game_id,
        agents: data.agents,
        conversation_history: [],
        step_number: 0,
        max_steps: 30,
        game_over: false,
        message: data.message
      });
      setPhase('emergency_meeting');
      // Keep currentStep at 25, don't reset it
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize game');
    } finally {
      setLoading(false);
    }
  };

  // Step game forward
  const stepGame = async () => {
    if (!gameData) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/impostor-game/step/${gameData.game_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setGameData({
        ...gameData,
        conversation_history: data.conversation_history,
        step_number: data.step_number,
        game_over: data.game_over,
        winner: data.winner,
        message: data.message
      });
      
      setCurrentStep(data.step_number);
      
      // Switch to emergency meeting phase at step 25
      if (data.step_number >= 25) {
        setPhase('emergency_meeting');
      }
      
      if (data.game_over || data.step_number >= 30) {
        setIsPlaying(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to step game');
      setIsPlaying(false);
    } finally {
      setLoading(false);
    }
  };

  // Initialize game only when reaching step 30
  useEffect(() => {
    if (currentStep === 30 && !gameData) {
      initializeGame();
    }
  }, [currentStep, gameData]);

  // Game Master Scenario Data (keeping for visual simulation)
  const gameScenario = [
    {step: 0, agents: {red: {location: 'Cafeteria', action: 'starts doing wiring task', met: ['blue', 'green', 'yellow']}, blue: {location: 'Cafeteria', action: 'starts doing fuel task', met: ['red', 'green', 'yellow']}, green: {location: 'Cafeteria', action: 'starts doing garbage disposal task', met: ['red', 'blue', 'yellow']}, yellow: {location: 'Cafeteria', action: 'pretends to do card swipe task', met: ['red', 'blue', 'green']}}},
    {step: 1, agents: {red: {location: 'Cafeteria', action: 'continues wiring task', met: ['blue', 'green', 'yellow']}, blue: {location: 'Cafeteria', action: 'continues fuel task', met: ['red', 'green', 'yellow']}, green: {location: 'Cafeteria', action: 'continues garbage disposal task', met: ['red', 'blue', 'yellow']}, yellow: {location: 'Cafeteria', action: 'fake struggling with card swipe', met: ['red', 'blue', 'green']}}},
    {step: 2, agents: {red: {location: 'Cafeteria', action: 'finishes wiring task', met: ['blue', 'green', 'yellow']}, blue: {location: 'Cafeteria', action: 'finishes fuel task', met: ['red', 'green', 'yellow']}, green: {location: 'Cafeteria', action: 'finishes garbage disposal task', met: ['red', 'blue', 'yellow']}, yellow: {location: 'Cafeteria', action: 'fake finishes card swipe', met: ['red', 'blue', 'green']}}},
    {step: 3, agents: {red: {location: 'Hallway', action: 'starts moving toward Electrical', met: []}, blue: {location: 'Hallway', action: 'starts moving toward Navigation', met: []}, green: {location: 'Cafeteria', action: 'remains in Cafeteria, starts second task', met: ['yellow']}, yellow: {location: 'Cafeteria', action: 'remains in Cafeteria with green', met: ['green']}}},
    {step: 4, agents: {red: {location: 'Hallway', action: 'walking toward Electrical', met: []}, blue: {location: 'Hallway', action: 'walking toward Navigation', met: []}, green: {location: 'Cafeteria', action: 'working on download task', met: ['yellow']}, yellow: {location: 'Cafeteria', action: 'pretends to do another cafeteria task', met: ['green']}}},
    {step: 5, agents: {red: {location: 'Electrical', action: 'enters Electrical room', met: []}, blue: {location: 'Navigation', action: 'enters Navigation room', met: []}, green: {location: 'Cafeteria', action: 'finishes download task', met: ['yellow']}, yellow: {location: 'Cafeteria', action: 'finishes fake cafeteria task', met: ['green']}}},
    {step: 6, agents: {red: {location: 'Electrical', action: 'starts electrical wiring task', met: []}, blue: {location: 'Navigation', action: 'starts navigation calibration', met: []}, green: {location: 'Hallway', action: 'starts moving toward Navigation', met: []}, yellow: {location: 'Hallway', action: 'starts moving toward Electrical', met: []}}},
    {step: 7, agents: {red: {location: 'Electrical', action: 'working on electrical wiring', met: []}, blue: {location: 'Navigation', action: 'working on navigation calibration', met: []}, green: {location: 'Hallway', action: 'walking toward Navigation', met: ['yellow']}, yellow: {location: 'Hallway', action: 'walking toward Electrical', met: ['green']}}},
    {step: 8, agents: {red: {location: 'Electrical', action: 'continues electrical wiring', met: []}, blue: {location: 'Navigation', action: 'continues navigation calibration', met: []}, green: {location: 'Hallway', action: 'reaches Navigation room entrance', met: []}, yellow: {location: 'Hallway', action: 'reaches Electrical room entrance', met: []}}},
    {step: 9, agents: {red: {location: 'Electrical', action: 'nearly finished electrical wiring', met: ['yellow']}, blue: {location: 'Navigation', action: 'finishes navigation calibration', met: ['green']}, green: {location: 'Navigation', action: 'enters Navigation room', met: ['blue']}, yellow: {location: 'Electrical', action: 'enters Electrical room', met: ['red']}}},
    {step: 10, agents: {red: {location: 'Electrical', action: 'finishes electrical wiring task', met: ['yellow']}, blue: {location: 'Navigation', action: 'starts second navigation task', met: ['green']}, green: {location: 'Navigation', action: 'starts navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'pretends to start electrical task', met: ['red']}}},
    {step: 11, agents: {red: {location: 'Electrical', action: 'starts second electrical task', met: ['yellow']}, blue: {location: 'Navigation', action: 'working on navigation task', met: ['green']}, green: {location: 'Navigation', action: 'working on navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'fake working on electrical task', met: ['red']}}},
    {step: 12, agents: {red: {location: 'Electrical', action: 'working on electrical task', met: ['yellow']}, blue: {location: 'Navigation', action: 'finishes navigation task', met: ['green']}, green: {location: 'Navigation', action: 'continues navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'continues fake electrical work', met: ['red']}}},
    {step: 13, agents: {red: {location: 'Electrical', action: 'finishes electrical task, starts leaving', met: ['yellow']}, blue: {location: 'Navigation', action: 'starts third navigation task', met: ['green']}, green: {location: 'Navigation', action: 'finishes navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'notices red leaving', met: ['red']}}},
    {step: 14, agents: {red: {location: 'Hallway', action: 'exits Electrical room', met: []}, blue: {location: 'Navigation', action: 'working on navigation task', met: ['green']}, green: {location: 'Navigation', action: 'starts second navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'alone in Electrical, stops pretending', met: []}}},
    {step: 15, agents: {red: {location: 'Hallway', action: 'walking toward Cafeteria', met: []}, blue: {location: 'Navigation', action: 'continues navigation task', met: ['green']}, green: {location: 'Navigation', action: 'working on navigation task', met: ['blue']}, yellow: {location: 'Hallway', action: 'leaves Electrical, moves toward Navigation', met: []}}},
    {step: 16, agents: {red: {location: 'Cafeteria', action: 'reaches Cafeteria', met: []}, blue: {location: 'Navigation', action: 'finishes navigation task', met: ['green']}, green: {location: 'Navigation', action: 'continues navigation task', met: ['blue']}, yellow: {location: 'Hallway', action: 'walking toward Navigation', met: []}}},
    {step: 17, agents: {red: {location: 'Cafeteria', action: 'starts cafeteria task', met: []}, blue: {location: 'Hallway', action: 'starts moving toward Cafeteria', met: ['yellow']}, green: {location: 'Navigation', action: 'finishes navigation task, starts leaving', met: []}, yellow: {location: 'Hallway', action: 'walking toward Navigation, crosses paths with blue', met: ['blue']}}},
    {step: 18, agents: {red: {location: 'Cafeteria', action: 'working on cafeteria task', met: []}, blue: {location: 'Hallway', action: 'continues toward Cafeteria', met: []}, green: {location: 'Hallway', action: 'exits Navigation room, walking', met: []}, yellow: {location: 'Navigation', action: 'reaches Navigation room', met: []}}},
    {step: 19, agents: {red: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'enters Cafeteria', met: ['red']}, green: {location: 'Hallway', action: 'walking toward Electrical', met: []}, yellow: {location: 'Navigation', action: 'enters Navigation room, pretends to do task', met: []}}},
    {step: 20, agents: {red: {location: 'Cafeteria', action: 'working on cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'starts cafeteria task', met: ['red']}, green: {location: 'Hallway', action: 'continues toward Electrical', met: []}, yellow: {location: 'Hallway', action: 'quickly leaves Navigation, follows green toward Electrical', met: []}}},
    {step: 21, agents: {red: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'working on cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'enters Electrical room', met: []}, yellow: {location: 'Hallway', action: 'reaches Electrical room entrance', met: []}}},
    {step: 22, agents: {red: {location: 'Cafeteria', action: 'finishes cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'starts electrical task', met: ['yellow']}, yellow: {location: 'Electrical', action: 'enters Electrical room', met: ['green']}}},
    {step: 23, agents: {red: {location: 'Cafeteria', action: 'starts second cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'finishes cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'working on electrical task', met: ['yellow'], status: 'alive'}, yellow: {location: 'Electrical', action: 'kills green', met: ['green']}}},
    {step: 24, agents: {red: {location: 'Cafeteria', action: 'working on cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'starts second cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Hallway', action: 'quickly leaves Electrical', met: []}}},
    {step: 25, agents: {red: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'working on cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Hallway', action: 'walking quickly toward Cafeteria', met: []}}},
    {step: 26, agents: {red: {location: 'Cafeteria', action: 'finishes cafeteria task', met: ['blue', 'yellow']}, blue: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['red', 'yellow']}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Cafeteria', action: 'enters Cafeteria, pretends to have been doing tasks', met: ['red', 'blue']}}},
    {step: 27, agents: {red: {location: 'Hallway', action: 'starts moving toward Electrical', met: []}, blue: {location: 'Hallway', action: 'finishes cafeteria task, starts moving toward Navigation', met: []}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Cafeteria', action: 'remains in Cafeteria, does fake task to establish alibi', met: []}}},
    {step: 28, agents: {red: {location: 'Hallway', action: 'walking toward Electrical', met: []}, blue: {location: 'Hallway', action: 'walking toward Navigation', met: []}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Hallway', action: 'finishes fake cafeteria task, starts moving toward Navigation', met: []}}},
    {step: 29, agents: {red: {location: 'Hallway', action: 'reaches Electrical room entrance', met: []}, blue: {location: 'Navigation', action: 'enters Navigation room', met: []}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Hallway', action: 'walking toward Navigation', met: []}}},
    {step: 30, agents: {red: {location: 'Electrical', action: 'enters Electrical, discovers green\'s dead body, calls emergency meeting', met: []}, blue: {location: 'Cafeteria', action: 'hears emergency meeting call, walks to meeting table', met: []}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Cafeteria', action: 'hears emergency meeting call, walks to meeting table', met: []}}}
  ];

  // Room positions for visual layout (adjusted for better fit)
  const roomPositions = {
    'Cafeteria': { x: 100, y: 100, width: 140, height: 90, color: '#ffeb3b' },
    'Electrical': { x: 380, y: 100, width: 120, height: 90, color: '#f44336' },
    'Navigation': { x: 100, y: 280, width: 120, height: 90, color: '#2196f3' },
    'Hallway': { x: 280, y: 190, width: 100, height: 60, color: '#9e9e9e' }
  };

  // Agent colors
  const agentColors = {
    red: '#f44336',
    blue: '#2196f3',
    green: '#4caf50',
    yellow: '#ffeb3b'
  };


  // Auto-advance simulation 
  useEffect(() => {
    let interval;
    if (isPlaying && currentStep < 30 && phase === 'simulation') {
      interval = setInterval(() => {
        setCurrentStep(prev => {
          const nextStep = prev + 1;
          
          // At step 30, pause for 2 seconds then switch to emergency meeting
          if (nextStep === 30) {
            setTimeout(() => {
              setPhase('emergency_meeting');
              // API will be initialized by the other useEffect
            }, 2000); // 2 second pause
          }
          
          return nextStep;
        });
      }, 500); // 0.5 seconds for visual simulation
    }
    
    return () => clearInterval(interval);
  }, [isPlaying, currentStep, phase]);

  // Separate useEffect for API steps (30+) - Run steps until max_steps (30 total)
  useEffect(() => {
    let timeout;
    if (isPlaying && gameData && currentStep >= 30 && !gameData.game_over && phase === 'emergency_meeting' && gameData.step_number < gameData.max_steps) {
      // Launch next step automatically after receiving response, with a small delay for reading
      timeout = setTimeout(() => {
        stepGame();
      }, 2000); // 2 seconds delay for reading messages
    }
    
    return () => clearTimeout(timeout);
  }, [isPlaying, currentStep, gameData, phase]);

  const resetSimulation = () => {
    setCurrentStep(0);
    setIsPlaying(false);
    setPhase('simulation');
    setGameData(null); // Clear API data
    setError(null);
  };

  // Map agent colors to hex values
  const getAgentColor = (color: string) => {
    const colorMap: { [key: string]: string } = {
      'red': '#f44336',
      'blue': '#2196f3', 
      'green': '#4caf50',
      'yellow': '#ffeb3b',
      'pink': '#e91e63',
      'orange': '#ff9800',
      'black': '#424242',
      'white': '#fafafa'
    };
    return colorMap[color.toLowerCase()] || '#9e9e9e';
  };

  // Get agent by ID
  const getAgentById = (id: number) => {
    return gameData?.agents.find(agent => agent.id === id);
  };

  const currentStepData = gameScenario[currentStep] || gameScenario[0];

  return (
    <div className="w-full h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden flex flex-col">
      {/* Space background elements */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-10 left-10 w-2 h-2 bg-white rounded-full animate-pulse"></div>
        <div className="absolute top-20 right-20 w-1 h-1 bg-yellow-300 rounded-full animate-ping"></div>
        <div className="absolute bottom-20 left-1/4 w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
        <div className="absolute top-1/3 right-1/3 w-1 h-1 bg-blue-300 rounded-full animate-ping"></div>
        <div className="absolute bottom-1/3 right-10 w-2 h-2 bg-purple-300 rounded-full animate-pulse"></div>
      </div>
      
      <div className="relative z-10 w-full max-w-[95vw] mx-auto p-2 h-full flex flex-col">
        <div className="bg-gray-900 rounded-xl shadow-2xl border-2 border-cyan-400 p-4 flex-1 flex flex-col overflow-hidden"
             style={{background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)'}}>
        {/* Loading State */}
        {loading && phase === 'simulation' && (
          <div className="text-center py-6">
            <div className="inline-block w-12 h-12 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
            <div className="text-lg text-cyan-300 mt-2 font-bold">Loading Crewmates...</div>
          </div>
        )}
        
        {/* Error State */}
        {error && (
          <div className="bg-red-900 border border-red-400 text-red-200 px-4 py-2 rounded-lg mb-3 border-dashed">
            <div className="flex items-center gap-2">
              <span className="text-lg">⚠️</span>
              <div>
                <strong className="font-bold text-red-300">Emergency Alert:</strong> {error}
              </div>
            </div>
          </div>
        )}
        
        {/* Header and Controls - Hidden during emergency meeting */}
        {phase === 'simulation' && (
          <>
            <div className="text-center mb-4">
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 mb-2 tracking-wide">
                🚀 AMONG US 🛸
              </h1>
              <p className="text-lg text-cyan-300 font-bold">Multi-Agent AI Space Mission</p>
            </div>
            
            {/* Controls */}
            <div className="flex justify-center items-center gap-4 mb-4">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`group relative overflow-hidden px-6 py-3 rounded-lg font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                  isPlaying 
                    ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white border border-red-400' 
                    : 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white border border-green-400'
                }`}
                disabled={loading || (gameData && gameData.game_over)}
              >
                <div className="flex items-center gap-2">
                  {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                  {isPlaying ? '⏸️ PAUSE MISSION' : '▶️ START MISSION'}
                </div>
                <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity"></div>
              </button>
              
              <button
                onClick={resetSimulation}
                className="group relative overflow-hidden px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold text-sm rounded-lg transition-all transform hover:scale-105 shadow-lg border border-blue-400"
                disabled={loading}
              >
                <div className="flex items-center gap-2">
                  <RotateCcw size={16} />
                  🔄 RESET SHIP
                </div>
                <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity"></div>
              </button>
            </div>
            
            {/* Mission Status */}
            <div className="text-center mb-3">
              <div className="inline-block bg-gray-800 border border-cyan-400 rounded-lg px-4 py-2">
                <div className="text-lg font-bold text-cyan-300 mb-1">
                  🌌 MISSION STATUS 🌌
                </div>
                <div className="text-sm text-white">
                  <span className="text-cyan-400 font-bold">Step:</span> {currentStep}/30 | 
                  <span className="text-purple-400 font-bold ml-2">Phase:</span> {phase === 'simulation' ? '🚀 Simulation' : '🚨 Emergency Meeting'}
                </div>
                {gameData && (
                  <div className="mt-2 p-2 bg-blue-900 rounded-lg border border-blue-500">
                    <p className="text-xs text-cyan-200 font-medium">{gameData.message}</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-4 lg:grid-cols-3 gap-4 flex-1 min-h-0">
            {/* Space Ship Map - Hidden during emergency meeting */}
            {phase === 'simulation' && (
            <div className="xl:col-span-3 lg:col-span-2 min-h-0">
              <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-xl p-3 relative border-2 border-cyan-500 shadow-2xl overflow-hidden h-full">
                <div className="flex items-center justify-center mb-2">
                  <h3 className="text-lg font-bold text-cyan-300 tracking-wide">🛸 THE SKELD 🛸</h3>
                </div>
              
              {/* Space corridors between rooms */}
              <svg className="absolute top-0 left-0 w-full h-full pointer-events-none" style={{zIndex: 1}}>
                {/* Cafeteria to Hallway */}
                <line x1="240" y1="145" x2="280" y2="220" stroke="url(#corridor-gradient)" strokeWidth="10" opacity="0.8" />
                {/* Hallway to Electrical */}
                <line x1="380" y1="220" x2="380" y2="145" stroke="url(#corridor-gradient)" strokeWidth="10" opacity="0.8" />
                {/* Hallway to Navigation */}
                <line x1="280" y1="250" x2="220" y2="280" stroke="url(#corridor-gradient)" strokeWidth="10" opacity="0.8" />
                
                {/* Gradient definition for corridors */}
                <defs>
                  <linearGradient id="corridor-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style={{stopColor: '#06b6d4', stopOpacity: 0.6}} />
                    <stop offset="50%" style={{stopColor: '#8b5cf6', stopOpacity: 0.8}} />
                    <stop offset="100%" style={{stopColor: '#06b6d4', stopOpacity: 0.6}} />
                  </linearGradient>
                </defs>
                
                {/* Junction points with glow effect */}
                <circle cx="280" cy="220" r="6" fill="#06b6d4" opacity="0.8">
                  <animate attributeName="r" values="4;8;4" dur="2s" repeatCount="indefinite"/>
                </circle>
                <circle cx="380" cy="190" r="6" fill="#8b5cf6" opacity="0.8">
                  <animate attributeName="r" values="4;8;4" dur="2s" repeatCount="indefinite"/>
                </circle>
                <circle cx="250" cy="260" r="6" fill="#06b6d4" opacity="0.8">
                  <animate attributeName="r" values="4;8;4" dur="2s" repeatCount="indefinite"/>
                </circle>
              </svg>

              {/* Space Ship Rooms */}
              {Object.entries(roomPositions).map(([roomName, pos]) => {
                const roomEmojis = {
                  'Cafeteria': '🍽️',
                  'Electrical': '⚡',
                  'Navigation': '🧭',
                  'Hallway': '🚪'
                };
                
                return (
                  <div
                    key={roomName}
                    className="absolute rounded-3xl flex flex-col items-center justify-center text-white font-black text-lg border-4 shadow-2xl transition-all hover:scale-105"
                    style={{
                      left: pos.x,
                      top: pos.y,
                      width: pos.width,
                      height: pos.height,
                      background: `linear-gradient(135deg, ${pos.color}, ${pos.color}dd)`,
                      borderColor: roomName === 'Electrical' ? '#ef4444' : '#06b6d4',
                      boxShadow: `0 0 20px ${roomName === 'Electrical' ? '#ef444433' : '#06b6d433'}`,
                      zIndex: 2
                    }}
                  >
                    <div className="text-3xl mb-1">{roomEmojis[roomName] || '🏠'}</div>
                    <div className="text-sm text-center px-2 text-shadow">{roomName}</div>
                  </div>
                );
              })}
              
              {/* Crewmates */}
              {Object.entries(currentStepData.agents).map(([agentId, agentData]) => {
                if (agentData.status === 'dead') {
                  const pos = roomPositions[agentData.location];
                  return (
                    <div
                      key={agentId}
                      className="absolute flex items-center justify-center transition-all duration-1000"
                      style={{
                        left: pos.x + pos.width/2,
                        top: pos.y + pos.height/2,
                        width: 40,
                        height: 40,
                        transform: 'translate(-50%, -50%)',
                        zIndex: 4
                      }}
                    >
                      {/* Ghost effect */}
                      <div className="relative">
                        <div className="absolute inset-0 bg-gray-400 rounded-full opacity-50 animate-pulse"></div>
                        <div className="relative w-10 h-10 bg-gray-600 rounded-full border-3 border-red-500 flex items-center justify-center">
                          <span className="text-xl animate-bounce">👻</span>
                        </div>
                      </div>
                    </div>
                  );
                }
                
                const pos = roomPositions[agentData.location];
                const agentsInRoom = Object.entries(currentStepData.agents).filter(([_, data]) => 
                  data.location === agentData.location && data.status !== 'dead'
                );
                const agentIndex = agentsInRoom.findIndex(([id, _]) => id === agentId);
                const totalInRoom = agentsInRoom.length;
                
                // Calculate position within room to spread agents evenly
                const roomCenterX = pos.x + pos.width/2;
                const roomCenterY = pos.y + pos.height/2;
                
                let offsetX = 0;
                let offsetY = 0;
                
                if (totalInRoom > 1) {
                  const spacing = 25;
                  const startOffset = -(totalInRoom - 1) * spacing / 2;
                  offsetX = startOffset + agentIndex * spacing;
                  
                  // If more than 3 agents, stack them in rows
                  if (totalInRoom > 3) {
                    const row = Math.floor(agentIndex / 3);
                    const col = agentIndex % 3;
                    offsetX = -(2 * spacing / 2) + col * spacing;
                    offsetY = -spacing/2 + row * spacing;
                  }
                }
                
                return (
                  <div
                    key={agentId}
                    className="absolute flex items-center justify-center transition-all duration-1000 hover:scale-110"
                    style={{
                      left: roomCenterX + offsetX,
                      top: roomCenterY + offsetY,
                      width: 40,
                      height: 40,
                      transform: 'translate(-50%, -50%)',
                      zIndex: 3
                    }}
                  >
                    {/* Among Us style crewmate */}
                    <div 
                      className="relative w-10 h-10 rounded-full border-3 border-white shadow-lg flex items-center justify-center font-black text-white text-sm transition-all"
                      style={{
                        backgroundColor: agentColors[agentId],
                        boxShadow: `0 0 12px ${agentColors[agentId]}66`
                      }}
                    >
                      {/* Visor effect */}
                      <div className="absolute top-1 left-1 w-2 h-1.5 bg-white opacity-80 rounded-full"></div>
                      <span className="text-shadow">{agentId.charAt(0).toUpperCase()}</span>
                      
                      {/* Impostor indicator */}
                      {agentId === 'yellow' && (
                        <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-600 rounded-full border-2 border-white flex items-center justify-center">
                          <span className="text-xs">👹</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

            </div>
          </div>
          )}

          {/* Mission Control Panel - Show current step info during simulation */}
          {phase === 'simulation' && (
          <div className="h-full flex flex-col min-h-0">
            {/* Crew Activity Monitor */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-3 border-2 border-purple-500 shadow-2xl flex-1 flex flex-col min-h-0">
              <div className="flex items-center justify-center mb-2 flex-shrink-0">
                <h3 className="text-lg font-bold text-purple-300">👥 CREW MONITOR 👥</h3>
              </div>
              <div className="space-y-2 flex-1 overflow-y-auto min-h-0">
                {Object.entries(currentStepData.agents).map(([agentId, agentData]) => (
                  <div key={agentId} className="bg-gray-700 rounded-lg p-2 border border-cyan-400">
                    <div className="flex items-center gap-2 mb-1">
                      <div 
                        className="w-6 h-6 rounded-full border border-white flex items-center justify-center font-bold text-white text-xs"
                        style={{backgroundColor: agentColors[agentId]}}
                      >
                        {agentId.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-bold text-cyan-300 text-sm capitalize">{agentId}</span>
                      {agentId === 'yellow' && (
                        <span className="bg-red-600 text-white px-1 py-0.5 rounded-full text-xs font-bold">👹 SUS</span>
                      )}
                    </div>
                    <div className="text-xs text-white bg-gray-800 rounded-lg p-1.5 mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className="text-yellow-400">📍</span>
                        <span className="text-purple-300 font-medium">{agentData.location}</span>
                      </div>
                      <div className="flex items-start gap-1.5 mt-0.5">
                        <span className="text-green-400">⚡</span>
                        <span className="text-gray-300">{agentData.action}</span>
                      </div>
                    </div>
                    {agentData.met && agentData.met.length > 0 && (
                      <div className="text-xs text-cyan-200 bg-blue-900 rounded-lg p-1.5">
                        <span className="text-cyan-400 font-medium">👀 Witnessed:</span> {agentData.met.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

          </div>
          )}

        </div>

        {/* Emergency Meeting Panel - Full Height */}
        {phase === 'emergency_meeting' && gameData && (
          <div className="mt-4 bg-gradient-to-br from-red-900 via-red-800 to-red-900 border-2 border-red-400 rounded-xl p-4 shadow-2xl h-[calc(100vh-10rem)]">
            <div className="text-center mb-3">
              <h2 className="text-2xl font-black text-red-300 mb-1 animate-pulse tracking-wide">
                🚨 EMERGENCY MEETING 🚨
              </h2>
              <div className="bg-gray-800 rounded-lg p-1.5 border border-yellow-400 inline-block">
                <p className="text-xs text-yellow-300 font-bold">{gameData.message}</p>
                <div className="text-xs text-cyan-300 mt-0.5 flex items-center justify-center gap-2">
                  <span>🔢 Step {gameData.step_number} / {gameData.max_steps}</span>
                  <span>💚 Alive: {gameData.agents.filter(a => a.is_alive).length} agents</span>
                </div>
                {gameData.winner && (
                  <div className="mt-1 p-1 bg-green-800 rounded-lg border border-green-400">
                    <p className="text-xs font-bold text-green-300">🏆 Winner: {gameData.winner} 🏆</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Layout: Emergency Status + Chat Side by Side */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-3 h-[calc(100%-6rem)]">
              
              {/* Emergency Status Panel */}
              <div className="lg:col-span-1">
                <div className="bg-gradient-to-br from-red-800 to-red-900 rounded-2xl p-2 border-2 border-red-400 shadow-xl h-full flex flex-col">
                  <div className="text-center mb-1">
                    <h3 className="text-xs font-bold text-red-300">🚨 CREW STATUS</h3>
                  </div>
                  <div className="space-y-0.5 flex-1 overflow-y-auto">
                    {gameData.agents.map((agent) => (
                      <div key={agent.id} className="bg-gray-800 rounded-lg p-1 border border-yellow-400">
                        <div className="flex items-center gap-1">
                          <div
                            className="w-6 h-6 rounded-full border border-white flex items-center justify-center font-bold text-white text-xs shadow-md flex-shrink-0"
                            style={{
                              backgroundColor: getAgentColor(agent.color),
                              boxShadow: `0 0 6px ${getAgentColor(agent.color)}66`
                            }}
                          >
                            {agent.name.charAt(0).toUpperCase()}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-bold text-cyan-300 text-xs truncate">{agent.name}</div>
                            <div className="flex gap-0.5 mt-0.5">
                              {agent.is_impostor && (
                                <span className="bg-red-600 text-white px-1 py-0.5 rounded text-xs font-bold leading-none">
                                  👹
                                </span>
                              )}
                              <span className={`px-1 py-0.5 rounded text-xs font-bold leading-none ${
                                agent.is_alive 
                                  ? 'bg-green-600 text-white' 
                                  : 'bg-gray-600 text-white'
                              }`}>
                                {agent.is_alive ? '💚' : '👻'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Chat Panel */}
              <div className="lg:col-span-3">
                <div className="bg-gray-900 rounded-xl border-2 border-cyan-400 shadow-2xl overflow-hidden h-full flex flex-col">
                  <div className="p-2 border-b-2 border-cyan-400 bg-gradient-to-r from-gray-800 to-gray-700 flex-shrink-0">
                    <div className="text-center">
                      <h3 className="text-lg font-bold text-cyan-300 mb-0.5">💬 CREW DISCUSSION 💬</h3>
                      <p className="text-xs text-cyan-200">AI Agents are sharing their observations and suspicions</p>
                    </div>
                  </div>
                  <div className="p-2 space-y-2 flex-1 overflow-y-auto bg-gradient-to-b from-gray-800 to-gray-900" style={{scrollbarWidth: 'thin', scrollbarColor: '#06b6d4 #374151'}}>
                {gameData.conversation_history
                  .filter(action => action.action_type === 'speak')
                  .map((action, index) => {
                    const agent = getAgentById(action.agent_id);
                    if (!agent) return null;
                    
                    return (
                      <div key={index} className="flex items-start gap-2 p-2 bg-gradient-to-r from-gray-700 to-gray-600 rounded-lg border border-cyan-400 shadow-lg">
                        {/* Agent Avatar */}
                        <div
                          className="w-8 h-8 rounded-full border border-white shadow-xl flex items-center justify-center text-white font-black text-xs flex-shrink-0 relative"
                          style={{
                            backgroundColor: getAgentColor(agent.color),
                            boxShadow: `0 0 8px ${getAgentColor(agent.color)}66`
                          }}
                        >
                          {/* Visor effect */}
                          <div className="absolute top-0.5 left-0.5 w-1.5 h-1 bg-white opacity-80 rounded-full"></div>
                          {agent.name.charAt(0).toUpperCase()}
                          
                          {/* Impostor indicator */}
                          {agent.is_impostor && (
                            <div className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-600 rounded-full border border-white flex items-center justify-center animate-pulse">
                              <span className="text-xs">👹</span>
                            </div>
                          )}
                        </div>
                        
                        {/* Chat Message */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 mb-1">
                            <span className="font-black text-sm text-cyan-300">
                              {agent.name}
                            </span>
                            {agent.is_impostor && (
                              <span className="bg-red-600 text-white px-1 py-0.5 rounded-full text-xs font-bold border border-red-400 animate-pulse">
                                👹
                              </span>
                            )}
                            <span className="text-xs text-yellow-400 bg-gray-800 px-1 py-0.5 rounded-full">
                              Step {gameData.step_number}
                            </span>
                          </div>
                          <div className="bg-gray-800 rounded-lg p-2 border border-purple-400 shadow-inner">
                            <div className="text-xs text-white leading-relaxed font-medium">
                              {action.content}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                
                {/* Show votes */}
                {gameData.conversation_history
                  .filter(action => action.action_type === 'vote')
                  .map((action, index) => {
                    const voter = getAgentById(action.agent_id);
                    const target = action.target_agent_id ? getAgentById(action.target_agent_id) : null;
                    if (!voter) return null;
                    
                    return (
                      <div key={`vote-${index}`} className="p-2 bg-gradient-to-r from-yellow-800 to-orange-800 rounded-lg border border-yellow-400 shadow-lg">
                        <div className="flex items-center gap-1.5 text-xs">
                          <div
                            className="w-5 h-5 rounded-full border border-white flex items-center justify-center font-bold text-white text-xs"
                            style={{backgroundColor: getAgentColor(voter.color)}}
                          >
                            {voter.name.charAt(0).toUpperCase()}
                          </div>
                          <span className="font-bold text-yellow-300">
                            {voter.name}
                          </span>
                          <span className="text-yellow-200 font-medium">voted to eliminate</span>
                          {target && (
                            <>
                              <div
                                className="w-5 h-5 rounded-full border border-white flex items-center justify-center font-bold text-white text-xs"
                                style={{backgroundColor: getAgentColor(target.color)}}
                              >
                                {target.name.charAt(0).toUpperCase()}
                              </div>
                              <span className="font-bold text-red-300">
                                {target.name}
                              </span>
                            </>
                          )}
                          <span className="text-sm">🗳️</span>
                        </div>
                      </div>
                    );
                  })}
                  
                  {/* Subtle loading indicator when API is processing */}
                  {loading && phase === 'emergency_meeting' && (
                    <div className="flex items-center gap-1 p-2 bg-gray-700 rounded-lg border border-cyan-400 ml-auto max-w-fit">
                      <div className="text-xs text-cyan-300">AI thinking</div>
                      <div className="flex gap-0.5">
                        <div className="w-1 h-1 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                        <div className="w-1 h-1 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                        <div className="w-1 h-1 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                      </div>
                    </div>
                  )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
};

export default AmongUsSimulation;
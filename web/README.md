# Among Us Multi-Agent AI Simulation

A real-time 2D Among Us simulation interface demonstrating how shared memory access enables better AI collaboration. This application shows 4 colored agents (red, blue, green, yellow) moving through a simplified map following a predefined 30-step timeline based on the scenario.md file.

## Features

- **Real-time simulation** with 4 agents moving through rooms (Cafeteria, Electrical, Navigation, Hallway)
- **Memory access toggle** for each agent to demonstrate collaborative AI reasoning
- **Visual memory connections** showing green dotted lines between agents with shared memory access
- **Agent memory panel** displaying what each agent observed during encounters
- **Emergency meeting interface** triggered when the body is discovered
- **Dramatically different reasoning** based on memory sharing configuration
- **Smooth animations** with 2-second intervals between steps
- **Timeline progress indicator** and reset functionality

## How It Works

1. **Start the simulation** - Click Play to watch agents move through the map
2. **Toggle memory access** - Check/uncheck boxes to enable shared memory for different agents
3. **Watch the emergency meeting** - When the body is discovered (step 30), agents will provide reasoning based on their memory access
4. **Compare reasoning quality** - Notice how shared memory enables better cross-referencing and collaboration

## Installation & Setup

```bash
# Navigate to the web directory
cd web

# Install dependencies
npm install

# Start the development server
npm run dev
```

The application will open in your browser at `http://localhost:3000`.

## Key Demonstration

The simulation clearly shows how AI agents with shared memory access can:
- Cross-reference observations from multiple agents
- Provide more sophisticated reasoning during the emergency meeting
- Identify suspicious behavior patterns through collaborative analysis
- Make better informed decisions compared to agents working with isolated memories

Try running the simulation with different memory sharing configurations to see the dramatic difference in agent reasoning quality! 
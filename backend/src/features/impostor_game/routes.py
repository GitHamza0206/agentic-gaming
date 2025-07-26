from fastapi import APIRouter, HTTPException
from .service import ImpostorGameService
from .schema import InitGameResponse, StepResponse, GameStateResponse

router = APIRouter(prefix="/impostor-game", tags=["Impostor Game"])

game_service = ImpostorGameService()

@router.post("/init", response_model=InitGameResponse)
async def init_game(num_players: int = 4, max_steps: int = 30):
    """
    Initialise un nouveau jeu de l'imposteur avec le nombre spécifié d'agents IA.
    """
    if num_players < 3 or num_players > 8:
        raise HTTPException(status_code=400, detail="Le nombre de joueurs doit être entre 3 et 8")
    
    if max_steps < 5 or max_steps > 100:
        raise HTTPException(status_code=400, detail="Le nombre maximum d'étapes doit être entre 5 et 100")
    
    return game_service.create_game(num_players, max_steps)

@router.post("/step/{game_id}", response_model=StepResponse)
async def game_step(game_id: str):
    """
    Fait progresser le jeu d'une étape.
    Alterne entre phases de discussion et de vote.
    """
    try:
        result = await game_service.step_game(game_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Jeu non trouvé")
        
        return result
    except Exception as e:
        print(f"Error in game_step: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement de l'étape: {str(e)}")

@router.get("/game/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """
    Récupère l'état actuel d'un jeu.
    """
    result = game_service.get_game_state_response(game_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    
    return result

@router.get("/debug/{game_id}")
async def debug_game(game_id: str):
    """
    Debug endpoint to check game state
    """
    game = game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    alive_agents = [a for a in game.agents if a.is_alive]
    
    return {
        "game_id": game_id,
        "step_number": game.step_number,
        "max_steps": game.max_steps,
        "status": game.status,
        "phase": game.phase,
        "alive_agents": len(alive_agents),
        "total_agents": len(game.agents),
        "votes": game.current_votes,
        "winner": game.winner,
        "can_continue": game.status == "active" and game.step_number < game.max_steps
    }

@router.get("/health")
async def health_check():
    """
    Vérifie que le service fonctionne correctement.
    """
    return {"status": "healthy", "service": "impostor-game"}
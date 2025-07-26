from fastapi import APIRouter, HTTPException
from .service import ImpostorGameService
from .schema import InitGameResponse, StepResponse, GameStateResponse

router = APIRouter(prefix="/impostor-game", tags=["Impostor Game"])

game_service = ImpostorGameService()

@router.post("/init", response_model=InitGameResponse)
async def init_game():
    """
    Initialise un nouveau jeu de l'imposteur avec 8 agents IA.
    """
    return game_service.create_game()

@router.post("/step/{game_id}", response_model=StepResponse)
async def game_step(game_id: str):
    """
    Fait progresser le jeu d'une étape.
    Alterne entre phases de discussion et de vote.
    """
    result = game_service.step_game(game_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    
    return result

@router.get("/game/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """
    Récupère l'état actuel d'un jeu.
    """
    result = game_service.get_game_state_response(game_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    
    return result

@router.get("/health")
async def health_check():
    """
    Vérifie que le service fonctionne correctement.
    """
    return {"status": "healthy", "service": "impostor-game"}
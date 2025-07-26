import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.features.impostor_game.routes import router as impostor_router

load_dotenv("../.env")  # backend/.env

app = FastAPI(
    title="Agentic Gaming API",
    description="API pour des jeux d'agents IA - Incluant le jeu de l'imposteur",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(impostor_router)

@app.get("/")
async def root():
    return {
        "message": "Bienvenue dans l'API Agentic Gaming",
        "available_endpoints": {
            "impostor_game": "/impostor-game/",
            "health": "/impostor-game/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "api": "agentic-gaming"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
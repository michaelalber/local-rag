"""Model management routes."""

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings

router = APIRouter(prefix="/models", tags=["models"])

# Model descriptions to help users choose
MODEL_DESCRIPTIONS = {
    "mistral": {
        "name": "Mistral 7B",
        "description": "General-purpose, balanced model. Great for most books and documents.",
        "best_for": ["General texts", "Business", "History", "Literature"],
        "size": "4.1GB (q4_K_M)",
    },
    "codellama": {
        "name": "Code Llama",
        "description": "Specialized for code and programming. Best for technical books.",
        "best_for": ["Programming", "Code examples", "Technical docs", "APIs"],
        "size": "3.8GB (7b)",
    },
    "llama2": {
        "name": "Llama 2",
        "description": "Versatile conversational model. Good for dialogue and explanations.",
        "best_for": ["Tutorials", "How-to guides", "Conversational content"],
        "size": "3.8GB (7b)",
    },
    "phi": {
        "name": "Phi-2",
        "description": "Small, fast model. Quick responses, lower quality than larger models.",
        "best_for": ["Quick lookups", "Simple questions", "Fast iteration"],
        "size": "1.7GB (2.7b)",
    },
    "neural-chat": {
        "name": "Neural Chat",
        "description": "Optimized for chat and instruction following.",
        "best_for": ["Q&A", "Instructions", "Step-by-step guides"],
        "size": "4.1GB (7b)",
    },
}


@router.get("")
async def list_models(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
    """
    List available Ollama models with descriptions.

    Returns models installed on the local Ollama instance with helpful
    metadata to guide model selection.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

        # Extract model names and enrich with descriptions
        models = []
        for model_info in data.get("models", []):
            model_name = model_info.get("name", "").split(":")[0]  # Remove tag (e.g., :latest)

            # Get description if available
            description_info = MODEL_DESCRIPTIONS.get(
                model_name,
                {
                    "name": model_name.title(),
                    "description": "Custom or specialized model",
                    "best_for": ["Custom use cases"],
                    "size": model_info.get("size", "Unknown"),
                },
            )

            models.append(
                {
                    "id": model_info.get("name"),  # Full name with tag
                    "name": description_info["name"],
                    "description": description_info["description"],
                    "best_for": description_info["best_for"],
                    "size": description_info.get("size", "Unknown"),
                    "modified_at": model_info.get("modified_at"),
                }
            )

        return {
            "models": models,
            "default": settings.llm_model,
        }

    except httpx.HTTPError:
        # Log full error details internally but return generic message
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Is Ollama running?",
        ) from None
    except Exception:
        # Log full error details internally but return generic message
        raise HTTPException(
            status_code=500,
            detail="An error occurred while listing models.",
        ) from None

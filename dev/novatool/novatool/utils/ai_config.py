from enum import Enum
import os
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

class AIService(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"

class AIConfig:
    MODELS = {
        AIService.OPENAI: {
            'primary': 'gpt-4o-mini',
            'fallback': 'gpt-3.5-turbo'
        },
        AIService.OLLAMA: {
            'primary': 'nemotron-mini',
            'fallback': 'llama3.2'
        }
    }

    @staticmethod
    def get_model(service: AIService) -> str:
        """Get primary model for service"""
        return AIConfig.MODELS[service]['primary']

    @staticmethod
    def get_fallback_model(service: AIService) -> str:
        """Get fallback model for service"""
        return AIConfig.MODELS[service]['fallback']

    @staticmethod
    def get_available_models(service: AIService) -> list:
        """Get list of available models for the service"""
        try:
            if service == AIService.OLLAMA:
                import ollama
                models = ollama.list()
                return [model['name'].split(':')[0] for model in models.get('models', [])]
            elif service == AIService.OPENAI:
                return [AIConfig.MODELS[service]['primary']]
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get available models: {str(e)}[/]")
            return []

    @staticmethod
    def validate_api_keys() -> dict:
        """Validate required API keys are present"""
        keys = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
        }

        missing = [k for k, v in keys.items() if not v]
        if missing:
            raise ValueError(f"Missing required API keys: {', '.join(missing)}")

        return keys
from google import genai
from google.genai import types
import time
from core.config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL, TEMPERATURE

class BaseAgent:
    def __init__(self, name: str, role: str, system_instruction: str, model_name: str = DEFAULT_GEMINI_MODEL):
        """Initializes the base agent with a name, role, system instructions, and target Gemini model."""
        self.name = name
        self.role = role
        self.system_instruction = system_instruction
        self.model_name = model_name
        
        # Configure Gemini Client using the new unified google-genai SDK
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the environment or .env file!")
            
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Setup modern GenerateContentConfig including system_instruction
        self.config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=TEMPERATURE,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192
        )

    def run(self, prompt: str, retries: int = 5, delay: int = 15) -> str:
        """Sends a prompt to the Gemini model and returns the response, with rate-limit retry logic."""
        for attempt in range(retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self.config
                )
                if response and response.text:
                    return response.text
                return "Agent failed to generate response."
            except Exception as e:
                print(f"[{self.name}] Error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                else:
                    raise e

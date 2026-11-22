import os
from typing import TypeVar

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

DEFAULT_MODEL = "gemini-3.1-flash-lite"
SchemaT = TypeVar("SchemaT", bound=BaseModel)


def get_client() -> genai.Client:
    """Create a Gemini API client using GEMINI_API_KEY from the environment"""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Add it to your .env file before running research."
        )
    return genai.Client(api_key=api_key)


def generate_structured(
        prompt: str,
        response_schema: type[SchemaT],
        system_instruction: str | None = None,
        model: str = DEFAULT_MODEL,
) -> SchemaT:
    """Call Gemini and parse the response directly into a Pydantic model."""
    client = get_client()
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        system_instruction=system_instruction,
        temperature=0.2,
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    if response.parsed is None:
        raise RuntimeError("Model did not return a structured response matching the schema.")
    return response.parsed
"""Small provider adapter. All credentials stay in the FastAPI process."""
import base64
import json
import os
import re

from fastapi import HTTPException


def provider_failure(provider: str, action: str, exc: Exception) -> HTTPException:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 429:
        return HTTPException(429, f"Batas atau kuota {provider} tercapai. Coba lagi nanti.")
    return HTTPException(502, f"{action} {provider} gagal: {type(exc).__name__}")


def model_for(provider: str) -> str:
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    raise HTTPException(400, "Provider tidak dikenal")


def generate(provider: str, model: str, instructions: str, prompt: str, image: tuple[bytes, str] | None = None) -> str:
    try:
        if provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise HTTPException(503, "OPENAI_API_KEY belum diatur pada backend")
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=45)
            if image:
                data, mime = image
                content = [{"type": "input_text", "text": prompt}, {"type": "input_image", "image_url": f"data:{mime};base64,{base64.b64encode(data).decode()}"}]
                response = client.responses.create(model=model, instructions=instructions, input=[{"role": "user", "content": content}])
            else:
                response = client.responses.create(model=model, instructions=instructions, input=prompt)
            return response.output_text
        if provider == "gemini":
            if not os.getenv("GEMINI_API_KEY"):
                raise HTTPException(503, "GEMINI_API_KEY belum diatur pada backend")
            from google import genai
            from google.genai import types
            with genai.Client(
                api_key=os.environ["GEMINI_API_KEY"],
                http_options=types.HttpOptions(
                    timeout=30000,
                    retry_options=types.HttpRetryOptions(attempts=2, initial_delay=1, max_delay=2),
                ),
            ) as client:
                contents = [f"{instructions}\n\n{prompt}"]
                if image:
                    contents.append(types.Part.from_bytes(data=image[0], mime_type=image[1]))
                response = client.models.generate_content(model=model, contents=contents)
                return response.text or ""
        raise HTTPException(400, "Provider tidak dikenal")
    except HTTPException:
        raise
    except Exception as exc:
        raise provider_failure(provider, "Permintaan ke", exc) from exc


def embed(texts: list[str], *, query: bool = False) -> list[list[float]]:
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(503, "GEMINI_API_KEY dibutuhkan untuk embedding PDF")
    try:
        from google import genai
        from google.genai import types

        model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
        dimension = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
        prepared = [
            f"task: question answering | query: {text}" if query else f"title: none | text: {text}"
            for text in texts
        ]
        contents = [types.Content(parts=[types.Part.from_text(text=text)]) for text in prepared]
        with genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=30000)) as client:
            response = client.models.embed_content(
                model=model,
                contents=contents,
                config=types.EmbedContentConfig(output_dimensionality=dimension),
            )
        vectors = [item.values for item in response.embeddings or []]
        if len(vectors) != len(texts) or any(vector is None or len(vector) != dimension for vector in vectors):
            raise HTTPException(502, "Jumlah atau dimensi embedding Gemini tidak sesuai")
        return vectors
    except HTTPException:
        raise
    except Exception as exc:
        raise provider_failure("Gemini", "Embedding", exc) from exc


def json_result(raw: str) -> dict:
    try:
        stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except (ValueError, TypeError):
        pass
    raise HTTPException(502, "Provider mengembalikan format jawaban yang tidak dapat dibaca")

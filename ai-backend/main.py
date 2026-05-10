from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from core.config import settings

import uvicorn

app = FastAPI(title="AI Backend")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=getattr(settings, "host", "127.0.0.1"),
        port=getattr(settings, "port", 8001),
        reload=True,
    )


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    label: str
    score: float


async def call_ollama(text: str) -> dict:
    prompt = f"""Analyze the sentiment of the following text. Respond with ONLY valid JSON, no other text:
{{"label": "positive" or "negative" or "neutral", "score": 0.0 to 1.0}}

Text: {text}

Respond with JSON only:"""

    async with httpx.AsyncClient() as client:
        print(f"[ai-backend] Calling Ollama with text: {text[:100]}")
        response = await client.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=30.0,
        )
        print(f"[ai-backend] Ollama raw response: {response.status_code} - {response.text[:500]}")
        response.raise_for_status()
        data = response.json()

    import json
    result = json.loads(data.get("response", "{}"))
    print(f"[ai-backend] Parsed result: {result}")
    return {
        "label": result.get("label", "neutral"),
        "score": float(result.get("score", 0.5)),
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_sentiment(request: AnalyzeRequest):
    try:
        result = await call_ollama(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}

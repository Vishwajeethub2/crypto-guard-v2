from fastapi import FastAPI

app = FastAPI(title="Crypto Guard V2 API")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "crypto-guard-api"
    }
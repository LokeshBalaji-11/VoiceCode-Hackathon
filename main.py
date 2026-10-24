app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "demo-fastapi-api"}


@app.get("/health")
async def health_check():
    """Returns service health status for FastAPI."""
    return {"status": "ok", "service": "demo-checkout-api"}

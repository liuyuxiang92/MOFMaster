"""FastAPI + LangServe entry point."""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from langserve import add_routes
from app.graph import create_graph
from app.schema import InvokeRequest, InvokeResponse

# Load environment variables
load_dotenv()

app = FastAPI(
    title="MOF-Scientist Backend",
    description="A scientific workflow agent for Metal-Organic Frameworks",
    version="0.1.0",
)

# Create and compile the graph
graph = create_graph()

# Add LangServe routes
add_routes(
    app,
    graph,
    path="/mof-scientist",
    playground_type="default",
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MOF-Scientist Backend API",
        "version": "0.1.0",
        "docs": "/docs",
        "playground": "/mof-scientist/playground",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(app, host=host, port=port)


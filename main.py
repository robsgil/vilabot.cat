"""
Vilabot.cat - Hyperlocal Events Discovery for Catalonia
FastAPI Backend serving API and static frontend
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from llm import extract_query_intent, generate_response
from scraper import scrape_all_sources

load_dotenv()

app = FastAPI(
    title="Vilabot.cat API",
    description="Hyperlocal events discovery for Catalonia",
    version="0.1.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    success: bool
    query: str
    extracted_intent: dict
    response: str
    sources_scraped: int
    events_found: int


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query about events in Catalonia.
    
    Flow:
    1. Extract keywords, date range, location from query using LLM
    2. Scrape configured websites for matching content
    3. Pass scraped content to LLM for response synthesis
    4. Return formatted response
    """
    try:
        # Step 1: Extract intent from query
        intent = await extract_query_intent(request.query)
        
        # Step 2: Scrape sources for matching content
        scraped_results = await scrape_all_sources(intent)
        
        # Step 3: Generate response from scraped content
        response_text = await generate_response(
            original_query=request.query,
            intent=intent,
            scraped_content=scraped_results["content"]
        )
        
        return QueryResponse(
            success=True,
            query=request.query,
            extracted_intent=intent,
            response=response_text,
            sources_scraped=scraped_results["sources_scraped"],
            events_found=scraped_results["events_found"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "service": "vilabot.cat",
        "version": "0.1.0"
    }


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend"""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Optional, List
from backend.utils.logger import get_logger
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
import tempfile
import uuid
import json

import json
import re
import asyncio

logger = get_logger(__name__)
import logging
logging.getLogger("backend").setLevel(logging.DEBUG)

def _load_reports() -> dict:
    if _REPORTS_FILE.exists():
        try:
            with open(_REPORTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load reports file: {e}")
    return {}

def _save_reports(reports: dict):
    try:
        from backend.agents.base_agent import safe_json_dumps
        with open(_REPORTS_FILE, "w", encoding="utf-8") as f:
            f.write(safe_json_dumps(reports))
    except Exception as e:
        logger.warning(f"Could not save reports file: {e}")

app = FastAPI(
    title="AI Research Assistant + BI Platform",
    description="Multi-agent research & business intelligence system powered by Groq & AutoGen",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    query: str
    workflow: Optional[str] = "group_chat"
    max_iterations: Optional[int] = 3

class ResearchResponse(BaseModel):
    status: str
    report: str
    workflow: str

class BIAnalyzeRequest(BaseModel):
    query: str
    industry: str
    region: str
    competitors: Optional[str] = None
    workflow: Optional[str] = "sequential"

class BIAnalyzeResponse(BaseModel):
    status: str
    report_id: str
    executive_summary: str
    metadata: dict

team_cache = {}

# ---------------------------------------------------------------------------
# Persistent report store
# Reports are saved to a JSON file next to main.py so they survive reloads
# and server restarts. The in-memory dict is loaded from disk on startup.
# ---------------------------------------------------------------------------
_REPORTS_FILE = Path(__file__).parent / "bi_reports.json"

bi_reports: dict = _load_reports()

def get_team(workflow: str):
    if workflow not in team_cache:
        if workflow == "sequential":
            from backend.teams import create_sequential_team
            team_cache[workflow] = create_sequential_team()
        elif workflow == "group_chat":
            from backend.teams import create_group_chat_team
            team_cache[workflow] = create_group_chat_team()
        elif workflow == "iterative":
            from backend.teams import create_iterative_team
            team_cache[workflow] = create_iterative_team()
        else:
            raise ValueError(f"Unknown workflow: {workflow}")
    return team_cache[workflow]

_bi_pipeline = None

def get_bi_pipeline():
    """Lazy-load BI pipeline — reuse the same instance across requests."""
    global _bi_pipeline
    if _bi_pipeline is None:
        from backend.config import settings
        api_config = {
            "statista_api_key": settings.STATISTA_API_KEY,
            "crunchbase_api_key": settings.CRUNCHBASE_API_KEY,
            "news_api_key": settings.NEWS_API_KEY,
            "cache_ttl": settings.BI_CACHE_TTL_HOURS * 3600
        }
        from backend.orchestration.bi_pipeline import Bipipeline
        _bi_pipeline = Bipipeline(api_config=api_config)
    return _bi_pipeline

@app.get("/")
def root():
    return {
        "message": "AI Research Assistant + Business Intelligence Platform API",
        "status": "running",
        "endpoints": {
            "research": "/research",
            "documents": "/documents/upload, /documents/query",
            "bi": "/api/bi/analyze, /api/bi/report/{id}"
        }
    }

@app.post("/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest):
    try:
        logger.info(f"Received research request: {request.query}")
        team = get_team(request.workflow)
        result = await team.run(request.query)
        return ResearchResponse(
            status=result["status"],
            report=result["report"],
            workflow=result["workflow"]
        )
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    from backend.tools.rag import process_pdf, chunk_document, generate_embeddings
    from backend.tools.rag.vector_store_tool import vector_store
    
    result = process_pdf(file, file.filename)
    if not result["success"]:
        return {"status": "error", "message": result["error"]}
    
    chunks = chunk_document(result["text"])
    embeddings = generate_embeddings([c["text"] for c in chunks])
    vector_store.add_documents(chunks, embeddings, result["metadata"])
    
    return {
        "status": "complete",
        "pages": result["metadata"]["pages"],
        "chunks": len(chunks)
    }
    
@app.post("/documents/query")
async def query_document(question: str = Form(...)):
    try:
        from backend.teams.document_team import create_document_team
        team = create_document_team()
        result = team["query_document"](question)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/bi/analyze", response_model=BIAnalyzeResponse)
async def analyze_market(
    request: BIAnalyzeRequest,
    file_paths: Optional[List[str]] = None
):
    """
    Main BI analysis endpoint
    - Analyzes market, competitors, trends
    - Accepts optional CSV/Excel uploads for internal data
    - Returns structured report with recommendations
    """
    try:
        logger.info(f"BI request: {request.industry} in {request.region}, files: {len(file_paths) if file_paths else 0}")
        
        competitor_list = None
        if request.competitors:
            competitor_list = [c.strip() for c in request.competitors.split(",")]
        
        pipeline = get_bi_pipeline()
        result = await pipeline.run(
            query=request.query,
            industry=request.industry,
            region=request.region,
            file_paths=file_paths,
            competitors=competitor_list
        )
        
        # Save report — persisted to disk so it survives reloads
        report_id = str(uuid.uuid4())
        bi_reports[report_id] = {
            "result": result,
            "created_at": result.get("metadata", {}).get("generated_at"),
            "industry": request.industry
        }
        _save_reports(bi_reports)
        
        return BIAnalyzeResponse(
            status=result.get("status", "complete"),
            report_id=report_id,
            executive_summary=result.get("executive_summary", ""),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"BI analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bi/report/{report_id}")
async def get_bi_report(report_id: str):
    """Retrieve a previously generated BI report"""
    if report_id not in bi_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    return bi_reports[report_id]["result"]

@app.post("/api/bi/analyze/upload", response_model=BIAnalyzeResponse)
async def analyze_with_upload(
    query: str = Form(...),
    industry: str = Form(...),
    region: str = Form(...),
    competitors: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None) 
):
    """
    Alternative endpoint: Form-data upload for BI analysis
    Useful for multipart/form-data requests from frontend
    """
    file_paths = []
    try:
        logger.info(f"BI upload request: {industry} in {region}, files: {len(files) if files else 0}")
        
        if files:
            for file in files:
                if not file.filename:
                    continue
                allowed_extensions = {'.csv', '.xlsx', '.xls', '.json'}
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in allowed_extensions:
                    logger.warning(f"Skipped unsupported file: {file.filename}")
                    continue
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=file_ext,
                    prefix=f"bi_upload_{uuid.uuid4().hex}_"
                ) as tmp:
                    content = await file.read()
                    tmp.write(content)
                    file_paths.append(tmp.name)
                    logger.info(f"Saved temp file: {tmp.name} ({len(content)} bytes)")
        
        result = await analyze_market(
            request=BIAnalyzeRequest(
                query=query,
                industry=industry,
                region=region,
                competitors=competitors
            ),
            file_paths=file_paths if file_paths else None
        )
        return result
        
    except Exception as e:
        logger.error(f"BI upload analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.unlink(path)
                    logger.debug(f"Cleaned up temp file: {path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {path}: {e}")

@app.get("/api/bi/industries")
async def list_industries():
    return {
        "industries": [
            "Electric Vehicles", "SaaS", "Fintech", "Healthcare AI",
            "Renewable Energy", "E-commerce", "Cybersecurity", "EdTech",
            "Food & Beverage", "Real Estate Tech"
        ]
    }

@app.get("/api/bi/regions")
async def list_regions():
    return {
        "regions": [
            "Global", "North America", "Europe", "Asia Pacific",
            "Latin America", "Middle East & Africa", "United States",
            "United Kingdom", "Germany", "China", "India"
        ]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "services": {"research": "ok", "documents": "ok", "bi": "ok"}
    }

@app.get("/api/bi/cache/stats")
async def cache_stats():
    """Debug endpoint: view persisted reports"""
    return {
        "total_reports": len(bi_reports),
        "report_ids": list(bi_reports.keys()),
        "cache_info": {
            report_id: {
                "industry": data["industry"],
                "created_at": data["created_at"]
            }
            for report_id, data in bi_reports.items()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
FastAPI Backend for QA Agent
Main application with all API endpoints
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import json

from .vector_store import VectorStore
from .ingestion import DocumentIngestion, DocumentParser
from .test_generator import TestCaseGenerator, TestCaseParser
from .script_generator import SeleniumScriptGenerator, ScriptParser

# Initialize FastAPI app
app = FastAPI(
    title="QA Agent API",
    description="Autonomous QA Agent for Test Case and Selenium Script Generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = VectorStore(persist_directory="./chroma_db")
ingestion = DocumentIngestion(vector_store)
test_generator = TestCaseGenerator(vector_store)
script_generator = SeleniumScriptGenerator(vector_store)

# Store HTML content globally for script generation
html_content_store = {"content": None, "filename": None}


# Pydantic models for request/response
class TestCaseRequest(BaseModel):
    query: str
    num_results: Optional[int] = 10


class TestCase(BaseModel):
    test_id: str
    feature: str
    test_scenario: str
    preconditions: Optional[List[str]] = []
    test_steps: Optional[List[str]] = []
    test_data: Optional[str] = ""
    expected_result: str
    test_type: str
    grounded_in: str


class ScriptRequest(BaseModel):
    test_case: dict


class StatusResponse(BaseModel):
    status: str
    message: str


class KnowledgeBaseStatus(BaseModel):
    status: str
    document_count: int
    sources: List[str]


# API Endpoints

@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint - API health check"""
    return StatusResponse(
        status="success",
        message="QA Agent API is running"
    )


@app.get("/api/status", response_model=KnowledgeBaseStatus)
async def get_status():
    """Get knowledge base status"""
    try:
        count = vector_store.get_document_count()
        sources = vector_store.get_sources()
        return KnowledgeBaseStatus(
            status="success",
            document_count=count,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a support document"""
    try:
        # Read file content
        content = await file.read()
        filename = file.filename
        
        # Ingest the document
        num_chunks = ingestion.ingest_file(
            file_content=content,
            filename=filename
        )
        
        return {
            "status": "success",
            "message": f"Document '{filename}' ingested successfully",
            "chunks_added": num_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-html")
async def upload_html(file: UploadFile = File(...)):
    """Upload and ingest the HTML file to test"""
    try:
        # Read file content
        content = await file.read()
        filename = file.filename
        
        # Store HTML content for script generation
        html_content_store["content"] = content.decode('utf-8')
        html_content_store["filename"] = filename
        
        # Set HTML content in script generator
        script_generator.set_html_content(html_content_store["content"])
        
        # Ingest the HTML
        num_chunks = ingestion.ingest_html(content, filename)
        
        return {
            "status": "success",
            "message": f"HTML '{filename}' ingested successfully",
            "chunks_added": num_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-html-text")
async def upload_html_text(html_content: str = Form(...), filename: str = Form(default="checkout.html")):
    """Upload HTML content as text"""
    try:
        # Store HTML content
        html_content_store["content"] = html_content
        html_content_store["filename"] = filename
        
        # Set HTML content in script generator
        script_generator.set_html_content(html_content)
        
        # Ingest the HTML
        num_chunks = ingestion.ingest_html(html_content, filename)
        
        return {
            "status": "success",
            "message": f"HTML content ingested successfully",
            "chunks_added": num_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/build-knowledge-base")
async def build_knowledge_base(files: List[UploadFile] = File(...)):
    """Build knowledge base from multiple files"""
    try:
        total_chunks = 0
        ingested_files = []
        
        for file in files:
            content = await file.read()
            filename = file.filename
            
            # Check if it's HTML
            if filename.lower().endswith('.html'):
                html_content_store["content"] = content.decode('utf-8')
                html_content_store["filename"] = filename
                script_generator.set_html_content(html_content_store["content"])
            
            # Ingest the file
            num_chunks = ingestion.ingest_file(
                file_content=content,
                filename=filename
            )
            total_chunks += num_chunks
            ingested_files.append(filename)
        
        return {
            "status": "success",
            "message": "Knowledge base built successfully",
            "total_chunks": total_chunks,
            "files_ingested": ingested_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-test-cases")
async def generate_test_cases(request: TestCaseRequest):
    """Generate test cases based on user query"""
    try:
        # Generate test cases
        response = test_generator.generate_test_cases(
            user_query=request.query,
            num_results=request.num_results
        )
        
        # Parse the response
        parsed = TestCaseParser.parse_json_response(response)
        
        return {
            "status": "success",
            "test_cases": parsed,
            "raw_response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/generate-all-test-cases")
async def generate_all_test_cases():
    """Generate comprehensive test cases for all features"""
    try:
        response = test_generator.generate_all_test_cases()
        parsed = TestCaseParser.parse_json_response(response)
        
        return {
            "status": "success",
            "test_cases": parsed,
            "raw_response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-feature-test-cases/{feature_name}")
async def generate_feature_test_cases(feature_name: str):
    """Generate test cases for a specific feature"""
    try:
        response = test_generator.generate_feature_test_cases(feature_name)
        parsed = TestCaseParser.parse_json_response(response)
        
        return {
            "status": "success",
            "feature": feature_name,
            "test_cases": parsed,
            "raw_response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-selenium-script")
async def generate_selenium_script(request: ScriptRequest):
    """Generate Selenium script for a test case"""
    try:
        # Ensure HTML content is set
        if not html_content_store["content"]:
            raise HTTPException(
                status_code=400,
                detail="No HTML content uploaded. Please upload HTML first."
            )
        
        # Generate script
        script = script_generator.generate_script(request.test_case)
        
        # Extract clean Python code
        clean_script = ScriptParser.extract_python_code(script)
        
        # Validate syntax
        is_valid, validation_msg = ScriptParser.validate_script(clean_script)
        
        return {
            "status": "success",
            "script": clean_script,
            "is_valid": is_valid,
            "validation_message": validation_msg,
            "raw_response": script
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-script-from-description")
async def generate_script_from_description(description: str = Form(...)):
    """Generate Selenium script from text description"""
    try:
        if not html_content_store["content"]:
            raise HTTPException(
                status_code=400,
                detail="No HTML content uploaded. Please upload HTML first."
            )
        
        script = script_generator.generate_script_from_text(description)
        clean_script = ScriptParser.extract_python_code(script)
        is_valid, validation_msg = ScriptParser.validate_script(clean_script)
        
        return {
            "status": "success",
            "script": clean_script,
            "is_valid": is_valid,
            "validation_message": validation_msg
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/clear-knowledge-base")
async def clear_knowledge_base():
    """Clear all documents from knowledge base"""
    try:
        vector_store.clear()
        html_content_store["content"] = None
        html_content_store["filename"] = None
        
        return {
            "status": "success",
            "message": "Knowledge base cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_knowledge_base(query: str, n_results: int = 5):
    """Search the knowledge base"""
    try:
        results = vector_store.search(query, n_results=n_results)
        return {
            "status": "success",
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/html-content")
async def get_html_content():
    """Get the currently stored HTML content"""
    if html_content_store["content"]:
        return {
            "status": "success",
            "filename": html_content_store["filename"],
            "content": html_content_store["content"]
        }
    else:
        return {
            "status": "error",
            "message": "No HTML content uploaded"
        }


# Run with: uvicorn backend.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
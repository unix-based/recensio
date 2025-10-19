"""
Agent Routes - Manage virtual user agents
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
import random
import uuid
from pydantic import BaseModel
from app.schemas.agent import AgentCreate, AgentResponse
from app.services.agent_service import AgentService, AIAgentService
from app.services.cache_service import CacheService
from app.services.agent_storage_service import AgentStorageService
from app.dependencies import get_agent_storage_service
from app.config import settings

router = APIRouter()

@router.get("/")
async def get_agents(task_id: str = None, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get ephemeral agents for current review session with progressive loading"""
    if task_id:
        # First check for incremental results (partial or complete)
        if task_id in incremental_results_store and incremental_results_store[task_id]:
            return incremental_results_store[task_id]
        
        # Fallback to completed results in background store
        if task_id in background_tasks_store:
            task_data = background_tasks_store[task_id]
            if task_data.get("results"):
                return task_data["results"]
    
    # If no task_id specified, return the most recent task results (including pending agents)
    if not task_id:
        for task_data in reversed(list(background_tasks_store.values())):
            if task_data.get("results"):
                return task_data["results"]
    
    # Return empty list if no active task or no results yet
    return []

# Removed persistent agent endpoints - agents are now ephemeral

# In-memory store for background tasks (in production, use Redis)
background_tasks_store = {}

# Store for incremental agent results
incremental_results_store = {}

class AILaunchRequest(BaseModel):
    website_url: str
    target_audience: Optional[Dict[str, Any]] = None

class TaskStatus(BaseModel):
    task_id: str
    status: str  # "started", "running", "completed", "failed"
    message: str
    progress: int = 0
    results: Optional[List[Dict]] = None
    error: Optional[str] = None

async def run_ai_agents_background(task_id: str, website_url: str, target_audience: Optional[Dict] = None):
    """Background task to run AI agents"""
    from app.logger import get_module_logger
    logger = get_module_logger(__name__)
    
    logger.info(f"🚀 Background AI Launch started for task {task_id}")
    
    try:
        # Update task status
        background_tasks_store[task_id]["status"] = "running"
        background_tasks_store[task_id]["message"] = "Initializing AI agent system..."
        background_tasks_store[task_id]["progress"] = 10
        
        # Check if API key is available
        if not settings.anthropic_api_key:
            logger.error("❌ ANTHROPIC_API_KEY not configured")
            background_tasks_store[task_id]["status"] = "failed"
            background_tasks_store[task_id]["error"] = "ANTHROPIC_API_KEY not configured"
            return
        
        # Get website content - normalize URL first to match verification storage
        logger.info(f"📄 Retrieving website content...")
        background_tasks_store[task_id]["message"] = "Retrieving website content..."
        background_tasks_store[task_id]["progress"] = 20
        
        # Normalize URL to match verification service
        normalized_url = website_url.strip()
        if not normalized_url.startswith(('http://', 'https://')):
            normalized_url = 'https://' + normalized_url
        
        logger.info(f"🔗 Original URL: {website_url} -> Normalized URL: {normalized_url}")
        
        cache_service = CacheService()
        site_content = cache_service.get_combined_content_for_url(normalized_url)
        
        # If not found, try with trailing slash (servers often redirect to trailing slash)
        if not site_content:
            normalized_url_with_slash = normalized_url.rstrip('/') + '/'
            logger.info(f"🔍 Trying with trailing slash: {normalized_url_with_slash}")
            site_content = cache_service.get_combined_content_for_url(normalized_url_with_slash)
            if site_content:
                normalized_url = normalized_url_with_slash
        
        # If still not found, try without trailing slash
        if not site_content:
            normalized_url_without_slash = normalized_url.rstrip('/')
            if normalized_url_without_slash != normalized_url:
                logger.info(f"🔍 Trying without trailing slash: {normalized_url_without_slash}")
                site_content = cache_service.get_combined_content_for_url(normalized_url_without_slash)
                if site_content:
                    normalized_url = normalized_url_without_slash
        
        # If still not found, try to extract content automatically
        if not site_content:
            logger.info(f"🔄 Content not found in cache, attempting to extract content for {normalized_url}")
            background_tasks_store[task_id]["message"] = "Extracting website content..."
            background_tasks_store[task_id]["progress"] = 25
            
            try:
                from app.services.link_verification_service import LinkVerificationService
                from app.services.link_verification_service import SiteSnapshot, PageContent, UsefulLink
                
                verification_service = LinkVerificationService()
                
                # Perform full site extraction
                logger.info(f"🔍 Starting comprehensive verification for {normalized_url}")
                logger.info(f"🔧 Verification service initialized: {type(verification_service).__name__}")
                result = await verification_service.comprehensive_verification(normalized_url, extract_full_site=True)
                logger.info(f"🔍 Verification completed, checking results...")
                
                if result.get("errors"):
                    logger.error(f"❌ Verification failed with errors: {result['errors']}")
                    logger.error(f"❌ Verification result keys: {list(result.keys())}")
                    background_tasks_store[task_id]["status"] = "failed"
                    background_tasks_store[task_id]["error"] = f"Verification failed: {', '.join(result['errors'])}"
                    return
                
                # Log verification results for debugging
                logger.info(f"📊 Verification results:")
                logger.info(f"   ✅ Valid: {result.get('is_valid', False)}")
                logger.info(f"   ✅ Accessible: {result.get('is_accessible', False)}")
                logger.info(f"   ✅ Suitable: {result.get('is_suitable', False)}")
                logger.info(f"   📄 Pages: {result.get('pages_extracted', 0)}")
                logger.info(f"   📊 Content length: {result.get('total_content', {}).get('combined_text_length', 0)}")
                
                # Store the extracted content
                if result.get("complete_site_content") and result.get("site_snapshot"):
                    logger.info(f"✅ Content extraction successful for {normalized_url}")
                    logger.debug(f"Result keys: {list(result.keys())}")
                    logger.debug(f"Complete site content keys: {list(result['complete_site_content'].keys())}")
                    logger.debug(f"Site snapshot keys: {list(result['site_snapshot'].keys())}")
                    
                    # Log content lengths for debugging
                    combined_text_length = len(result["complete_site_content"]["combined_text"])
                    logger.info(f"📊 Extracted content: {combined_text_length} characters")
                    logger.info(f"📊 Total pages: {result['site_snapshot']['total_pages']}")
                    logger.info(f"📊 Useful links: {len(result.get('useful_links', []))}")
                    # Create PageContent objects
                    main_page = PageContent(
                        url=result["site_snapshot"]["url"],
                        html=result["complete_site_content"]["main_page"]["html"],
                        text=result["complete_site_content"]["main_page"]["text"],
                        title=result["complete_site_content"]["main_page"]["title"],
                        meta_description=result["complete_site_content"]["main_page"]["meta_description"],
                        links=result["complete_site_content"]["main_page"]["links"]
                    )
                    
                    internal_pages = []
                    for page_data in result["complete_site_content"]["internal_pages"]:
                        page = PageContent(
                            url=page_data["url"],
                            html=page_data["html"],
                            text=page_data["text"],
                            title=page_data["title"],
                            meta_description=page_data["meta_description"],
                            links=page_data["links"]
                        )
                        internal_pages.append(page)
                    
                    useful_links = []
                    for link_data in result.get("useful_links", []):
                        link = UsefulLink(
                            url=link_data["url"],
                            title=link_data["title"],
                            reason=link_data["reason"],
                            priority=link_data["priority"]
                        )
                        useful_links.append(link)
                    
                    snapshot = SiteSnapshot(
                        url=result["site_snapshot"]["url"],
                        main_page=main_page,
                        internal_pages=internal_pages,
                        useful_links=useful_links,
                        complete_html=result["complete_site_content"]["combined_html"],
                        complete_text=result["complete_site_content"]["combined_text"],
                        total_pages=result["site_snapshot"]["total_pages"],
                        extraction_timestamp=result["site_snapshot"]["extraction_timestamp"]
                    )
                    
                    # Store in cache
                    storage_id = cache_service.store_site_snapshot(snapshot)
                    logger.info(f"✅ Content extracted and stored with ID: {storage_id}")
                    
                    # Use the extracted content directly instead of retrieving from cache
                    site_content = snapshot.complete_text
                    logger.info(f"✅ Using extracted content directly: {len(site_content)} characters")
                    
                else:
                    logger.error(f"❌ No content extracted from {normalized_url}")
                    logger.error(f"Result structure: {result}")
                    logger.error(f"Result keys: {list(result.keys()) if result else 'None'}")
                    
                    # Try to provide more specific error information
                    if result.get("errors"):
                        error_msg = f"Content extraction failed: {', '.join(result['errors'])}"
                    elif not result.get("is_accessible"):
                        error_msg = f"Website not accessible: {normalized_url}"
                    elif not result.get("is_suitable"):
                        error_msg = f"Website not suitable for evaluation: {normalized_url}"
                    else:
                        error_msg = f"No content could be extracted from {normalized_url}. Check if the website is accessible and try again."
                    
                    background_tasks_store[task_id]["status"] = "failed"
                    background_tasks_store[task_id]["error"] = error_msg
                    return
                    
            except Exception as e:
                logger.error(f"❌ Error during content extraction: {str(e)}")
                background_tasks_store[task_id]["status"] = "failed"
                background_tasks_store[task_id]["error"] = f"Failed to extract website content: {str(e)}"
                return
        
        if not site_content:
            logger.error(f"❌ Website content not found for {normalized_url} (original: {website_url})")
            background_tasks_store[task_id]["status"] = "failed"
            background_tasks_store[task_id]["error"] = f"Website content not found for {normalized_url}. Please verify the link first."
            return
        
        logger.info(f"✅ Retrieved {len(site_content)} characters of website content")
        background_tasks_store[task_id]["message"] = f"Retrieved {len(site_content)} characters of website content"
        background_tasks_store[task_id]["progress"] = 30
        
        # Initialize AI agent service
        logger.info(f"🤖 Initializing AI agent service...")
        background_tasks_store[task_id]["message"] = "Initializing AI agent service..."
        background_tasks_store[task_id]["progress"] = 40
        
        ai_service = AIAgentService(settings.anthropic_api_key, settings.model_speed)
        
        # Launch all AI agents with progressive updates
        logger.info(f"🚀 Starting AI agent launch process...")
        background_tasks_store[task_id]["message"] = "Generating AI profiles and launching agents..."
        background_tasks_store[task_id]["progress"] = 50
        
        # Create callback for progressive updates
        def on_agent_complete(agent_result):
            # Handle initialization of pending agents
            if agent_result.get("action") == "initialize":
                logger.info(f"🔄 Initializing {len(agent_result['agents'])} pending agents in incremental store")
                incremental_results_store[task_id] = agent_result["agents"]
                return
            
            logger.info(f"📝 Agent completed: {agent_result.get('name', 'Unknown')}")
            # Update the specific agent in the results list
            if task_id in incremental_results_store:
                for i, agent in enumerate(incremental_results_store[task_id]):
                    if agent["id"] == agent_result["id"]:
                        incremental_results_store[task_id][i] = agent_result
                        break
            
            # Update progress based on completed agents
            completed_count = len([a for a in incremental_results_store.get(task_id, []) if a.get("status") == "completed"])
            total_agents = 30  # Total agent count
            progress = min(50 + (completed_count / total_agents) * 50, 99)
            background_tasks_store[task_id]["progress"] = int(progress)
            background_tasks_store[task_id]["message"] = f"Generated {completed_count} reviews..."
        
        # Initialize incremental store with pending agents first
        # This ensures the callback can update agents as they complete
        logger.info("🔄 Initializing incremental results store with pending agents...")
        results = await ai_service.launch_all_agents(site_content, target_audience, on_agent_complete)
        
        # Store all agents (including pending ones) in incremental results store
        incremental_results_store[task_id] = results
        
        logger.info(f"🎉 AI agent launch completed successfully! Generated {len(results)} reviews")
        
        # Debug: Log agent status breakdown
        completed_agents = len([a for a in results if a.get("status") == "completed"])
        pending_agents = len([a for a in results if a.get("status") == "pending"])
        reviewing_agents = len([a for a in results if a.get("status") == "reviewing"])
        logger.info(f"📊 Agent Status Breakdown: {completed_agents} completed, {reviewing_agents} reviewing, {pending_agents} pending")
        
        # Update final status
        background_tasks_store[task_id]["status"] = "completed"
        background_tasks_store[task_id]["message"] = f"Successfully completed! Generated {len(results)} reviews"
        background_tasks_store[task_id]["progress"] = 100
        background_tasks_store[task_id]["results"] = results
        incremental_results_store[task_id] = results  # Store final results
        
    except Exception as e:
        logger.error(f"💥 Background AI Launch failed: {str(e)}")
        background_tasks_store[task_id]["status"] = "failed"
        background_tasks_store[task_id]["error"] = str(e)

@router.post("/ai-launch")
async def launch_ai_agents(request: AILaunchRequest, background_tasks: BackgroundTasks):
    """Start AI agents launch as background task and return immediately"""
    from app.logger import get_module_logger
    logger = get_module_logger(__name__)
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    logger.info(f"🚀 AI Launch API called for URL: {request.website_url}")
    logger.info(f"🎯 Target audience: {request.target_audience}")
    logger.info(f"📋 Task ID: {task_id}")
    
    # Initialize task status
    background_tasks_store[task_id] = {
        "task_id": task_id,
        "status": "started",
        "message": "AI agent launch initiated...",
        "progress": 0,
        "results": None,
        "error": None,
        "website_url": request.website_url,
        "target_audience": request.target_audience
    }
    
    # Start background task
    background_tasks.add_task(
        run_ai_agents_background, 
        task_id, 
        request.website_url, 
        request.target_audience
    )
    
    logger.info(f"✅ Background task started with ID: {task_id}")
    
    # Return immediately with task ID
    return {
        "task_id": task_id,
        "status": "started",
        "message": "AI agent launch started in background",
        "website_url": request.website_url,
        "target_audience": request.target_audience
    }

@router.get("/ai-status/{task_id}")
async def get_ai_task_status(task_id: str):
    """Get the status of a background AI agent task"""
    from app.logger import get_module_logger
    logger = get_module_logger(__name__)
    
    if task_id not in background_tasks_store:
        logger.warning(f"⚠️ Task ID not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = background_tasks_store[task_id]
    
    # Log status check
    logger.info(f"📊 Status check for task {task_id}: {task_data['status']} ({task_data['progress']}%)")
    
    return TaskStatus(**task_data)

# Agent deletion not needed - agents are ephemeral

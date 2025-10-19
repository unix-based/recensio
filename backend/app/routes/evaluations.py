"""
Evaluation Routes - Manage product evaluations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from pydantic import BaseModel
import asyncio
from app.schemas.evaluation import EvaluationCreate, EvaluationResponse
from app.services.evaluation_service import EvaluationService
from app.services.link_verification_service import LinkVerificationService
from app.services.cache_service import CacheService
from app.services.agent_storage_service import AgentStorageService
from app.dependencies import get_agent_storage_service

router = APIRouter()

# Global dict to track background extraction status
extraction_status = {}

async def extract_site_in_background(url: str):
    """Background task to extract complete site content"""
    from app.logger import get_module_logger
    logger = get_module_logger(__name__)
    
    try:
        extraction_status[url] = {"status": "in_progress", "message": "Extracting complete site content..."}
        logger.info(f"🔄 Starting background site extraction for {url}")
        
        verification_service = LinkVerificationService()
        cache_service = CacheService()
        
        # Check if already stored to avoid duplicate work
        if cache_service.snapshot_exists(url):
            extraction_status[url] = {"status": "completed", "message": "Site content already available"}
            logger.info(f"✅ Site {url} already stored, skipping extraction")
            return
        
        # Perform full site extraction
        result = await verification_service.comprehensive_verification(url, extract_full_site=True)
        
        if result.get("errors"):
            extraction_status[url] = {
                "status": "failed", 
                "message": f"Extraction failed: {result['errors'][0]}"
            }
            logger.error(f"❌ Background extraction failed for {url}: {result['errors'][0]}")
            return
        
        # Store the extracted content
        if result.get("complete_site_content") and "site_snapshot" in result:
            from app.services.link_verification_service import SiteSnapshot, PageContent, UsefulLink
            
            main_page_data = result["complete_site_content"]["main_page"]
            main_page = PageContent(
                url=main_page_data["url"],
                html=main_page_data["html"],
                text=main_page_data["text"],
                title=main_page_data["title"],
                meta_description=main_page_data["meta_description"],
                links=[]
            )
            
            internal_pages = []
            for page_data in result["complete_site_content"]["internal_pages"]:
                page = PageContent(
                    url=page_data["url"],
                    html=page_data["html"],
                    text=page_data["text"],
                    title=page_data["title"],
                    meta_description=page_data["meta_description"],
                    links=[]
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
            
            storage_id = cache_service.store_site_snapshot(snapshot)
            extraction_status[url] = {
                "status": "completed", 
                "message": f"Complete site extracted and stored (ID: {storage_id})",
                "pages_extracted": result["site_snapshot"]["total_pages"],
                "useful_links": len(result.get("useful_links", [])),
                "storage_id": storage_id
            }
            logger.success(f"✅ Background extraction completed for {url} - stored with ID {storage_id}")
        else:
            extraction_status[url] = {"status": "failed", "message": "Failed to extract site content"}
            logger.error(f"❌ Background extraction failed for {url}: No content extracted")
            
    except Exception as e:
        extraction_status[url] = {"status": "failed", "message": f"Extraction error: {str(e)}"}
        logger.error(f"❌ Background extraction exception for {url}: {str(e)}")

@router.get("/", response_model=List[EvaluationResponse])
async def get_evaluations(agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get all evaluations"""
    service = EvaluationService(agent_storage)
    return service.get_all_evaluations()

@router.get("/stored-sites")
async def list_stored_sites(agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """List all stored site snapshots"""
    storage_service = SiteStorageService()
    snapshots = cache_service.list_stored_snapshots()
    stats = cache_service.get_storage_stats()
    
    return {
        "stored_snapshots": snapshots,
        "storage_stats": stats
    }

@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(evaluation_id: int, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get specific evaluation by ID"""
    service = EvaluationService(agent_storage)
    evaluation = service.get_evaluation_by_id(evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation

@router.post("/", response_model=EvaluationResponse)
async def create_evaluation(evaluation_data: EvaluationCreate, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Create new evaluation"""
    service = EvaluationService(agent_storage)
    return service.create_evaluation(evaluation_data)

@router.post("/simulate")
async def simulate_evaluations(product_url: str, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Simulate evaluations from all active agents"""
    service = EvaluationService(agent_storage)
    results = service.simulate_all_agent_evaluations(product_url)
    return {
        "message": f"Simulated evaluations for {len(results)} agents",
        "evaluations": results
    }

@router.get("/summary/{product_url}")
async def get_evaluation_summary(product_url: str, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get evaluation summary for a product from real data"""
    from app.services.dashboard_service import DashboardService
    # Using Valkey/Redis for storage
    
    service = DashboardService(db)
    stats = service.get_overall_stats()
    
    # Get evaluations for this product
    evaluations = db.query(Evaluation).all()
    
    completed_evaluations = [e for e in evaluations if e.overall_score is not None]
    
    # Calculate rating distribution
    rating_dist = {
        "91-100": 0, "81-90": 0, "71-80": 0, "61-70": 0, "51-60": 0,
        "41-50": 0, "31-40": 0, "21-30": 0, "11-20": 0, "1-10": 0
    }
    
    for eval in completed_evaluations:
        score = eval.overall_score or 0
        if score >= 91: rating_dist["91-100"] += 1
        elif score >= 81: rating_dist["81-90"] += 1
        elif score >= 71: rating_dist["71-80"] += 1
        elif score >= 61: rating_dist["61-70"] += 1
        elif score >= 51: rating_dist["51-60"] += 1
        elif score >= 41: rating_dist["41-50"] += 1
        elif score >= 31: rating_dist["31-40"] += 1
        elif score >= 21: rating_dist["21-30"] += 1
        elif score >= 11: rating_dist["11-20"] += 1
        else: rating_dist["1-10"] += 1
    
    # Get top reviews (highest rated completed evaluations)
    top_evals = sorted(
        completed_evaluations,
        key=lambda x: x.overall_score or 0,
        reverse=True
    )[:3]
    
    top_reviews = []
    for eval in top_evals:
        if eval.feedback:
            top_reviews.append({
                "agent": {
                    "name": "Anonymous Agent",
                    "emoji": "🤖",
                    "rating": eval.overall_score or 0
                },
                "review": eval.feedback
            })
    
    # Since agents are ephemeral, we can't provide demographic insights
    # based on persistent agent data. Return empty arrays.
    by_age = []
    by_life_views = []
    
    return {
        "product_url": product_url,
        "total_evaluations": stats["total_evaluations"],
        "completed_evaluations": len(completed_evaluations),
        "average_ratings": stats["average_scores"],
        "rating_distribution": rating_dist,
        "top_reviews": top_reviews,
        "demographic_insights": {
            "by_age": by_age,
            "by_life_views": by_life_views
        }
    }

class LinkCheckRequest(BaseModel):
    url: str

class LinkCheckResponse(BaseModel):
    is_valid: bool
    message: str
    url: str

@router.post("/check-link")
async def check_link(request: LinkCheckRequest, background_tasks: BackgroundTasks, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Fast site verification with background complete site extraction"""
    try:
        verification_service = LinkVerificationService()
        cache_service = CacheService()
        
        # Check if we already have this site stored
        stored_snapshot = cache_service.get_site_snapshot_by_url(request.url)
        if stored_snapshot:
            return {
                "is_valid": True,
                "is_accessible": True, 
                "is_suitable": True,
                "message": "Site verification successful - complete content available",
                "url": request.url,
                "extraction_status": "completed",
                "site_snapshot": {
                    "url": stored_snapshot["metadata"]["url"],
                    "total_pages": stored_snapshot["metadata"]["total_pages"],
                    "useful_links_count": stored_snapshot["metadata"]["useful_links_count"],
                    "combined_text_length": stored_snapshot["metadata"]["total_content_length"],
                    "extraction_timestamp": stored_snapshot["metadata"]["extraction_timestamp"],
                    "stored_at": stored_snapshot["metadata"]["created_at"]
                },
                "details": {
                    "status_code": 200,
                    "from_storage": True,
                    "background_extraction": "not_needed"
                }
            }
        
        # Perform FAST verification (main page only for speed)
        result = await verification_service.comprehensive_verification(request.url, extract_full_site=False)
        
        # FAIL with HTTP error if verification failed
        if result["errors"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "is_valid": result["is_valid"],
                    "is_accessible": result["is_accessible"], 
                    "is_suitable": result["is_suitable"],
                    "message": result["errors"][0],
                    "url": result.get("normalized_url", request.url),
                    "details": {
                        "status_code": result.get("status_code"),
                        "suitability": result.get("suitability"),
                        "all_errors": result["errors"]
                    }
                }
            )
        
        # START background extraction task (non-blocking)
        normalized_url = result.get("normalized_url", request.url)
        background_tasks.add_task(extract_site_in_background, normalized_url)
        extraction_status[normalized_url] = {"status": "queued", "message": "Background extraction queued"}
        
        from app.logger import get_module_logger
        logger = get_module_logger(__name__)
        logger.info(f"⚡ Fast verification completed for {request.url} - background extraction started")
        
        # Return SUCCESS immediately to allow UI progression
        return {
            "is_valid": result["is_valid"],
            "is_accessible": result["is_accessible"], 
            "is_suitable": result["is_suitable"],
            "message": "Site verification successful - extracting complete content in background",
            "url": normalized_url,
            "extraction_status": "in_progress",
            "main_content": result.get("main_content", {}),
            "details": {
                "status_code": result.get("status_code"),
                "suitability": result.get("suitability"),
                "from_storage": False,
                "background_extraction": "started",
                "fast_verification": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "is_valid": False,
                "is_accessible": False,
                "is_suitable": False,
                "message": f"Verification error: {str(e)}",
                "url": request.url,
                "details": {}
            }
        )

class CompleteSiteExtractionRequest(BaseModel):
    url: str
    max_pages: int = 15

@router.post("/extract-complete-site")
async def extract_complete_site(request: CompleteSiteExtractionRequest, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Extract complete site content with AI-powered link analysis and verification"""
    try:
        verification_service = LinkVerificationService()
        cache_service = CacheService()
        
        # Check if we already have this site stored
        stored_snapshot = cache_service.get_site_snapshot_by_url(request.url)
        if stored_snapshot:
            return {
                "is_valid": True,
                "is_accessible": True, 
                "is_suitable": True,
                "message": "Complete site content retrieved from storage",
                "url": request.url,
                "site_snapshot": {
                    "url": stored_snapshot["metadata"]["url"],
                    "total_pages": stored_snapshot["metadata"]["total_pages"],
                    "useful_links_count": stored_snapshot["metadata"]["useful_links_count"],
                    "combined_text_length": stored_snapshot["metadata"]["total_content_length"],
                    "extraction_timestamp": stored_snapshot["metadata"]["extraction_timestamp"],
                    "stored_at": stored_snapshot["metadata"]["created_at"]
                },
                "useful_links": stored_snapshot["content"]["useful_links"],
                "complete_site_content": stored_snapshot["content"],
                "extraction_stats": {
                    "total_pages_extracted": stored_snapshot["metadata"]["total_pages"],
                    "useful_links_found": stored_snapshot["metadata"]["useful_links_count"],
                    "total_content_length": stored_snapshot["metadata"]["total_content_length"],
                    "total_html_length": len(stored_snapshot["content"]["combined_html"])
                },
                "details": {
                    "from_storage": True,
                    "last_updated": stored_snapshot["metadata"]["last_updated"]
                }
            }
        
        # Extract fresh content
        result = await verification_service.comprehensive_verification(
            request.url, 
            extract_full_site=True
        )
        
        # FAIL with HTTP error if verification failed
        if result["errors"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "is_valid": result["is_valid"],
                    "is_accessible": result["is_accessible"], 
                    "is_suitable": result["is_suitable"],
                    "message": result["errors"][0],
                    "url": result.get("normalized_url", request.url),
                    "details": {
                        "status_code": result.get("status_code"),
                        "suitability": result.get("suitability"),
                        "all_errors": result["errors"]
                    }
                }
            )
        
        # Store the extracted content if successful
        if result.get("complete_site_content") and "site_snapshot" in result:
            try:
                # Create SiteSnapshot object from result for storage
                from app.services.link_verification_service import SiteSnapshot, PageContent, UsefulLink
                from datetime import datetime
                
                main_page_data = result["complete_site_content"]["main_page"]
                main_page = PageContent(
                    url=main_page_data["url"],
                    html=main_page_data["html"],
                    text=main_page_data["text"],
                    title=main_page_data["title"],
                    meta_description=main_page_data["meta_description"],
                    links=[]  # Not needed for storage
                )
                
                internal_pages = []
                for page_data in result["complete_site_content"]["internal_pages"]:
                    page = PageContent(
                        url=page_data["url"],
                        html=page_data["html"],
                        text=page_data["text"],
                        title=page_data["title"],
                        meta_description=page_data["meta_description"],
                        links=[]  # Not needed for storage
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
                
                # Store the snapshot
                storage_id = cache_service.store_site_snapshot(snapshot)
                result["storage_id"] = storage_id
                
            except Exception as e:
                # Don't fail the request if storage fails, just log it
                from app.logger import get_module_logger
                logger = get_module_logger(__name__)
                logger.error(f"Failed to store site snapshot: {str(e)}")
        
        # Return complete site extraction results
        return {
            "is_valid": result["is_valid"],
            "is_accessible": result["is_accessible"], 
            "is_suitable": result["is_suitable"],
            "message": "Complete site extraction successful",
            "url": result.get("normalized_url", request.url),
            "site_snapshot": result.get("site_snapshot", {}),
            "useful_links": result.get("useful_links", []),
            "complete_site_content": result.get("complete_site_content", {}),
            "extraction_stats": {
                "total_pages_extracted": result.get("pages_extracted", 0),
                "useful_links_found": len(result.get("useful_links", [])),
                "total_content_length": result.get("total_content", {}).get("combined_text_length", 0),
                "total_html_length": result.get("total_content", {}).get("combined_html_length", 0)
            },
            "details": {
                "status_code": result.get("status_code"),
                "suitability": result.get("suitability"),
                "from_storage": False,
                "storage_id": result.get("storage_id")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "is_valid": False,
                "is_accessible": False,
                "is_suitable": False,
                "message": f"Complete site extraction error: {str(e)}",
                "url": request.url,
                "details": {}
            }
        )

@router.get("/stored-site/{url:path}")
async def get_stored_site(url: str, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get a stored site snapshot by URL"""
    storage_service = SiteStorageService()
    snapshot = cache_service.get_site_snapshot_by_url(url)
    
    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail=f"No stored snapshot found for URL: {url}"
        )
    
    return {
        "message": "Site snapshot retrieved successfully",
        "url": url,
        "snapshot": snapshot
    }

@router.delete("/stored-site/{url:path}")
async def delete_stored_site(url: str, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Delete a stored site snapshot by URL"""
    storage_service = SiteStorageService()
    success = cache_service.delete_snapshot_by_url(url)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No stored snapshot found for URL: {url}"
        )
    
    return {
        "message": f"Site snapshot deleted successfully for {url}",
        "url": url
    }

@router.get("/site-content-for-profiles/{url:path}")
async def get_site_content_for_profiles(url: str, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get site content formatted for AI profile generation and audience selection"""
    storage_service = SiteStorageService()
    profile_data = cache_service.get_site_content_for_profile_generation(url)
    
    if not profile_data:
        raise HTTPException(
            status_code=404,
            detail=f"No stored site content found for URL: {url}. Please verify the site first."
        )
    
    return {
        "message": "Site content retrieved for profile generation",
        "url": url,
        "profile_data": profile_data
    }

@router.get("/business-summary/{url:path}")
async def get_business_summary_for_ai(url: str, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get a concise business summary optimized for AI audience generation"""
    storage_service = SiteStorageService()
    business_summary = cache_service.get_business_summary_for_ai(url)
    
    if not business_summary:
        raise HTTPException(
            status_code=404,
            detail=f"No stored site content found for URL: {url}. Please verify the site first."
        )
    
    return {
        "message": "Business summary retrieved for AI processing",
        "url": url,
        "business_summary": business_summary
    }

@router.get("/extraction-status/{url:path}")
async def get_extraction_status(url: str, agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Check the status of background site extraction"""
    storage_service = SiteStorageService()
    
    # First check if already completed and stored
    if cache_service.snapshot_exists(url):
        stored_snapshot = cache_service.get_site_snapshot_by_url(url)
        return {
            "url": url,
            "status": "completed",
            "message": "Site extraction completed and stored",
            "completed": True,
            "details": {
                "total_pages": stored_snapshot["metadata"]["total_pages"] if stored_snapshot else 0,
                "useful_links": stored_snapshot["metadata"]["useful_links_count"] if stored_snapshot else 0,
                "storage_timestamp": stored_snapshot["metadata"]["created_at"] if stored_snapshot else None
            }
        }
    
    # Check background extraction status
    status = extraction_status.get(url, {"status": "not_started", "message": "No extraction requested for this URL"})
    
    return {
        "url": url,
        "status": status["status"],
        "message": status["message"],
        "completed": status["status"] == "completed",
        "details": {
            "pages_extracted": status.get("pages_extracted", 0),
            "useful_links": status.get("useful_links", 0),
            "storage_id": status.get("storage_id")
        }
    }

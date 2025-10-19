"""
Site Storage Service - Store and retrieve complete site snapshots using Valkey/Redis
"""

import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any
from app.logger import get_module_logger, log_info, log_error, log_success, log_warning
from app.services.link_verification_service import SiteSnapshot, PageContent, UsefulLink
from app.services.cache_service import CacheService
from app.config import settings
from app.standards import TypeHints, LoggingPatterns, StandardizedDocstring

logger = get_module_logger(__name__)


class SiteStorageService:
    """Service for storing and retrieving complete site snapshots using Valkey/Redis.
    
    This service provides persistent storage for website snapshots using Valkey/Redis
    as the backend storage system. It handles metadata and content storage with
    automatic TTL management and efficient retrieval.
    """
    
    def __init__(self) -> None:
        """Initialize the site storage service with Valkey/Redis backend.
        
        Sets up the cache service with a 24-hour TTL for site snapshots.
        """
        self.cache_service = CacheService(ttl=86400)  # 24 hours TTL
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize the Valkey/Redis connection.
        
        Raises:
            ConnectionError: If unable to connect to Valkey/Redis
        """
        try:
            # CacheService already initializes Redis connection in __init__
            log_success(LoggingPatterns.SERVICE_READY.format(service="Site Storage"))
        except Exception as e:
            log_error(LoggingPatterns.SERVICE_ERROR.format(service="Site Storage", error=str(e)))
            raise

    def _get_url_hash(self, url: str) -> str:
        """Generate a hash for the URL for efficient lookups.
        
        Args:
            url: The URL to hash
            
        Returns:
            SHA256 hash of the URL as a hexadecimal string
        """
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def store_site_snapshot(self, snapshot: SiteSnapshot) -> str:
        """Store a complete site snapshot in Valkey/Redis.
        
        Args:
            snapshot: SiteSnapshot object containing all site data
            
        Returns:
            URL hash string used as the storage key
            
        Raises:
            StorageError: If unable to store the snapshot
        """
        log_info(LoggingPatterns.START_OPERATION.format(operation="site snapshot storage", target=snapshot.url))
        
        url_hash = self._get_url_hash(snapshot.url)
        
        try:
            # Prepare metadata
            metadata = {
                "url": snapshot.url,
                "url_hash": url_hash,
                "title": snapshot.main_page.title,
                "total_pages": snapshot.total_pages,
                "total_content_length": len(snapshot.complete_text),
                "useful_links_count": len(snapshot.useful_links),
                "extraction_timestamp": snapshot.extraction_timestamp,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            # Prepare content data
            content_data = {
                "combined_html": snapshot.complete_html,
                "combined_text": snapshot.complete_text,
                "main_page": {
                    "url": snapshot.main_page.url,
                    "html": snapshot.main_page.html,
                    "text": snapshot.main_page.text,
                    "title": snapshot.main_page.title,
                    "meta_description": snapshot.main_page.meta_description,
                    "links": snapshot.main_page.links
                },
                "internal_pages": [{
                    "url": page.url,
                    "html": page.html,
                    "text": page.text,
                    "title": page.title,
                    "meta_description": page.meta_description,
                    "links": page.links
                } for page in snapshot.internal_pages],
                "useful_links": [{
                    "url": link.url,
                    "title": link.title,
                    "reason": link.reason,
                    "priority": link.priority
                } for link in snapshot.useful_links]
            }
            
            # Store using cache service
            self.cache_service.store_site_snapshot_data(snapshot.url, metadata, content_data)
            
            log_success(LoggingPatterns.COMPLETE_OPERATION.format(operation="site snapshot storage", target=snapshot.url))
            return url_hash
            
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="site snapshot storage", target=snapshot.url, error=str(e)))
            raise

    def get_site_snapshot_by_url(self, url: str) -> TypeHints.OptionalDict:
        """Retrieve a site snapshot by URL from Valkey/Redis.
        
        Args:
            url: The URL to retrieve snapshot for
            
        Returns:
            Dictionary containing metadata and content, or None if not found
        """
        try:
            snapshot_data = self.cache_service.get_site_snapshot(url)
            if not snapshot_data:
                return None
                
            return {
                "metadata": snapshot_data["metadata"],
                "content": snapshot_data["content"]
            }
                
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="site snapshot retrieval", target=url, error=str(e)))
            return None

    def list_stored_snapshots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all stored site snapshots (metadata only) from Valkey/Redis.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List of snapshot metadata dictionaries
        """
        try:
            snapshots = self.cache_service.list_site_snapshots()
            # Sort by last_updated and limit
            snapshots.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
            return snapshots[:limit]
                
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="site snapshots listing", target="all", error=str(e)))
            return []

    def delete_snapshot_by_url(self, url: str) -> bool:
        """Delete a site snapshot by URL from Valkey/Redis.
        
        Args:
            url: The URL to delete snapshot for
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            success = self.cache_service.delete_site_snapshot(url)
            if success:
                log_success(LoggingPatterns.DATA_DELETED.format(entity_type="site snapshot", entity_id=url))
                return True
            else:
                log_warning(f"No snapshot found to delete for {url}")
                return False
                    
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="site snapshot deletion", target=url, error=str(e)))
            return False

    def get_combined_content_for_url(self, url: str) -> TypeHints.OptionalString:
        """Get just the combined text content for a URL (optimized for AI processing).
        
        Args:
            url: The URL to get content for
            
        Returns:
            Combined text content string, or None if not found
        """
        snapshot_data = self.get_site_snapshot_by_url(url)
        if snapshot_data and snapshot_data.get("content"):
            return snapshot_data["content"]["combined_text"]
        return None

    def get_site_content_for_profile_generation(self, url: str) -> TypeHints.OptionalDict:
        """Get site content formatted specifically for AI profile generation and audience selection.
        
        Args:
            url: The URL to get content for
            
        Returns:
            Structured content data for AI processing, or None if not found
        """
        snapshot_data = self.get_site_snapshot_by_url(url)
        if not snapshot_data:
            return None
            
        content = snapshot_data["content"]
        metadata = snapshot_data["metadata"]
        
        # Format useful links for AI analysis
        useful_links_summary = []
        for link in content["useful_links"]:
            useful_links_summary.append(f"- {link['title']} ({link['url']}) - {link['reason']} [Priority: {link['priority']}]")
        
        # Create a structured summary for AI consumption
        return {
            "website_url": metadata["url"],
            "website_title": metadata["title"],
            "total_pages_analyzed": metadata["total_pages"],
            "content_quality_score": metadata["useful_links_count"],
            
            # Main business content for understanding the product/service
            "main_page_content": {
                "title": content["main_page"]["title"],
                "meta_description": content["main_page"]["meta_description"],
                "text_content": content["main_page"]["text"][:5000],  # First 5000 chars for main page
            },
            
            # Combined content from all useful pages
            "complete_business_content": content["combined_text"],
            
            # AI-identified valuable pages
            "useful_pages_summary": useful_links_summary,
            
            # Individual page summaries for detailed analysis
            "key_pages": [
                {
                    "url": page["url"],
                    "title": page["title"],
                    "content_preview": page["text"][:1000],  # First 1000 chars per page
                    "content_length": len(page["text"])
                }
                for page in content["internal_pages"][:10]  # Top 10 pages
            ],
            
            # Metadata for AI context
            "extraction_info": {
                "total_content_length": len(content["combined_text"]),
                "extraction_timestamp": metadata["extraction_timestamp"],
                "pages_count": metadata["total_pages"]
            }
        }

    def get_business_summary_for_ai(self, url: str) -> TypeHints.OptionalString:
        """Get a concise business summary optimized for AI processing (audience generation, etc.).
        
        Args:
            url: The URL to get business summary for
            
        Returns:
            Formatted business summary string, or None if not found
        """
        profile_data = self.get_site_content_for_profile_generation(url)
        if not profile_data:
            return None
            
        # Create a structured summary for AI
        summary_parts = [
            f"WEBSITE: {profile_data['website_title']} ({profile_data['website_url']})",
            f"\nMAIN DESCRIPTION: {profile_data['main_page_content']['meta_description']}",
            f"\nCORE CONTENT:\n{profile_data['main_page_content']['text_content']}",
            f"\nKEY PAGES IDENTIFIED:"
        ]
        
        # Add useful pages summary
        for link_summary in profile_data['useful_pages_summary'][:8]:  # Top 8 useful pages
            summary_parts.append(link_summary)
            
        # Add extraction stats
        summary_parts.append(f"\nCONTENT ANALYSIS: Analyzed {profile_data['extraction_info']['pages_count']} pages, "
                           f"{profile_data['extraction_info']['total_content_length']} total characters")
        
        return "\n".join(summary_parts)

    def snapshot_exists(self, url: str) -> bool:
        """Check if a snapshot exists for the given URL in Valkey/Redis.
        
        Args:
            url: The URL to check for existence
            
        Returns:
            True if snapshot exists, False otherwise
        """
        try:
            return self.cache_service.snapshot_exists(url)
        except Exception:
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics from Valkey/Redis.
        
        Returns:
            Dictionary containing storage statistics and metadata
        """
        try:
            stats = self.cache_service.get_storage_stats()
            return {
                "total_snapshots": stats.get("total_snapshots", 0),
                "total_content_length": stats.get("total_content_length", 0),
                "total_pages_stored": stats.get("total_pages_stored", 0),
                "storage_type": "Valkey/Redis",
                "redis_url": self.cache_service.redis_url
            }
                
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="storage statistics retrieval", target="system", error=str(e)))
            return {"error": str(e)}
"""
Cache Service - Valkey/Redis-based caching for site snapshots and content
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import redis
from app.config import settings
from app.logger import get_module_logger
from app.services.link_verification_service import SiteSnapshot, PageContent, UsefulLink

logger = get_module_logger(__name__)


class CacheService:
    """Service for caching site snapshots and content using Valkey/Redis"""
    
    def __init__(self, redis_url: str = None, ttl: int = None):
        self.redis_url = redis_url or settings.valkey_url
        self.ttl = ttl or settings.cache_ttl
        self._redis_client = None
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection"""
        try:
            logger.info(f"Attempting to connect to Valkey/Redis at {self.redis_url}")
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._redis_client.ping()
            logger.info(f"✅ Connected to Valkey/Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Valkey/Redis: {str(e)}")
            logger.error(f"Redis URL: {self.redis_url}")
            raise
    
    def _get_redis(self):
        """Get Redis client, reconnect if needed"""
        try:
            self._redis_client.ping()
            return self._redis_client
        except:
            logger.warning("Redis connection lost, reconnecting...")
            self._connect()
            return self._redis_client
    
    def _get_url_hash(self, url: str) -> str:
        """Generate a hash for the URL for efficient lookups"""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()
    
    def _get_snapshot_key(self, url: str) -> str:
        """Get cache key for site snapshot"""
        url_hash = self._get_url_hash(url)
        return f"site_snapshot:{url_hash}"
    
    def _get_content_key(self, url: str) -> str:
        """Get cache key for site content"""
        url_hash = self._get_url_hash(url)
        return f"site_content:{url_hash}"
    
    def _get_metadata_key(self, url: str) -> str:
        """Get cache key for site metadata"""
        url_hash = self._get_url_hash(url)
        return f"site_metadata:{url_hash}"
    
    def store_site_snapshot(self, snapshot: SiteSnapshot) -> bool:
        """Store a complete site snapshot in the cache"""
        logger.info(f"Storing site snapshot for {snapshot.url}")
        
        try:
            redis_client = self._get_redis()
            
            # Store metadata
            metadata = {
                "url": snapshot.url,
                "title": snapshot.main_page.title,
                "total_pages": snapshot.total_pages,
                "total_content_length": len(snapshot.complete_text),
                "useful_links_count": len(snapshot.useful_links),
                "extraction_timestamp": snapshot.extraction_timestamp,
                "created_at": datetime.utcnow().isoformat()
            }
            
            metadata_key = self._get_metadata_key(snapshot.url)
            redis_client.hset(metadata_key, mapping=metadata)
            redis_client.expire(metadata_key, self.ttl)
            
            # Store content (split into chunks if too large)
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
            
            content_key = self._get_content_key(snapshot.url)
            
            # Store content as JSON (Redis has size limits, so we might need to chunk)
            content_json = json.dumps(content_data)
            if len(content_json) > 500 * 1024 * 1024:  # 500MB limit
                logger.warning(f"Content too large for single Redis key, storing in chunks")
                # Store in chunks
                chunk_size = 100 * 1024 * 1024  # 100MB chunks
                for i, chunk in enumerate([content_json[j:j+chunk_size] for j in range(0, len(content_json), chunk_size)]):
                    chunk_key = f"{content_key}:chunk:{i}"
                    redis_client.set(chunk_key, chunk, ex=self.ttl)
                redis_client.set(f"{content_key}:chunks", len([content_json[j:j+chunk_size] for j in range(0, len(content_json), chunk_size)]), ex=self.ttl)
            else:
                redis_client.set(content_key, content_json, ex=self.ttl)
            
            logger.success(f"Successfully cached site snapshot for {snapshot.url}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching site snapshot for {snapshot.url}: {str(e)}")
            return False
    
    def get_site_snapshot_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve a site snapshot by URL"""
        try:
            redis_client = self._get_redis()
            
            # Get metadata
            metadata_key = self._get_metadata_key(url)
            metadata = redis_client.hgetall(metadata_key)
            if not metadata:
                return None
            
            # Get content
            content_key = self._get_content_key(url)
            content_json = redis_client.get(content_key)
            
            if not content_json:
                # Try to get chunked content
                chunks_count = redis_client.get(f"{content_key}:chunks")
                if chunks_count:
                    chunks = []
                    for i in range(int(chunks_count)):
                        chunk = redis_client.get(f"{content_key}:chunk:{i}")
                        if chunk:
                            chunks.append(chunk)
                    content_json = "".join(chunks)
                else:
                    return None
            
            content_data = json.loads(content_json)
            
            return {
                "metadata": metadata,
                "content": content_data
            }
            
        except Exception as e:
            logger.error(f"Error retrieving site snapshot for {url}: {str(e)}")
            return None
    
    def list_stored_snapshots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all stored site snapshots (metadata only)"""
        try:
            redis_client = self._get_redis()
            
            # Get all metadata keys
            pattern = "site_metadata:*"
            keys = redis_client.keys(pattern)
            
            snapshots = []
            for key in keys[:limit]:
                metadata = redis_client.hgetall(key)
                if metadata:
                    snapshots.append(metadata)
            
            # Sort by created_at if available
            snapshots.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return snapshots
            
        except Exception as e:
            logger.error(f"Error listing stored snapshots: {str(e)}")
            return []
    
    def delete_snapshot_by_url(self, url: str) -> bool:
        """Delete a site snapshot by URL"""
        try:
            redis_client = self._get_redis()
            
            # Delete metadata
            metadata_key = self._get_metadata_key(url)
            redis_client.delete(metadata_key)
            
            # Delete content
            content_key = self._get_content_key(url)
            redis_client.delete(content_key)
            
            # Delete chunked content if exists
            chunks_count = redis_client.get(f"{content_key}:chunks")
            if chunks_count:
                for i in range(int(chunks_count)):
                    redis_client.delete(f"{content_key}:chunk:{i}")
                redis_client.delete(f"{content_key}:chunks")
            
            logger.info(f"Successfully deleted snapshot for {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting snapshot for {url}: {str(e)}")
            return False
    
    def get_combined_content_for_url(self, url: str) -> Optional[str]:
        """Get just the combined text content for a URL (optimized for AI processing)"""
        logger.debug(f"Looking for content for URL: {url}")
        snapshot_data = self.get_site_snapshot_by_url(url)
        if snapshot_data and snapshot_data.get("content"):
            content_length = len(snapshot_data["content"]["combined_text"])
            logger.debug(f"Found content for {url}: {content_length} characters")
            return snapshot_data["content"]["combined_text"]
        else:
            logger.debug(f"No content found for URL: {url}")
        return None
    
    def get_site_content_for_profile_generation(self, url: str) -> Optional[Dict[str, Any]]:
        """Get site content formatted specifically for AI profile generation and audience selection"""
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
            "total_pages_analyzed": int(metadata.get("total_pages", 0)),
            "content_quality_score": int(metadata.get("useful_links_count", 0)),
            
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
                "pages_count": int(metadata.get("total_pages", 0))
            }
        }
    
    def get_business_summary_for_ai(self, url: str) -> Optional[str]:
        """Get a concise business summary optimized for AI processing (audience generation, etc.)"""
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
        """Check if a snapshot exists for the given URL"""
        try:
            redis_client = self._get_redis()
            metadata_key = self._get_metadata_key(url)
            return redis_client.exists(metadata_key) > 0
        except Exception:
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            redis_client = self._get_redis()
            
            # Count metadata keys
            metadata_keys = redis_client.keys("site_metadata:*")
            total_snapshots = len(metadata_keys)
            
            # Get total content length
            total_content_length = 0
            for key in metadata_keys:
                metadata = redis_client.hgetall(key)
                if metadata and 'total_content_length' in metadata:
                    total_content_length += int(metadata['total_content_length'])
            
            # Get total pages
            total_pages = 0
            for key in metadata_keys:
                metadata = redis_client.hgetall(key)
                if metadata and 'total_pages' in metadata:
                    total_pages += int(metadata['total_pages'])
            
            return {
                "total_snapshots": total_snapshots,
                "total_content_length": total_content_length,
                "total_pages_stored": total_pages,
                "cache_ttl": self.ttl,
                "redis_url": self.redis_url
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {"error": str(e)}
    
    def clear_all_cache(self) -> bool:
        """Clear all cached site snapshots"""
        try:
            redis_client = self._get_redis()
            
            # Get all site-related keys
            patterns = ["site_metadata:*", "site_content:*"]
            for pattern in patterns:
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            
            logger.info("Successfully cleared all site cache")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def health_check(self) -> bool:
        """Check if cache service is healthy"""
        try:
            redis_client = self._get_redis()
            redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return False
    
    # Additional methods for SiteStorageService compatibility
    
    def store_site_snapshot_data(self, url: str, metadata: Dict[str, Any], content_data: Dict[str, Any]) -> bool:
        """Store site snapshot data (compatibility method for SiteStorageService)"""
        try:
            redis_client = self._get_redis()
            
            # Store metadata
            metadata_key = self._get_metadata_key(url)
            redis_client.hset(metadata_key, mapping=metadata)
            redis_client.expire(metadata_key, self.ttl)
            
            # Store content
            content_key = self._get_content_key(url)
            content_json = json.dumps(content_data)
            
            if len(content_json) > 500 * 1024 * 1024:  # 500MB limit
                logger.warning(f"Content too large for single Redis key, storing in chunks")
                # Store in chunks
                chunk_size = 100 * 1024 * 1024  # 100MB chunks
                for i, chunk in enumerate([content_json[j:j+chunk_size] for j in range(0, len(content_json), chunk_size)]):
                    chunk_key = f"{content_key}:chunk:{i}"
                    redis_client.set(chunk_key, chunk, ex=self.ttl)
                redis_client.set(f"{content_key}:chunks", len([content_json[j:j+chunk_size] for j in range(0, len(content_json), chunk_size)]), ex=self.ttl)
            else:
                redis_client.set(content_key, content_json, ex=self.ttl)
            
            logger.info(f"Successfully cached site snapshot for {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching site snapshot for {url}: {str(e)}")
            return False
    
    def get_site_snapshot(self, url: str) -> Optional[Dict[str, Any]]:
        """Get site snapshot (compatibility method for SiteStorageService)"""
        return self.get_site_snapshot_by_url(url)
    
    def list_site_snapshots(self) -> List[Dict[str, Any]]:
        """List site snapshots (compatibility method for SiteStorageService)"""
        return self.list_stored_snapshots()
    
    def delete_site_snapshot(self, url: str) -> bool:
        """Delete site snapshot (compatibility method for SiteStorageService)"""
        return self.delete_snapshot_by_url(url)
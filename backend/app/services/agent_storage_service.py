"""
Agent Storage Service - Store and retrieve agents using Valkey/Redis
"""

import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any
from app.logger import get_module_logger, log_info, log_error, log_success, log_warning
from app.services.cache_service import CacheService
from app.config import settings
from app.standards import TypeHints, LoggingPatterns, StandardizedDocstring

logger = get_module_logger(__name__)


class AgentStorageService:
    """Service for storing and retrieving agents using Valkey/Redis.
    
    This service provides persistent storage for AI agents using Valkey/Redis
    as the backend storage system. It handles agent metadata and profile data
    with automatic TTL management and efficient retrieval.
    """
    
    def __init__(self) -> None:
        """Initialize the agent storage service with Valkey/Redis backend.
        
        Sets up the cache service with a 30-day TTL for agent data.
        """
        self.cache_service = CacheService(ttl=86400 * 30)  # 30 days TTL
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize the Valkey/Redis connection.
        
        Raises:
            ConnectionError: If unable to connect to Valkey/Redis
        """
        try:
            # CacheService already initializes Redis connection in __init__
            log_success(LoggingPatterns.SERVICE_READY.format(service="Agent Storage"))
        except Exception as e:
            log_error(LoggingPatterns.SERVICE_ERROR.format(service="Agent Storage", error=str(e)))
            raise
    
    def _get_agent_key(self, agent_id: int) -> str:
        """Generate a key for agent storage.
        
        Args:
            agent_id: The agent ID to generate key for
            
        Returns:
            Redis key string for the agent
        """
        return f"agent:{agent_id}"
    
    def _get_next_agent_id(self) -> int:
        """Get the next available agent ID.
        
        Returns:
            Next available agent ID (starts at 1 if none exist)
        """
        try:
            redis_client = self.cache_service._get_redis()
            return redis_client.incr("agent:next_id")
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="agent ID generation", target="system", error=str(e)))
            return 1
    
    def create_agent(self, agent_data: Dict[str, Any]) -> TypeHints.AgentData:
        """Create a new agent.
        
        Args:
            agent_data: Dictionary containing agent profile data
            
        Returns:
            Dictionary containing the created agent data with assigned ID
            
        Raises:
            StorageError: If unable to create the agent
        """
        log_info(LoggingPatterns.START_OPERATION.format(operation="agent creation", target=agent_data.get('name', 'Unknown')))
        
        try:
            agent_id = self._get_next_agent_id()
            agent_key = self._get_agent_key(agent_id)
            
            # Prepare agent data
            agent_record = {
                "id": agent_id,
                "name": agent_data.get("name"),
                "age": agent_data.get("age"),
                "gender": agent_data.get("gender"),
                "occupation": agent_data.get("occupation"),
                "life_views": agent_data.get("life_views"),
                "innovation_attitude": agent_data.get("innovation_attitude"),
                "risk_tolerance": agent_data.get("risk_tolerance"),
                "gullibility": agent_data.get("gullibility"),
                "emoji": agent_data.get("emoji"),
                "avatar_color": agent_data.get("avatar_color"),
                "status": agent_data.get("status", "pending"),
                "overall_rating": agent_data.get("overall_rating"),
                "clarity_rating": agent_data.get("clarity_rating"),
                "ux_rating": agent_data.get("ux_rating"),
                "value_proposition_rating": agent_data.get("value_proposition_rating"),
                "review_text": agent_data.get("review_text"),
                "interests": agent_data.get("interests"),
                "tech_savviness": agent_data.get("tech_savviness"),
                "budget_range": agent_data.get("budget_range"),
                "location": agent_data.get("location"),
                "is_active": agent_data.get("is_active", True),
                "created_at": datetime.now().isoformat()
            }
            
            # Store in Redis
            redis_client = self.cache_service._get_redis()
            redis_client.hset(agent_key, mapping=agent_record)
            redis_client.expire(agent_key, self.cache_service.ttl)
            
            # Add to agents list
            redis_client.sadd("agents:list", agent_id)
            
            log_success(LoggingPatterns.DATA_CREATED.format(entity_type="agent", entity_id=agent_id))
            return agent_record
            
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="agent creation", target=agent_data.get('name', 'Unknown'), error=str(e)))
            raise
    
    def get_agent(self, agent_id: int) -> TypeHints.OptionalDict:
        """Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to retrieve
            
        Returns:
            Dictionary containing agent data, or None if not found
        """
        try:
            agent_key = self._get_agent_key(agent_id)
            redis_client = self.cache_service._get_redis()
            
            agent_data = redis_client.hgetall(agent_key)
            if not agent_data:
                return None
            
            # Convert bytes to strings and handle types
            result = {}
            for key, value in agent_data.items():
                key_str = key.decode() if isinstance(key, bytes) else key
                value_str = value.decode() if isinstance(value, bytes) else value
                
                # Convert numeric fields
                if key_str in ["id", "age", "risk_tolerance", "gullibility", "tech_savviness"]:
                    result[key_str] = int(value_str) if value_str else None
                elif key_str in ["overall_rating", "clarity_rating", "ux_rating", "value_proposition_rating"]:
                    result[key_str] = float(value_str) if value_str else None
                elif key_str == "is_active":
                    result[key_str] = value_str.lower() == "true"
                else:
                    result[key_str] = value_str
            
            return result
            
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="agent retrieval", target=f"ID {agent_id}", error=str(e)))
            return None
    
    def update_agent(self, agent_id: int, update_data: Dict[str, Any]) -> TypeHints.OptionalDict:
        """Update an agent.
        
        Args:
            agent_id: The ID of the agent to update
            update_data: Dictionary containing fields to update
            
        Returns:
            Dictionary containing updated agent data, or None if not found
        """
        try:
            agent_key = self._get_agent_key(agent_id)
            redis_client = self.cache_service._get_redis()
            
            # Check if agent exists
            if not redis_client.exists(agent_key):
                return None
            
            # Update fields
            redis_client.hset(agent_key, mapping=update_data)
            redis_client.expire(agent_key, self.cache_service.ttl)
            
            log_success(LoggingPatterns.DATA_UPDATED.format(entity_type="agent", entity_id=agent_id))
            # Return updated agent
            return self.get_agent(agent_id)
            
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="agent update", target=f"ID {agent_id}", error=str(e)))
            return None
    
    def delete_agent(self, agent_id: int) -> bool:
        """Delete an agent.
        
        Args:
            agent_id: The ID of the agent to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            agent_key = self._get_agent_key(agent_id)
            redis_client = self.cache_service._get_redis()
            
            # Remove from agents list
            redis_client.srem("agents:list", agent_id)
            
            # Delete agent data
            deleted = redis_client.delete(agent_key)
            
            log_success(LoggingPatterns.DATA_DELETED.format(entity_type="agent", entity_id=agent_id))
            return deleted > 0
            
        except Exception as e:
            log_error(LoggingPatterns.FAIL_OPERATION.format(operation="agent deletion", target=f"ID {agent_id}", error=str(e)))
            return False
    
    def list_agents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all agents"""
        try:
            redis_client = self.cache_service._get_redis()
            
            # Get agent IDs
            agent_ids = redis_client.smembers("agents:list")
            if not agent_ids:
                return []
            
            # Convert to integers and sort
            agent_ids = sorted([int(aid) for aid in agent_ids])
            
            # Apply pagination
            paginated_ids = agent_ids[offset:offset + limit]
            
            # Get agents
            agents = []
            for agent_id in paginated_ids:
                agent = self.get_agent(agent_id)
                if agent:
                    agents.append(agent)
            
            return agents
            
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            return []
    
    def get_agents_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get agents by status"""
        try:
            all_agents = self.list_agents(limit=1000)  # Get all agents
            return [agent for agent in all_agents if agent.get("status") == status]
            
        except Exception as e:
            logger.error(f"Error getting agents by status {status}: {str(e)}")
            return []
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        try:
            redis_client = self.cache_service._get_redis()
            
            total_agents = redis_client.scard("agents:list")
            
            # Count by status
            all_agents = self.list_agents(limit=1000)
            status_counts = {}
            for agent in all_agents:
                status = agent.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_agents": total_agents,
                "status_counts": status_counts,
                "storage_type": "Valkey/Redis"
            }
            
        except Exception as e:
            logger.error(f"Error getting agent stats: {str(e)}")
            return {"error": str(e)}

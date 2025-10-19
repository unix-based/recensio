"""
Agent Service - Business logic for agent management
"""

from typing import List, Dict, Any, Optional
from app.schemas.agent import AgentCreate
from app.services.agent_storage_service import AgentStorageService
from pydantic_ai import Agent as PydanticAgent
from pydantic import BaseModel, Field
import random
import json
import asyncio
from app.logger import get_module_logger
from app.prompts import (
    get_profile_system_prompt,
    get_targeted_profile_prompt, 
    get_random_profile_prompt,
    get_review_system_prompt,
    get_website_review_prompt
)

logger = get_module_logger(__name__)

class AgentService:
    """Service for managing virtual user agents.
    
    Handles CRUD operations for agent entities and provides
    methods for generating diverse agent profiles.
    """
    
    def __init__(self, agent_storage: AgentStorageService) -> None:
        """Initialize the agent service with storage service.
        
        Args:
            agent_storage: Agent storage service for Valkey/Redis
        """
        self.agent_storage = agent_storage
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Retrieve all agents from storage.
        
        Returns:
            List of agent dictionaries
        """
        return self.agent_storage.list_agents()
    
    def get_agent_by_id(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific agent by ID.
        
        Args:
            agent_id: The unique identifier of the agent
            
        Returns:
            Agent entity if found, None otherwise
        """
        return self.agent_storage.get_agent(agent_id)
    
    def create_agent(self, agent_data: AgentCreate) -> Dict[str, Any]:
        """Create a new agent in storage.
        
        Args:
            agent_data: Validated agent data from request
            
        Returns:
            The created Agent entity
        """
        return self.agent_storage.create_agent(agent_data.dict())
    
    def generate_diverse_agents(self, count: int = 30) -> List[Dict[str, Any]]:
        """Generate diverse agent profiles matching frontend structure.
        
        Args:
            count: Number of agents to generate (default: 30)
            
        Returns:
            List of generated Agent entities
        """
        agents = []
        
        # Frontend-compatible data
        first_names = {
            "male": ["James", "Robert", "Michael", "David", "William", "Richard", "Thomas", "Christopher", "Daniel", "Matthew"],
            "female": ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
        }
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        occupations = ["Software Developer", "Product Manager", "UX Designer", "Marketing Specialist", "Data Analyst", "Entrepreneur", "Consultant", "Teacher", "Engineer", "Healthcare Worker"]
        life_views = ["progressive", "moderate", "conservative"]
        innovation_attitudes = ["conservative", "moderate", "innovator"]
        male_emojis = ["👨", "👨‍💼", "👨‍💻", "👨‍🔬", "👨‍🎓", "👨‍🏫", "👨‍⚕️", "👨‍🌾", "👨‍🍳", "👨‍🎨"]
        female_emojis = ["👩", "👩‍💼", "👩‍💻", "👩‍🔬", "👩‍🎓", "👩‍🏫", "👩‍⚕️", "👩‍🌾", "👩‍🍳", "👩‍🎨"]
        avatar_colors = ["bg-blue-500", "bg-purple-500", "bg-pink-500", "bg-indigo-500", "bg-cyan-500", "bg-teal-500", "bg-emerald-500", "bg-lime-500", "bg-amber-500", "bg-orange-500"]
        
        for i in range(count):
            gender = random.choice(["male", "female"])
            first_name = random.choice(first_names[gender])
            last_name = random.choice(last_names)
            
            agent_data = {
                "name": f"{first_name} {last_name}",
                "age": random.randint(22, 65),
                "gender": gender,
                "occupation": random.choice(occupations),
                "life_views": random.choice(life_views),
                "innovation_attitude": random.choice(innovation_attitudes),
                "risk_tolerance": random.randint(1, 10),
                "gullibility": random.randint(1, 10),
                "emoji": random.choice(male_emojis if gender == "male" else female_emojis),
                "avatar_color": random.choice(avatar_colors),
                "status": "pending",
                
                # Legacy fields for backward compatibility
                "interests": json.dumps(["Technology", "Design"]),
                "tech_savviness": random.randint(3, 10),
                "budget_range": random.choice(["$0-100", "$100-500", "$500-1000", "$1000+"]),
                "location": "Remote"
            }
            
            agent = Agent(**agent_data)
            self.db.add(agent)
            agents.append(agent)
        
        self.db.commit()
        return agents
    
    def delete_agent(self, agent_id: int) -> bool:
        """Delete agent"""
        agent = self.get_agent_by_id(agent_id)
        if agent:
            self.db.delete(agent)
            self.db.commit()
            return True
        return False
    
    def start_review_process(self, agent_id: int) -> bool:
        """Start review process for an agent"""
        agent = self.get_agent_by_id(agent_id)
        if agent and agent.status == "pending":
            agent.status = "reviewing"
            self.db.commit()
            return True
        return False
    
    def complete_review(self, agent_id: int) -> bool:
        """Complete review for an agent with generated ratings"""
        agent = self.get_agent_by_id(agent_id)
        if agent and agent.status == "reviewing":
            # Generate realistic ratings
            base_rating = random.randint(40, 95)
            variance = 15
            
            agent.overall_rating = max(0, min(100, base_rating + random.randint(-variance, variance)))
            agent.clarity_rating = max(0, min(100, base_rating + random.randint(-variance, variance)))
            agent.ux_rating = max(0, min(100, base_rating + random.randint(-variance, variance)))
            agent.value_proposition_rating = max(0, min(100, base_rating + random.randint(-variance, variance)))
            
            reviews = [
                "Clear and concise presentation. The value proposition is immediately apparent.",
                "Well-designed interface with intuitive navigation. Could improve loading times.",
                "Strong visual hierarchy makes it easy to understand the product offering.",
                "The messaging resonates well with the target audience.",
                "Some sections feel cluttered, but overall a solid user experience.",
                "Excellent use of whitespace and typography. Very professional.",
                "The call-to-action could be more prominent, but the design is clean.",
                "Information architecture is well thought out. Easy to find what I need.",
                "Modern design that inspires confidence. The brand identity is strong.",
                "Good balance between aesthetics and functionality."
            ]
            
            agent.review_text = random.choice(reviews)
            agent.status = "completed"
            self.db.commit()
            return True
        return False

class UserProfile(BaseModel):
    """AI-generated user profile for autonomous agent reviews.
    
    Represents a virtual user with realistic demographic and
    psychological characteristics for product evaluation.
    """
    name: str
    age: int
    gender: str
    occupation: str
    marital_status: str
    life_views: str
    risk_propensity: int
    trustfulness: int
    attitude_to_innovation: str
    emoji: str

class ReviewResult(BaseModel):
    """Review result from AI agent evaluation.
    
    Contains the structured output of an autonomous agent's
    review of a website or product.
    """
    review_text: str = Field(max_length=300, description="Review text limited to 300 characters")
    clarity_rating: int
    ux_rating: int
    value_proposition_rating: int
    profile: Optional[UserProfile] = None

class AIAgentService:
    """Service for AI-powered agent generation and review execution.
    
    Uses Anthropic's Claude AI to generate realistic user profiles
    and execute autonomous agent reviews of websites.
    """
    
    def __init__(self, anthropic_api_key: str, model_speed: str = "fast") -> None:
        """Initialize with Anthropic API key and model speed preference.
        
        Args:
            anthropic_api_key: API key for Anthropic Claude service
            model_speed: Model speed preference ("fast", "balanced", "quality")
        """
        from app.config import settings
        self.api_key = anthropic_api_key
        
        # Use configurable model from settings
        self.model = settings.claude_model
        self.review_model = settings.claude_review_model
        
        # Profile generator agent - using selected model
        self.profile_agent = PydanticAgent(
            self.model,
            output_type=List[UserProfile],
            system_prompt=get_profile_system_prompt()
        )
    
    async def generate_ai_profiles(self, count: int = 30, target_audience: Optional[Dict] = None) -> List[UserProfile]:
        """Generate profiles using AI based on target audience or random"""
        try:
            if target_audience:
                logger.info(f"🎯 Generating {count} targeted AI profiles for audience: {target_audience.get('occupation', 'N/A')}")
                logger.info(f"📊 Target specs - Age: {target_audience.get('ageRange', [22, 65])}, Gender: {target_audience.get('gender', 'any')}")
                prompt = get_targeted_profile_prompt(count, target_audience)
            else:
                logger.info(f"🎲 Generating {count} random diverse AI profiles...")
                prompt = get_random_profile_prompt(count)
            
            logger.info(f"📝 Sending profile generation request to Claude AI...")
            result = await self.profile_agent.run(prompt)
            profiles = result.output
            
            logger.info(f"✅ Successfully generated {len(profiles)} unique AI profiles")
            
            # Log sample profiles for debugging
            if profiles:
                sample_count = min(3, len(profiles))
                logger.info(f"📋 Sample profiles generated:")
                for i, profile in enumerate(profiles[:sample_count]):
                    logger.info(f"   {i+1}. {profile.name} ({profile.age}, {profile.occupation}) - Risk: {profile.risk_propensity}/10, Trust: {profile.trustfulness}/10")
            
            return profiles
            
        except Exception as e:
            logger.error(f"💥 Error generating AI profiles: {e}")
            logger.error(f"📍 Profile generation failed for count={count}, target_audience={target_audience}")
            raise
    
    async def execute_agent_review(self, profile: UserProfile, site_content: str) -> ReviewResult:
        """Execute single agent review using centralized prompt template"""
        
        logger.info(f"👤 Starting review for {profile.name} ({profile.age}, {profile.occupation})")
        logger.info(f"🧠 Personality traits - Risk: {profile.risk_propensity}/10, Trust: {profile.trustfulness}/10, Innovation: {profile.attitude_to_innovation}")
        
        # Optimize content length for faster processing (truncate if too long)
        max_content_length = 8000  # Reduced from default for speed
        if len(site_content) > max_content_length:
            site_content = site_content[:max_content_length] + "...[truncated]"
            logger.info(f"📄 Content truncated to {max_content_length} chars for faster processing")
        
        # Get prompt from centralized prompts module
        agent_prompt = get_website_review_prompt(profile.dict(), site_content)
        
        # Create agent with system prompt from centralized prompts - using review-specific model
        review_agent = PydanticAgent(
            self.review_model,
            output_type=ReviewResult,
            system_prompt=get_review_system_prompt()
        )
        
        try:
            logger.info(f"🤖 {profile.name} is analyzing website content ({len(site_content)} chars)...")
            result = await review_agent.run(agent_prompt)
            review_result = result.output
            
            # Attach profile to review result
            review_result.profile = profile
            
            # Log detailed review results
            logger.info(f"✅ {profile.name} completed review:")
            logger.info(f"   📝 Review: {review_result.review_text[:100]}{'...' if len(review_result.review_text) > 100 else ''}")
            logger.info(f"   📊 Ratings - Clarity: {review_result.clarity_rating}/100, UX: {review_result.ux_rating}/100, Value: {review_result.value_proposition_rating}/100")
            
            return review_result
            
        except Exception as e:
            logger.error(f"💥 Error with {profile.name}'s review: {e}")
            logger.error(f"📍 Review failed for {profile.name} - {profile.occupation} ({profile.age} years old)")
            raise
    
    async def launch_all_agents(self, site_content: str, target_audience: Optional[Dict] = None, on_agent_complete = None) -> List[Dict[str, Any]]:
        """Generate AI profiles and execute all 30 agent reviews"""
        try:
            logger.info("=" * 80)
            logger.info("🚀 LAUNCHING AI AGENT EVALUATION SYSTEM")
            logger.info("=" * 80)
            
            # Generate fresh AI profiles (reduced count for speed)
            logger.info("📋 PHASE 1: Profile Generation")
            profile_count = 20  # Reduced from 30 to 20 for faster execution
            profiles = await self.generate_ai_profiles(profile_count, target_audience)
            
            # Launch all agents with staggered execution for progressive loading
            logger.info("\n🤖 PHASE 2: Progressive Agent Reviews")
            logger.info(f"🔄 Launching {len(profiles)} autonomous AI agents progressively...")
            logger.info(f"📄 Website content length: {len(site_content)} characters")
            
            import time
            start_time = time.time()
            
            # Use semaphore to limit concurrent requests (avoid rate limits)
            # Use configurable concurrency for optimal performance
            from app.config import settings
            semaphore = asyncio.Semaphore(settings.max_concurrent_agents)
            
            # Add connection pooling optimization with session reuse
            import aiohttp
            connector = aiohttp.TCPConnector(
                limit=settings.max_concurrent_agents * 3,  # Increased pool size
                limit_per_host=settings.max_concurrent_agents * 2,  # More connections per host
                ttl_dns_cache=300,  # DNS caching
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            async def execute_with_semaphore(profile):
                async with semaphore:
                    return await self.execute_agent_review(profile, site_content)
            
            tasks = [
                execute_with_semaphore(profile)
                for profile in profiles
            ]
            
            logger.info("⏳ Processing agents as they complete...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Performance metrics
            successful_reviews = len([r for r in results if not isinstance(r, Exception)])
            reviews_per_second = successful_reviews / duration if duration > 0 else 0
            logger.info(f"⚡ PERFORMANCE METRICS:")
            logger.info(f"   🕐 Total duration: {duration:.2f} seconds")
            logger.info(f"   ✅ Successful reviews: {successful_reviews}/{len(profiles)}")
            logger.info(f"   🚀 Reviews per second: {reviews_per_second:.2f}")
            logger.info(f"   🔄 Concurrency level: {settings.max_concurrent_agents}")
            
            # Process results with progressive updates
            logger.info("\n📊 PHASE 3: Progressive Results Processing")
            agent_results = []
            failed_agents = []
            
            # Initialize all agents as pending first
            pending_agents = []
            for i, profile in enumerate(profiles):
                pending_agents.append({
                    "id": i + 1,
                    "name": profile.name,
                    "age": profile.age,
                    "gender": profile.gender.lower(),
                    "occupation": profile.occupation,
                    "lifeViews": profile.life_views.lower(),
                    "innovationAttitude": profile.attitude_to_innovation.lower(),
                    "riskTolerance": profile.risk_propensity,
                    "gullibility": 10 - profile.trustfulness,
                    "emoji": profile.emoji,
                    "status": "reviewing",  # Start as reviewing
                    "ratings": None,
                    "review": None
                })
            
            # Initialize incremental store with pending agents if callback provided
            if on_agent_complete:
                logger.info("🔄 Initializing incremental store with pending agents...")
                # Call the callback with a special "initialize" signal
                on_agent_complete({"action": "initialize", "agents": pending_agents})
            
            # Process results (no persistent storage)
            for i, (profile, result) in enumerate(zip(profiles, results)):
                if isinstance(result, Exception):
                    logger.error(f"❌ {profile.name} failed: {result}")
                    failed_agents.append(profile.name)
                    # Update failed agent status
                    pending_agents[i]["status"] = "pending"  # Reset to pending on failure
                    continue
                
                # Create completed agent data (memory only)
                completed_agent = {
                    "id": i + 1,
                    "name": profile.name,
                    "age": profile.age,
                    "gender": profile.gender.lower(),
                    "occupation": profile.occupation,
                    "lifeViews": profile.life_views.lower(),
                    "innovationAttitude": profile.attitude_to_innovation.lower(),
                    "riskTolerance": profile.risk_propensity,
                    "gullibility": 10 - profile.trustfulness,
                    "emoji": profile.emoji,
                    "status": "completed",
                    "ratings": {
                        "overall": round((result.clarity_rating + result.ux_rating + result.value_proposition_rating) / 3),
                        "clarity": result.clarity_rating,
                        "ux": result.ux_rating,
                        "valueProposition": result.value_proposition_rating
                    },
                    "review": result.review_text
                }
                
                agent_results.append(completed_agent)
                pending_agents[i] = completed_agent
                
                # Call progress callback if provided
                if on_agent_complete:
                    on_agent_complete(completed_agent)
                
                logger.info(f"✅ {i+1}/{len(profiles)} - {profile.name} completed review")
            
            logger.info(f"✅ Processed {len(agent_results)} ephemeral evaluations with progressive loading")
            
            # Log comprehensive statistics
            logger.info("=" * 80)
            logger.info("📈 AI AGENT EVALUATION COMPLETE - STATISTICS")
            logger.info("=" * 80)
            logger.info(f"⏱️  Total execution time: {duration:.2f} seconds")
            logger.info(f"✅ Successful reviews: {len(agent_results)}/{len(profiles)}")
            logger.info(f"❌ Failed reviews: {len(failed_agents)}")
            
            if failed_agents:
                logger.warning(f"💔 Failed agents: {', '.join(failed_agents)}")
            
            if agent_results:
                # Calculate rating statistics
                clarity_ratings = [r['ratings']['clarity'] for r in agent_results]
                ux_ratings = [r['ratings']['ux'] for r in agent_results]  
                value_ratings = [r['ratings']['valueProposition'] for r in agent_results]
                
                avg_clarity = sum(clarity_ratings) / len(clarity_ratings)
                avg_ux = sum(ux_ratings) / len(ux_ratings)
                avg_value = sum(value_ratings) / len(value_ratings)
                
                logger.info(f"📊 Average ratings:")
                logger.info(f"   🔍 Clarity: {avg_clarity:.1f}/100")
                logger.info(f"   🎨 UX/Design: {avg_ux:.1f}/100") 
                logger.info(f"   💎 Value Proposition: {avg_value:.1f}/100")
                logger.info(f"   🌟 Overall Average: {(avg_clarity + avg_ux + avg_value)/3:.1f}/100")
                
                # Log sample reviews
                logger.info(f"📝 Sample reviews:")
                sample_count = min(3, len(agent_results))
                for i, result in enumerate(agent_results[:sample_count]):
                    logger.info(f"   {i+1}. {result['name']}: \"{result['review'][:80]}{'...' if len(result['review']) > 80 else ''}\"")
            
            logger.info("=" * 80)
            
            # Debug: Log final agent count and status breakdown
            completed_count = len([a for a in pending_agents if a.get("status") == "completed"])
            reviewing_count = len([a for a in pending_agents if a.get("status") == "reviewing"])
            pending_count = len([a for a in pending_agents if a.get("status") == "pending"])
            logger.info(f"🎯 FINAL RESULT: Returning {len(pending_agents)} total agents")
            logger.info(f"   ✅ Completed: {completed_count}")
            logger.info(f"   🔄 Reviewing: {reviewing_count}")
            logger.info(f"   ⏳ Pending: {pending_count}")
            
            # Return combined list including ALL agents (completed + pending) for frontend
            return pending_agents
            
        except Exception as e:
            logger.error(f"💥 CRITICAL ERROR launching AI agents: {e}")
            logger.error(f"📍 Launch failed for target_audience={target_audience}")
            raise

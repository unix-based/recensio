"""
Link Verification Service - Simplified URL validation and content extraction using Claude AI
"""

import re
import httpx
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse, urlunparse
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass
import os
from textwrap import dedent
from app.logger import get_module_logger
from app.config import settings
from app.prompts import get_suitability_system_prompt, get_link_analyzer_system_prompt, get_link_analysis_prompt

logger = get_module_logger(__name__)

class LinkValidationResult(BaseModel):
    """Result of link validation"""
    is_valid: bool
    is_accessible: bool = False
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    normalized_url: Optional[str] = None

class UsefulLink(BaseModel):
    """Model for AI-identified useful links"""
    url: str = Field(description="The URL of the useful page")
    title: str = Field(description="The title or description of what this page contains")
    reason: str = Field(description="Why this link is useful for understanding the project")
    priority: int = Field(description="Priority from 1-10 where 10 is most important")

class UsefulLinksResponse(BaseModel):
    """Response from AI for useful links identification"""
    useful_links: List[UsefulLink] = Field(description="List of useful links for the project")

@dataclass
class PageContent:
    """Container for extracted page content"""
    url: str
    html: str
    text: str
    title: str
    meta_description: str
    links: List[str]

class SuitabilityResult(BaseModel):
    """Result of site suitability check"""
    is_suitable: bool
    confidence: float = Field(ge=0.0, le=1.0)
    site_type: str
    reasons: List[str]
    content_quality: str  # "excellent", "good", "poor", "insufficient"

@dataclass
class SiteSnapshot:
    """Complete snapshot of a website"""
    url: str
    main_page: PageContent
    internal_pages: List[PageContent]
    useful_links: List[UsefulLink]
    complete_html: str  # Combined HTML of all pages
    complete_text: str  # Combined text of all pages
    total_pages: int
    extraction_timestamp: str

class LinkVerificationService:
    """Service for comprehensive link verification and content extraction using Claude AI"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(settings.link_verification_timeout)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        # Initialize AI agents - API key is required
        if not settings.anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables. This is required for secure link verification.")
            raise ValueError("ANTHROPIC_API_KEY is required but not found in environment variables")
        
        os.environ['ANTHROPIC_API_KEY'] = settings.anthropic_api_key
        
        self.suitability_agent = Agent(
            settings.claude_model,
            output_type=SuitabilityResult,
            system_prompt=get_suitability_system_prompt()
        )
        
        self.link_analyzer_agent = Agent(
            settings.claude_model,
            output_type=UsefulLinksResponse,
            system_prompt=get_link_analyzer_system_prompt()
        )

    def validate_url_syntax(self, url: str) -> Tuple[bool, str]:
        """Validate URL syntax and normalize it"""
        try:
            url = url.strip()
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Parse URL to validate structure
            parsed = urlparse(url)
            
            if not parsed.netloc:
                return False, "Invalid URL: No domain found"
            
            # Basic domain validation
            domain = parsed.netloc.split(':')[0]
            # Check for valid domain format with proper TLD
            domain_parts = domain.split('.')
            if len(domain_parts) < 2:
                return False, "Invalid URL: Domain must have at least one dot"
            
            # Check each part of domain
            for part in domain_parts:
                if not part or len(part) < 1:
                    return False, "Invalid URL: Empty domain part"
                if not re.match(r'^[a-zA-Z0-9-]+$', part):
                    return False, "Invalid URL: Invalid characters in domain"
            
            # Check TLD (last part) is at least 2 characters and alphabetic
            tld = domain_parts[-1]
            if len(tld) < 2 or not re.match(r'^[a-zA-Z]{2,}$', tld):
                return False, "Invalid URL: Invalid top-level domain"
            
            # Check domain parts aren't too short (reject things like 'h.ho')
            if any(len(part) == 1 for part in domain_parts[:-1]) and len(tld) == 2:
                return False, "Invalid URL: Domain parts too short"
            
            # Reconstruct clean URL
            clean_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path or '/',
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            return True, clean_url
        except Exception as e:
            return False, f"URL parsing error: {str(e)}"

    async def check_url_accessibility(self, url: str) -> LinkValidationResult:
        """Check if URL is accessible"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.head(url)
                
                # If HEAD fails, try GET
                if response.status_code == 405:
                    response = await client.get(url)
                
                return LinkValidationResult(
                    is_valid=True,
                    is_accessible=response.status_code == 200,
                    status_code=response.status_code,
                    normalized_url=str(response.url),
                    error_message=None if response.status_code == 200 else f"HTTP {response.status_code}"
                )
        except httpx.TimeoutException as e:
            return LinkValidationResult(
                is_valid=False,
                is_accessible=False,
                error_message=f"Request timeout: {str(e)}"
            )
        except httpx.ConnectError as e:
            return LinkValidationResult(
                is_valid=False,
                is_accessible=False,
                error_message=f"Connection failed: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            return LinkValidationResult(
                is_valid=False,
                is_accessible=False,
                status_code=e.response.status_code,
                error_message=f"HTTP error: {e.response.status_code}"
            )
        except Exception as e:
            return LinkValidationResult(
                is_valid=False,
                is_accessible=False,
                error_message=f"Network error: {str(e)}"
            )

    async def extract_page_content(self, url: str) -> Optional[PageContent]:
        """Extract full page content including HTML, text, and links"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return None
                
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract components
                text_content = soup.get_text(separator=' ', strip=True)
                title = soup.title.string.strip() if soup.title and soup.title.string else ""
                
                meta_tag = soup.find("meta", attrs={"name": "description"})
                meta_desc = meta_tag.get("content", "").strip() if meta_tag else ""
                
                links = list(set([urljoin(url, link['href']) for link in soup.find_all('a', href=True)]))
                
                return PageContent(
                    url=url,
                    html=html_content,
                    text=text_content,
                    title=title,
                    meta_description=meta_desc,
                    links=links
                )
        except Exception:
            return None

    def filter_internal_links(self, base_url: str, links: List[str]) -> List[str]:
        """Filter links to only include internal pages on same domain"""
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc.lower()
        
        internal_links = []
        for link in links:
            try:
                parsed_link = urlparse(link)
                link_domain = parsed_link.netloc.lower()
                
                # Include only same domain links
                if not link_domain or link_domain == base_domain:
                    # Normalize the link
                    if not link_domain:
                        # Relative link - make absolute
                        normalized_link = urljoin(base_url, link)
                    else:
                        normalized_link = link
                    
                    # Remove fragments and clean up
                    parsed_normalized = urlparse(normalized_link)
                    clean_link = urlunparse((
                        parsed_normalized.scheme,
                        parsed_normalized.netloc,
                        parsed_normalized.path,
                        parsed_normalized.params,
                        parsed_normalized.query,
                        ''  # Remove fragment
                    ))
                    
                    # Avoid duplicates and exclude certain patterns
                    if (clean_link not in internal_links and 
                        clean_link != base_url and
                        not any(pattern in clean_link.lower() for pattern in [
                            'javascript:', 'mailto:', 'tel:', '#', 
                            'privacy', 'terms', 'legal', 'cookie'
                        ])):
                        internal_links.append(clean_link)
                        
            except Exception:
                continue
                
        return list(set(internal_links))  # Remove duplicates

    async def analyze_useful_links(self, base_url: str, all_links: List[str]) -> List[UsefulLink]:
        """Use AI to analyze and filter useful links"""
        internal_links = self.filter_internal_links(base_url, all_links)
        
        if not internal_links:
            return []
            
        # Prepare links for AI analysis
        links_text = "\n".join([f"- {link}" for link in internal_links[:50]])  # Limit for AI processing
        
        prompt = get_link_analysis_prompt(base_url, links_text)
        
        try:
            result = await self.link_analyzer_agent.run(prompt)
            return result.output.useful_links
        except Exception as e:
            logger.error(f"Error analyzing links with AI: {str(e)}")
            return []

    async def scrape_multiple_pages(self, useful_links: List[UsefulLink], max_pages: int = 10) -> List[PageContent]:
        """Scrape content from multiple useful pages concurrently"""
        if not useful_links:
            return []
            
        # Sort by priority and take top pages
        sorted_links = sorted(useful_links, key=lambda x: x.priority, reverse=True)
        top_links = sorted_links[:max_pages]
        
        # Scrape pages concurrently
        tasks = [self.extract_page_content(link.url) for link in top_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failures and return successful extractions
        successful_pages = []
        for i, result in enumerate(results):
            if isinstance(result, PageContent):
                successful_pages.append(result)
                logger.info(f"Successfully scraped: {top_links[i].url}")
            else:
                logger.warning(f"Failed to scrape: {top_links[i].url}")
                
        return successful_pages

    async def create_complete_site_snapshot(self, url: str) -> Optional[SiteSnapshot]:
        """Create a complete snapshot of the entire website"""
        logger.info(f"Creating complete site snapshot for {url}")
        
        try:
            # Step 1: Extract main page content
            main_content = await self.extract_page_content(url)
            if not main_content:
                logger.error(f"Could not extract main page content from {url}")
                return None
            
            # Step 2: Analyze and identify useful links
            logger.info("Analyzing links with AI to identify useful pages...")
            useful_links = await self.analyze_useful_links(url, main_content.links)
            logger.info(f"AI identified {len(useful_links)} useful links")
            
            # Step 3: Scrape all useful pages
            logger.info("Scraping additional pages...")
            internal_pages = await self.scrape_multiple_pages(useful_links, max_pages=15)
            logger.info(f"Successfully scraped {len(internal_pages)} additional pages")
            
            # Step 4: Combine all content
            all_pages = [main_content] + internal_pages
            combined_html = "\n\n<!-- PAGE SEPARATOR -->\n\n".join([page.html for page in all_pages])
            combined_text = "\n\n=== PAGE SEPARATOR ===\n\n".join([page.text for page in all_pages])
            
            # Create the complete snapshot
            snapshot = SiteSnapshot(
                url=url,
                main_page=main_content,
                internal_pages=internal_pages,
                useful_links=useful_links,
                complete_html=combined_html,
                complete_text=combined_text,
                total_pages=len(all_pages),
                extraction_timestamp=asyncio.get_event_loop().time().__str__()
            )
            
            logger.success(f"Complete site snapshot created for {url}")
            logger.info(f"Total pages: {snapshot.total_pages}, "
                       f"Total content length: {len(snapshot.complete_text)} chars, "
                       f"Useful links found: {len(snapshot.useful_links)}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error creating site snapshot: {str(e)}")
            return None

    async def check_site_suitability_with_claude(self, main_content: PageContent) -> SuitabilityResult:
        """Use Claude AI to check if the site is suitable for evaluation - AI IS REQUIRED"""
        logger.info(f"Checking site suitability with Claude AI for {main_content.url}")
        logger.debug("Analyzing main page content only (optimized for speed)")
        
        combined_content = dedent(f"""
            Website: {main_content.url}
            Title: {main_content.title}
            Meta Description: {main_content.meta_description}
            Full Content: {main_content.text[:3000]}
            Available Links: {len(main_content.links)} links found
            """).strip()
        
        logger.debug("Sending suitability analysis request to Claude AI")
        result = await self.suitability_agent.run(combined_content)
        suitability = result.output
        
        logger.success(f"Claude AI suitability check completed for {main_content.url}")
        logger.info(f"Site suitability: {'✅ SUITABLE' if suitability.is_suitable else '❌ NOT SUITABLE'} "
                   f"(confidence: {suitability.confidence:.2f}, type: {suitability.site_type})")
        
        for reason in suitability.reasons:
            logger.debug(f"Suitability reason: {reason}")
        
        return suitability


    async def comprehensive_verification(self, url: str, extract_full_site: bool = True) -> Dict[str, Any]:
        """Complete verification pipeline using Claude AI with optional full site extraction"""
        logger.info(f"🔍 Starting comprehensive verification for: {url}")
        logger.info(f"📋 Verification mode: {'Full site extraction' if extract_full_site else 'Main page only'}")
        
        result = {"original_url": url, "is_valid": False, "is_accessible": False, "is_suitable": False, "errors": []}
        
        try:
            # Step 1: Syntax validation
            logger.info(f"🔗 Step 1: Validating URL syntax for {url}")
            is_valid_syntax, normalized_url = self.validate_url_syntax(url)
            if not is_valid_syntax:
                logger.error(f"❌ URL syntax validation failed: {normalized_url}")
                result["errors"].append(normalized_url)
                return result
            
            logger.info(f"✅ URL syntax validation passed: {normalized_url}")
            result["normalized_url"] = normalized_url
            result["is_valid"] = True
            
            # Step 2: Accessibility check
            logger.info(f"🌐 Step 2: Checking URL accessibility for {normalized_url}")
            accessibility = await self.check_url_accessibility(normalized_url)
            result["is_accessible"] = accessibility.is_accessible
            result["status_code"] = accessibility.status_code
            
            if not accessibility.is_accessible:
                error_msg = accessibility.error_message or "Site not accessible"
                logger.error(f"❌ URL accessibility check failed: {error_msg}")
                result["errors"].append(error_msg)
                return result
            
            logger.info(f"✅ URL accessibility check passed: HTTP {accessibility.status_code}")
            
            # Step 3: Extract main page content
            logger.info(f"📄 Step 3: Extracting main page content from {normalized_url}")
            main_content = await self.extract_page_content(normalized_url)
            if not main_content:
                logger.error(f"❌ Failed to extract main page content from {normalized_url}")
                result["errors"].append("Could not extract page content")
                return result
            
            logger.info(f"✅ Main page content extracted: {len(main_content.text)} characters, title: '{main_content.title}'")
            
            # Step 4: Check suitability using Claude AI (main page only for speed)
            logger.info(f"🤖 Step 4: Checking site suitability with Claude AI for {normalized_url}")
            suitability = await self.check_site_suitability_with_claude(main_content)
            result["is_suitable"] = suitability.is_suitable
            result["suitability"] = suitability.dict()
            
            # FAIL if site is not suitable
            if not suitability.is_suitable:
                error_msg = f"Site rejected by AI: {suitability.site_type} - {', '.join(suitability.reasons)}"
                logger.error(f"❌ Site verification FAILED for {url}: {error_msg}")
                result["errors"].append(error_msg)
                return result
            
            logger.info(f"✅ Site suitability check passed: {suitability.site_type} (confidence: {suitability.confidence:.2f})")
            
            # Automatic: Extract full site after successful verification
            if extract_full_site:
                logger.info(f"🌐 Step 5: Extracting complete site after successful verification...")
                site_snapshot = await self.create_complete_site_snapshot(normalized_url)
                
                if site_snapshot:
                    logger.info(f"✅ Complete site extraction successful: {site_snapshot.total_pages} pages, {len(site_snapshot.complete_text)} characters")
                    result["site_snapshot"] = {
                        "url": site_snapshot.url,
                        "total_pages": site_snapshot.total_pages,
                        "useful_links_count": len(site_snapshot.useful_links),
                        "combined_text_length": len(site_snapshot.complete_text),
                        "combined_html_length": len(site_snapshot.complete_html),
                        "extraction_timestamp": site_snapshot.extraction_timestamp
                    }
                    
                    result["useful_links"] = [
                        {
                            "url": link.url,
                            "title": link.title,
                            "reason": link.reason,
                            "priority": link.priority
                        }
                        for link in site_snapshot.useful_links
                    ]
                    
                    result["complete_site_content"] = {
                        "combined_text": site_snapshot.complete_text,
                        "combined_html": site_snapshot.complete_html,
                        "main_page": {
                            "url": site_snapshot.main_page.url,
                            "title": site_snapshot.main_page.title,
                            "text": site_snapshot.main_page.text,
                            "html": site_snapshot.main_page.html,
                            "meta_description": site_snapshot.main_page.meta_description,
                            "links": site_snapshot.main_page.links
                        },
                        "internal_pages": [
                            {
                                "url": page.url,
                                "title": page.title,
                                "text": page.text,
                                "html": page.html,
                                "meta_description": page.meta_description,
                                "links": page.links
                            }
                            for page in site_snapshot.internal_pages
                        ]
                    }
                    
                    result["pages_extracted"] = site_snapshot.total_pages
                    result["total_content"] = {
                        "combined_text_length": len(site_snapshot.complete_text),
                        "combined_html_length": len(site_snapshot.complete_html),
                        "pages": [{"url": site_snapshot.main_page.url, "title": site_snapshot.main_page.title, "content_length": len(site_snapshot.main_page.text)}] +
                                [{"url": page.url, "title": page.title, "content_length": len(page.text)} for page in site_snapshot.internal_pages]
                    }
                    
                    logger.success(f"🎉 Complete site extraction completed for {url}")
                    logger.info(f"Total pages extracted: {site_snapshot.total_pages}, "
                               f"Total content: {len(site_snapshot.complete_text)} chars, "
                               f"Useful links: {len(site_snapshot.useful_links)}")
                else:
                    # Fall back to main page only
                    logger.warning("❌ Full site extraction failed, falling back to main page only")
                    extract_full_site = False
            
            # If not extracting full site, use main page only
            if not extract_full_site:
                logger.info(f"📄 Using main page only mode: {len(main_content.text)} characters")
                result["main_content"] = {
                    "title": main_content.title,
                    "meta_description": main_content.meta_description,
                    "text_length": len(main_content.text),
                    "links_found": len(main_content.links)
                }
                result["pages_extracted"] = 1
                
                result["total_content"] = {
                    "combined_text_length": len(main_content.text),
                    "combined_html_length": len(main_content.html),
                    "pages": [{"url": main_content.url, "title": main_content.title, "content_length": len(main_content.text)}]
                }
                
                result["full_page_contents"] = [
                    {
                        "url": main_content.url,
                        "title": main_content.title,
                        "html": main_content.html,
                        "text": main_content.text,
                        "meta_description": main_content.meta_description
                    }
                ]
                
                logger.success(f"🎉 Fast verification completed for {url}")
                logger.info(f"Final results: Valid: {result['is_valid']}, Accessible: {result['is_accessible']}, "
                           f"Suitable: {result['is_suitable']}, Content: {len(main_content.text)} chars")
            
            # Final verification summary
            logger.info(f"🎯 VERIFICATION COMPLETE for {url}")
            logger.info(f"   ✅ Valid: {result['is_valid']}")
            logger.info(f"   ✅ Accessible: {result['is_accessible']}")
            logger.info(f"   ✅ Suitable: {result['is_suitable']}")
            logger.info(f"   📄 Pages extracted: {result.get('pages_extracted', 0)}")
            logger.info(f"   📊 Content length: {result.get('total_content', {}).get('combined_text_length', 0)} characters")
            
        except Exception as e:
            logger.error(f"💥 Unexpected error during comprehensive verification of {url}: {str(e)}")
            logger.error(f"📍 Error type: {type(e).__name__}")
            import traceback
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            result["errors"].append(f"Unexpected error: {str(e)}")
        
        return result
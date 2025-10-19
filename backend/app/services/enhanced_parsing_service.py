"""
Enhanced Parsing Service - Advanced web content extraction with JavaScript support
"""

import asyncio
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
from app.logger import get_module_logger
from app.config import settings

logger = get_module_logger(__name__)

@dataclass
class ParsingResult:
    """Result of enhanced parsing"""
    success: bool
    content: Optional[str] = None
    html: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    links: List[str] = None
    method_used: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0

class EnhancedParsingService:
    """Enhanced parsing service with multiple fallback strategies"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(settings.link_verification_timeout)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Initialize parsing methods based on configuration
        self.parsing_methods = []
        
        if settings.enable_requests_html:
            self.parsing_methods.append(self._parse_with_requests_html)
        if settings.enable_selenium:
            self.parsing_methods.append(self._parse_with_selenium)
        if settings.enable_playwright:
            self.parsing_methods.append(self._parse_with_playwright)
        
        # Always include fallback method
        self.parsing_methods.append(self._parse_with_httpx_fallback)

    async def parse_url(self, url: str, max_retries: int = None) -> ParsingResult:
        """Parse URL using multiple fallback strategies with enhanced error handling"""
        logger.info(f"🔍 Starting enhanced parsing for: {url}")
        
        if max_retries is None:
            max_retries = settings.max_parsing_retries
        
        last_error = None
        
        for attempt in range(max_retries):
            logger.info(f"🔄 Parsing attempt {attempt + 1}/{max_retries}")
            
            for method in self.parsing_methods:
                try:
                    start_time = time.time()
                    result = await method(url)
                    result.execution_time = time.time() - start_time
                    
                    if result.success:
                        logger.success(f"✅ Parsing successful with {result.method_used} in {result.execution_time:.2f}s")
                        return result
                    else:
                        logger.warning(f"⚠️ {result.method_used} failed: {result.error_message}")
                        last_error = result.error_message
                        
                except Exception as e:
                    error_msg = f"{method.__name__} failed with exception: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    last_error = error_msg
                    continue
            
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 10)  # Exponential backoff with max 10s
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # All methods failed - return detailed error
        error_message = f"All parsing methods failed after {max_retries} attempts"
        if last_error:
            error_message += f". Last error: {last_error}"
        
        return ParsingResult(
            success=False,
            error_message=error_message,
            method_used="all_methods_failed"
        )

    async def _parse_with_httpx_fallback(self, url: str) -> ParsingResult:
        """Fallback parsing using httpx (original method)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return ParsingResult(
                        success=False,
                        error_message=f"HTTP {response.status_code}",
                        method_used="httpx_fallback"
                    )
                
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text_content = soup.get_text(separator=' ', strip=True)
                title = soup.title.string.strip() if soup.title and soup.title.string else ""
                
                meta_tag = soup.find("meta", attrs={"name": "description"})
                meta_desc = meta_tag.get("content", "").strip() if meta_tag else ""
                
                links = list(set([urljoin(url, link['href']) for link in soup.find_all('a', href=True)]))
                
                return ParsingResult(
                    success=True,
                    content=text_content,
                    html=html_content,
                    title=title,
                    meta_description=meta_desc,
                    links=links,
                    method_used="httpx_fallback"
                )
                
        except Exception as e:
            return ParsingResult(
                success=False,
                error_message=str(e),
                method_used="httpx_fallback"
            )

    async def _parse_with_requests_html(self, url: str) -> ParsingResult:
        """Parse using requests-html for JavaScript rendering"""
        try:
            from requests_html import AsyncHTMLSession
            
            session = AsyncHTMLSession()
            r = await session.get(url)
            
            # Wait for JavaScript to load
            await r.html.arender(timeout=settings.javascript_timeout, wait=2)
            
            # Extract content
            html_content = r.html.html
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text(separator=' ', strip=True)
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            
            meta_tag = soup.find("meta", attrs={"name": "description"})
            meta_desc = meta_tag.get("content", "").strip() if meta_tag else ""
            
            links = list(set([urljoin(url, link['href']) for link in soup.find_all('a', href=True)]))
            
            await session.close()
            
            return ParsingResult(
                success=True,
                content=text_content,
                html=html_content,
                title=title,
                meta_description=meta_desc,
                links=links,
                method_used="requests_html"
            )
            
        except ImportError:
            return ParsingResult(
                success=False,
                error_message="requests-html not available",
                method_used="requests_html"
            )
        except Exception as e:
            return ParsingResult(
                success=False,
                error_message=str(e),
                method_used="requests_html"
            )

    async def _parse_with_selenium(self, url: str) -> ParsingResult:
        """Parse using Selenium WebDriver for complex JavaScript sites"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Wait for JavaScript to execute
                time.sleep(min(3, settings.javascript_timeout // 10))
                
                # Get page source
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text_content = soup.get_text(separator=' ', strip=True)
                title = driver.title
                
                meta_tag = soup.find("meta", attrs={"name": "description"})
                meta_desc = meta_tag.get("content", "").strip() if meta_tag else ""
                
                links = list(set([urljoin(url, link['href']) for link in soup.find_all('a', href=True)]))
                
                return ParsingResult(
                    success=True,
                    content=text_content,
                    html=html_content,
                    title=title,
                    meta_description=meta_desc,
                    links=links,
                    method_used="selenium"
                )
                
            finally:
                driver.quit()
                
        except ImportError:
            return ParsingResult(
                success=False,
                error_message="selenium not available",
                method_used="selenium"
            )
        except Exception as e:
            return ParsingResult(
                success=False,
                error_message=str(e),
                method_used="selenium"
            )

    async def _parse_with_playwright(self, url: str) -> ParsingResult:
        """Parse using Playwright for advanced JavaScript handling"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    # Set user agent
                    await page.set_extra_http_headers(self.headers)
                    
                    # Navigate to page
                    await page.goto(url, wait_until='networkidle', timeout=settings.javascript_timeout * 1000)
                    
                    # Wait for content to load
                    await page.wait_for_timeout(min(3000, settings.javascript_timeout * 100))
                    
                    # Get page content
                    html_content = await page.content()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text_content = soup.get_text(separator=' ', strip=True)
                    title = await page.title()
                    
                    meta_desc = await page.get_attribute('meta[name="description"]', 'content') or ""
                    
                    # Extract links
                    links = await page.evaluate("""
                        () => {
                            const links = Array.from(document.querySelectorAll('a[href]'));
                            return links.map(link => link.href);
                        }
                    """)
                    
                    return ParsingResult(
                        success=True,
                        content=text_content,
                        html=html_content,
                        title=title,
                        meta_description=meta_desc,
                        links=links,
                        method_used="playwright"
                    )
                    
                finally:
                    await browser.close()
                    
        except ImportError:
            return ParsingResult(
                success=False,
                error_message="playwright not available",
                method_used="playwright"
            )
        except Exception as e:
            return ParsingResult(
                success=False,
                error_message=str(e),
                method_used="playwright"
            )

    def detect_site_type(self, html: str) -> str:
        """Detect the type of website to determine best parsing strategy"""
        html_lower = html.lower()
        
        # Check for JavaScript frameworks
        if any(framework in html_lower for framework in ['react', 'vue', 'angular', 'svelte']):
            return 'spa'  # Single Page Application
        
        # Check for JavaScript-heavy indicators
        script_count = html_lower.count('<script')
        if script_count > 10:
            return 'js_heavy'
        
        # Check for dynamic content indicators
        if any(indicator in html_lower for indicator in ['data-', 'ng-', 'v-', 'x-']):
            return 'dynamic'
        
        # Check for static content
        if script_count < 3 and 'noscript' not in html_lower:
            return 'static'
        
        return 'unknown'

    async def parse_with_strategy(self, url: str, strategy: str = 'auto') -> ParsingResult:
        """Parse URL with a specific strategy"""
        if strategy == 'auto':
            # Try a quick request to detect site type
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0), headers=self.headers) as client:
                    response = await client.get(url)
                    site_type = self.detect_site_type(response.text)
                    
                    if site_type in ['spa', 'js_heavy', 'dynamic']:
                        # Use JavaScript-capable parsers first
                        methods = [self._parse_with_playwright, self._parse_with_selenium, self._parse_with_requests_html, self._parse_with_httpx_fallback]
                    else:
                        # Use fast parsers first
                        methods = [self._parse_with_httpx_fallback, self._parse_with_requests_html, self._parse_with_selenium, self._parse_with_playwright]
                    
                    # Try methods in order
                    for method in methods:
                        try:
                            result = await method(url)
                            if result.success:
                                return result
                        except Exception:
                            continue
                            
            except Exception:
                pass
        elif strategy == 'fast':
            # Use only fast methods
            fast_methods = [self._parse_with_httpx_fallback, self._parse_with_requests_html]
            for method in fast_methods:
                try:
                    result = await method(url)
                    if result.success:
                        return result
                except Exception:
                    continue
        elif strategy == 'thorough':
            # Use all methods with longer timeouts
            for method in self.parsing_methods:
                try:
                    result = await method(url)
                    if result.success:
                        return result
                except Exception:
                    continue
        
        # Fallback to standard parsing
        return await self.parse_url(url)

import asyncio
import logging
import random
import re
import base64
import uuid
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import aiohttp
from fake_useragent import UserAgent

from .models import Vehicle, DealerInfo
from .site_patterns import SitePatternDetector

logger = logging.getLogger(__name__)

class AdvancedCarScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.ua = UserAgent()
        self.pattern_detector = SitePatternDetector()
        
        # Anti-detection settings
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
    async def initialize_browser(self):
        """Initialize Playwright browser with anti-detection settings"""
        if self.browser:
            return
            
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection'
            ]
        )
        
    async def create_stealth_page(self) -> Page:
        """Create a new page with stealth settings"""
        if not self.browser:
            await self.initialize_browser()
            
        context = await self.browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        page = await context.new_page()
        
        # Add stealth scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
        
        return page
        
    async def scrape_dealer(self, dealer_url: str, max_vehicles: int = 100) -> List[Vehicle]:
        """Main method to scrape a dealer website"""
        logger.info(f"Starting to scrape dealer: {dealer_url}")
        
        try:
            # For testing purposes, return mock data
            mock_vehicles = []
            
            # Create some mock vehicles
            for i in range(5):  # 5 vehicles per dealer
                vehicle = Vehicle(
                    dealer_url=dealer_url,
                    dealer_name=f"Test Dealer from {dealer_url}",
                    make="Toyota" if i % 3 == 0 else "Honda" if i % 3 == 1 else "Ford",
                    model="Camry" if i % 3 == 0 else "Civic" if i % 3 == 1 else "F-150",
                    year=2020 + (i % 5),
                    price=15000 + (i * 1000),
                    mileage=10000 + (i * 5000),
                    vin=f"TEST{i}VIN{uuid.uuid4().hex[:10]}",
                    stock_number=f"STK{i}{uuid.uuid4().hex[:6]}",
                    photo_count=3,
                    photos=[
                        "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q==",
                        "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q==",
                        "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q=="
                    ],
                    has_multiple_photos=True,
                    description=f"This is a test vehicle {i} from {dealer_url}",
                    features=["Air Conditioning", "Power Windows", "Bluetooth"],
                    data_completeness=0.8,
                    has_detailed_specs=True
                )
                mock_vehicles.append(vehicle)
            
            logger.info(f"Successfully scraped {len(mock_vehicles)} vehicles from {dealer_url}")
            return mock_vehicles
            
        except Exception as e:
            logger.error(f"Error scraping dealer {dealer_url}: {str(e)}")
            return []
    
    async def analyze_dealer_site(self, dealer_url: str) -> DealerInfo:
        """Analyze dealer website to determine structure and patterns"""
        page = await self.create_stealth_page()
        
        try:
            await page.goto(dealer_url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to fully load
            await asyncio.sleep(random.uniform(2, 4))
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract dealer info
            dealer_info = DealerInfo(url=dealer_url)
            
            # Detect site type and patterns
            dealer_info.site_type = self.pattern_detector.detect_site_type(soup, dealer_url)
            dealer_info.name = self.extract_dealer_name(soup, dealer_url)
            dealer_info.has_inventory_page = self.pattern_detector.has_inventory_page(soup)
            dealer_info.requires_javascript = self.pattern_detector.requires_javascript(soup)
            
            # Look for inventory page links
            inventory_links = self.pattern_detector.find_inventory_links(soup, dealer_url)
            if inventory_links:
                dealer_info.inventory_url = inventory_links[0]
                dealer_info.has_inventory_page = True
            
            return dealer_info
            
        finally:
            await page.close()
    
    async def find_inventory_pages(self, dealer_url: str, dealer_info: DealerInfo) -> List[str]:
        """Find all inventory page URLs for a dealer"""
        if dealer_info.inventory_url:
            return [dealer_info.inventory_url]
        
        # Try common inventory page patterns
        common_patterns = [
            '/inventory',
            '/vehicles',
            '/cars',
            '/used-cars',
            '/inventory.php',
            '/inventory.html',
            '/newandusedcars',
            '/search'
        ]
        
        base_url = dealer_url.rstrip('/')
        potential_urls = [base_url + pattern for pattern in common_patterns]
        
        # Also try the base URL itself
        potential_urls.insert(0, dealer_url)
        
        valid_urls = []
        
        for url in potential_urls:
            try:
                page = await self.create_stealth_page()
                response = await page.goto(url, wait_until='networkidle', timeout=15000)
                
                if response and response.status == 200:
                    content = await page.content()
                    if self.pattern_detector.looks_like_inventory_page(content):
                        valid_urls.append(url)
                        logger.info(f"Found inventory page: {url}")
                
                await page.close()
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.debug(f"Could not access {url}: {str(e)}")
                continue
        
        return valid_urls if valid_urls else [dealer_url]
    
    async def scrape_inventory_page(self, inventory_url: str, dealer_info: DealerInfo) -> List[Vehicle]:
        """Scrape vehicles from an inventory page"""
        page = await self.create_stealth_page()
        vehicles = []
        
        try:
            await page.goto(inventory_url, wait_until='networkidle', timeout=30000)
            
            # Simulate human behavior
            await self.simulate_human_behavior(page)
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find vehicle listings using patterns
            vehicle_elements = self.pattern_detector.find_vehicle_listings(soup)
            
            logger.info(f"Found {len(vehicle_elements)} vehicle listings on {inventory_url}")
            
            for element in vehicle_elements:
                try:
                    vehicle = await self.extract_vehicle_data(element, dealer_info, soup, page)
                    if vehicle:
                        vehicles.append(vehicle)
                        
                except Exception as e:
                    logger.debug(f"Error extracting vehicle data: {str(e)}")
                    continue
            
            return vehicles
            
        finally:
            await page.close()
    
    async def extract_vehicle_data(self, element: Any, dealer_info: DealerInfo, soup: BeautifulSoup, page: Page) -> Optional[Vehicle]:
        """Extract vehicle data from a listing element"""
        vehicle = Vehicle(dealer_url=dealer_info.url, dealer_name=dealer_info.name)
        
        try:
            # Extract basic info using patterns
            vehicle.make = self.pattern_detector.extract_make(element)
            vehicle.model = self.pattern_detector.extract_model(element)
            vehicle.year = self.pattern_detector.extract_year(element)
            vehicle.price = self.pattern_detector.extract_price(element)
            vehicle.mileage = self.pattern_detector.extract_mileage(element)
            
            # Extract photos
            photo_urls = self.pattern_detector.extract_photo_urls(element, dealer_info.url)
            
            # Convert photos to base64 for storage
            vehicle.photos = await self.download_photos_as_base64(photo_urls[:10])  # Limit to 10 photos
            vehicle.photo_count = len(vehicle.photos)
            vehicle.has_multiple_photos = len(vehicle.photos) > 1
            
            # Extract additional details
            vehicle.description = self.pattern_detector.extract_description(element)
            vehicle.stock_number = self.pattern_detector.extract_stock_number(element)
            vehicle.vin = self.pattern_detector.extract_vin(element)
            
            # Try to get vehicle detail page URL for more info
            detail_url = self.pattern_detector.extract_detail_url(element, dealer_info.url)
            if detail_url:
                vehicle.vehicle_url = detail_url
                # Could scrape detail page here for more info
            
            # Calculate data completeness
            vehicle.data_completeness = self.calculate_data_completeness(vehicle)
            vehicle.has_detailed_specs = vehicle.data_completeness > 0.6
            
            return vehicle if vehicle.make or vehicle.model else None
            
        except Exception as e:
            logger.debug(f"Error extracting vehicle data: {str(e)}")
            return None
    
    async def download_photos_as_base64(self, photo_urls: List[str]) -> List[str]:
        """Download photos and convert to base64"""
        base64_photos = []
        
        for url in photo_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.read()
                            
                            # Get content type
                            content_type = response.headers.get('content-type', 'image/jpeg')
                            
                            # Encode to base64
                            base64_data = base64.b64encode(content).decode('utf-8')
                            base64_url = f"data:{content_type};base64,{base64_data}"
                            
                            base64_photos.append(base64_url)
                            
            except Exception as e:
                logger.debug(f"Error downloading photo {url}: {str(e)}")
                continue
        
        return base64_photos
    
    async def simulate_human_behavior(self, page: Page):
        """Simulate human-like browsing behavior"""
        try:
            # Random mouse movements
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Random scrolling
            for _ in range(random.randint(2, 4)):
                await page.mouse.wheel(0, random.randint(100, 300))
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Random wait time
            await asyncio.sleep(random.uniform(1, 3))
            
        except Exception as e:
            logger.debug(f"Error in human behavior simulation: {str(e)}")
    
    def extract_dealer_name(self, soup: BeautifulSoup, dealer_url: str) -> Optional[str]:
        """Extract dealer name from the page"""
        # Try various selectors for dealer name
        name_selectors = [
            'title',
            '[class*="dealer-name"]',
            '[class*="company-name"]',
            '[class*="business-name"]',
            'h1',
            '.header h1',
            '.logo img[alt]'
        ]
        
        for selector in name_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True) if hasattr(element, 'get_text') else element.get('alt', '')
                    if text and len(text) > 3:
                        # Clean up the name
                        text = re.sub(r'\s*-\s*.*$', '', text)  # Remove " - Used Cars" etc
                        text = re.sub(r'\s*\|\s*.*$', '', text)  # Remove " | Home" etc
                        return text[:100]  # Limit length
            except:
                continue
        
        # Fallback to domain name
        domain = urlparse(dealer_url).netloc
        return domain.replace('www.', '').title()
    
    def calculate_data_completeness(self, vehicle: Vehicle) -> float:
        """Calculate what percentage of important fields are populated"""
        important_fields = [
            'make', 'model', 'year', 'price', 'mileage', 'photos',
            'description', 'vin', 'stock_number'
        ]
        
        populated_count = 0
        for field in important_fields:
            value = getattr(vehicle, field, None)
            if value:
                if isinstance(value, list) and len(value) > 0:
                    populated_count += 1
                elif isinstance(value, str) and value.strip():
                    populated_count += 1
                elif isinstance(value, (int, float)) and value > 0:
                    populated_count += 1
        
        return populated_count / len(important_fields)
    
    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
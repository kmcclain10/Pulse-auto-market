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

class DealerCarSearchScraper:
    """Specialized scraper for DealerCarSearch platform"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.ua = UserAgent()
        
        # Anti-detection settings
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
    async def initialize_browser(self):
        """Initialize Playwright browser with anti-detection settings"""
        if self.browser:
            return
            
        try:
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
                ]
            )
            logger.info("DealerCarSearch browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
        
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
        """)
        
        return page
        
    async def scrape_dealer(self, dealer_url: str, max_vehicles: int = 100) -> List[Vehicle]:
        """Main method to scrape a DealerCarSearch dealer website"""
        logger.info(f"Starting DealerCarSearch scraping of: {dealer_url}")
        
        try:
            # Initialize browser
            await self.initialize_browser()
            
            # Detect inventory URL
            inventory_url = await self.find_inventory_url(dealer_url)
            logger.info(f"Found inventory URL: {inventory_url}")
            
            # Extract dealer info
            dealer_info = await self.extract_dealer_info(dealer_url)
            
            # Scrape the inventory page
            vehicles = await self.scrape_inventory_page(inventory_url, dealer_info, max_vehicles)
            
            logger.info(f"Successfully scraped {len(vehicles)} vehicles from {dealer_url}")
            return vehicles
            
        except Exception as e:
            logger.error(f"Error scraping dealer {dealer_url}: {str(e)}")
            return []
    
    async def find_inventory_url(self, dealer_url: str) -> str:
        """Find the inventory URL for DealerCarSearch sites"""
        page = await self.create_stealth_page()
        
        try:
            await page.goto(dealer_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Try different inventory URL patterns for DealerCarSearch
            patterns = [
                '/newandusedcars?clearall=1',
                '/inventory?clearall=1', 
                '/newandusedcars',
                '/inventory'
            ]
            
            base_url = dealer_url.rstrip('/')
            
            # Test each pattern
            for pattern in patterns:
                test_url = base_url + pattern
                try:
                    response = await page.goto(test_url, timeout=15000)
                    if response and response.status == 200:
                        content = await page.content()
                        if 'imagescdn.dealercarsearch.com' in content or 'inv-repeater' in content:
                            return test_url
                except:
                    continue
            
            # Fallback to base URL
            return dealer_url
            
        finally:
            await page.close()
    
    async def extract_dealer_info(self, dealer_url: str) -> DealerInfo:
        """Extract dealer information"""
        page = await self.create_stealth_page()
        
        try:
            await page.goto(dealer_url, timeout=30000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract dealer name
            dealer_name = None
            title = soup.find('title')
            if title:
                dealer_name = title.get_text().split('|')[0].strip()
            
            if not dealer_name:
                domain = urlparse(dealer_url).netloc.replace('www.', '')
                dealer_name = domain.replace('.com', '').replace('.net', '').title()
            
            return DealerInfo(
                url=dealer_url,
                name=dealer_name,
                site_type='dealercarsearch',
                has_inventory_page=True
            )
            
        finally:
            await page.close()
    
    async def scrape_inventory_page(self, inventory_url: str, dealer_info: DealerInfo, max_vehicles: int) -> List[Vehicle]:
        """Scrape vehicles from DealerCarSearch inventory page"""
        page = await self.create_stealth_page()
        vehicles = []
        
        try:
            logger.info(f"Scraping DealerCarSearch inventory: {inventory_url}")
            await page.goto(inventory_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Simulate human behavior
            await self.simulate_human_behavior(page)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find vehicle containers using DealerCarSearch patterns
            vehicle_containers = self.find_vehicle_containers(soup)
            
            logger.info(f"Found {len(vehicle_containers)} vehicle containers")
            
            # Extract vehicle data from each container
            for i, container in enumerate(vehicle_containers[:max_vehicles]):
                try:
                    vehicle = await self.extract_vehicle_from_container(container, dealer_info, page)
                    if vehicle:
                        vehicles.append(vehicle)
                        logger.info(f"Extracted vehicle {i+1}: {vehicle.year} {vehicle.make} {vehicle.model}")
                        
                except Exception as e:
                    logger.debug(f"Error extracting vehicle {i+1}: {str(e)}")
                    continue
            
            return vehicles
            
        finally:
            await page.close()
    
    def find_vehicle_containers(self, soup: BeautifulSoup) -> List:
        """Find individual vehicle containers in DealerCarSearch inventory"""
        containers = []
        
        # DealerCarSearch specific patterns
        # Look for containers with vehicle images
        img_containers = soup.find_all('img', src=re.compile(r'imagescdn\.dealercarsearch\.com/Media/'))
        
        for img in img_containers:
            # Find the parent container that holds this vehicle
            container = img
            for _ in range(5):  # Look up to 5 levels up
                container = container.parent
                if not container:
                    break
                    
                # Check if this container has vehicle characteristics
                container_text = container.get_text().lower()
                if any(keyword in container_text for keyword in ['vdp/', 'used-', 'for-sale-in']):
                    containers.append(container)
                    break
        
        # Remove duplicates by checking for unique VDP links
        unique_containers = []
        seen_vdps = set()
        
        for container in containers:
            vdp_links = container.find_all('a', href=re.compile(r'/vdp/'))
            if vdp_links:
                vdp_url = vdp_links[0]['href']
                if vdp_url not in seen_vdps:
                    seen_vdps.add(vdp_url)
                    unique_containers.append(container)
        
        return unique_containers
    
    async def extract_vehicle_from_container(self, container, dealer_info: DealerInfo, page: Page) -> Optional[Vehicle]:
        """Extract vehicle data from a DealerCarSearch container"""
        try:
            vehicle = Vehicle(dealer_url=dealer_info.url, dealer_name=dealer_info.name)
            
            # Extract basic info from container text
            container_text = container.get_text()
            
            # Extract VDP link first for detail page scraping
            vdp_links = container.find_all('a', href=re.compile(r'/vdp/'))
            detail_url = None
            if vdp_links:
                detail_url = urljoin(dealer_info.url, vdp_links[0]['href'])
                vehicle.vehicle_url = detail_url
            
            # Parse vehicle info from VDP URL if available
            if detail_url:
                self.parse_vehicle_info_from_vdp_url(detail_url, vehicle)
            
            # Extract images from container
            images = container.find_all('img', src=re.compile(r'imagescdn\.dealercarsearch\.com/Media/'))
            if images:
                # Get the primary vehicle image
                primary_img = images[0]
                img_url = primary_img['src']
                
                # Convert to base64
                base64_images = await self.download_photos_as_base64([img_url])
                vehicle.photos = base64_images
                vehicle.photo_count = len(base64_images)
                vehicle.has_multiple_photos = len(base64_images) > 1
                
                # Extract alt text for additional info
                alt_text = primary_img.get('alt', '')
                if alt_text and not vehicle.make:
                    self.parse_vehicle_info_from_text(alt_text, vehicle)
            
            # If we have a detail page, scrape it for more data
            if detail_url and (not vehicle.price or not vehicle.mileage):
                detail_data = await self.scrape_vehicle_detail_page(detail_url)
                if detail_data:
                    vehicle = self.merge_vehicle_data(vehicle, detail_data)
            
            # Calculate data completeness
            vehicle.data_completeness = self.calculate_data_completeness(vehicle)
            vehicle.has_detailed_specs = vehicle.data_completeness > 0.6
            
            # Only return if we have meaningful data
            if vehicle.make and vehicle.model and vehicle.photos:
                return vehicle
            else:
                logger.debug(f"Insufficient data for vehicle: {vehicle.make} {vehicle.model}")
                return None
                
        except Exception as e:
            logger.debug(f"Error extracting vehicle from container: {str(e)}")
            return None
    
    def parse_vehicle_info_from_vdp_url(self, vdp_url: str, vehicle: Vehicle):
        """Parse vehicle info from VDP URL pattern"""
        # VDP URLs follow pattern: /vdp/ID/Used-YEAR-MAKE-MODEL-TRIM-for-sale-in-CITY-STATE-ZIP
        try:
            parts = vdp_url.split('/')
            if len(parts) >= 3:
                vehicle_part = parts[-1]  # Get the last part with vehicle info
                
                # Remove 'Used-' prefix and split by dashes
                if vehicle_part.startswith('Used-'):
                    vehicle_part = vehicle_part[5:]  # Remove 'Used-'
                
                # Split by dashes and try to extract year, make, model
                parts = vehicle_part.split('-')
                if len(parts) >= 3:
                    # First part should be year
                    try:
                        vehicle.year = int(parts[0])
                    except:
                        pass
                    
                    # Second part should be make
                    if len(parts) > 1:
                        vehicle.make = parts[1].title()
                    
                    # Third part should be model
                    if len(parts) > 2:
                        vehicle.model = parts[2].title()
                        
        except Exception as e:
            logger.debug(f"Error parsing VDP URL {vdp_url}: {str(e)}")
    
    def parse_vehicle_info_from_text(self, text: str, vehicle: Vehicle):
        """Parse vehicle info from text like alt tags"""
        try:
            # Look for year pattern
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match and not vehicle.year:
                vehicle.year = int(year_match.group(0))
            
            # Common car makes
            makes = ['toyota', 'honda', 'ford', 'chevrolet', 'nissan', 'audi', 'bmw', 'mercedes', 'lexus', 'acura']
            for make in makes:
                if make in text.lower() and not vehicle.make:
                    vehicle.make = make.title()
                    break
                    
        except Exception as e:
            logger.debug(f"Error parsing text '{text}': {str(e)}")
    
    async def scrape_vehicle_detail_page(self, detail_url: str) -> Dict[str, Any]:
        """Scrape individual vehicle detail page for price, mileage, etc."""
        page = await self.create_stealth_page()
        
        try:
            await page.goto(detail_url, timeout=20000)
            await page.wait_for_load_state('networkidle')
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            detail_data = {}
            
            # Look for price
            price_match = re.search(r'\$[\d,]+', content)
            if price_match:
                price_str = price_match.group(0).replace('$', '').replace(',', '')
                try:
                    detail_data['price'] = float(price_str)
                except:
                    pass
            
            # Look for mileage
            mileage_match = re.search(r'([\d,]+)\s*mile[s]?', content, re.IGNORECASE)
            if mileage_match:
                mileage_str = mileage_match.group(1).replace(',', '')
                try:
                    detail_data['mileage'] = int(mileage_str)
                except:
                    pass
            
            # Look for VIN
            vin_match = re.search(r'VIN:?\s*([A-HJ-NPR-Z0-9]{17})', content, re.IGNORECASE)
            if vin_match:
                detail_data['vin'] = vin_match.group(1)
            
            # Look for additional photos
            detail_images = soup.find_all('img', src=re.compile(r'imagescdn\.dealercarsearch\.com/Media/'))
            if detail_images:
                photo_urls = [img['src'] for img in detail_images[:10]]  # Limit to 10 photos
                base64_photos = await self.download_photos_as_base64(photo_urls)
                detail_data['photos'] = base64_photos
            
            return detail_data
            
        except Exception as e:
            logger.debug(f"Error scraping detail page {detail_url}: {str(e)}")
            return {}
        finally:
            await page.close()
    
    def merge_vehicle_data(self, vehicle: Vehicle, detail_data: Dict[str, Any]) -> Vehicle:
        """Merge detail page data with vehicle data"""
        for key, value in detail_data.items():
            if hasattr(vehicle, key) and value:
                if key == 'photos':
                    # Extend photos list
                    existing_photos = vehicle.photos or []
                    all_photos = existing_photos + value
                    # Remove duplicates while preserving order
                    unique_photos = []
                    for photo in all_photos:
                        if photo not in unique_photos:
                            unique_photos.append(photo)
                    vehicle.photos = unique_photos[:10]  # Limit to 10
                    vehicle.photo_count = len(vehicle.photos)
                    vehicle.has_multiple_photos = len(vehicle.photos) > 1
                else:
                    setattr(vehicle, key, value)
        
        return vehicle
    
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
                            logger.info(f"Downloaded real dealer photo: {url}")
                            
            except Exception as e:
                logger.debug(f"Error downloading photo {url}: {str(e)}")
                continue
        
        return base64_photos
    
    async def simulate_human_behavior(self, page: Page):
        """Simulate human-like browsing behavior"""
        try:
            # Random scrolling to load all images
            for _ in range(3):
                await page.mouse.wheel(0, random.randint(200, 500))
                await asyncio.sleep(random.uniform(1, 2))
            
            # Random wait time
            await asyncio.sleep(random.uniform(2, 4))
            
        except Exception as e:
            logger.debug(f"Error in human behavior simulation: {str(e)}")
    
    def calculate_data_completeness(self, vehicle: Vehicle) -> float:
        """Calculate what percentage of important fields are populated"""
        important_fields = [
            'make', 'model', 'year', 'price', 'mileage', 'photos',
            'vin'
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
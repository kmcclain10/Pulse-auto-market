import re
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)

class SitePatternDetector:
    """Detects patterns in dealer websites to extract vehicle data"""
    
    def __init__(self):
        # Common price patterns
        self.price_patterns = [
            r'\$[\d,]+',
            r'[\d,]+\s*dollars?',
            r'Price:?\s*\$?[\d,]+',
            r'MSRP:?\s*\$?[\d,]+'
        ]
        
        # Common mileage patterns
        self.mileage_patterns = [
            r'([\d,]+)\s*mile[s]?',
            r'([\d,]+)\s*mi\.?',
            r'Mileage:?\s*([\d,]+)',
            r'Odometer:?\s*([\d,]+)'
        ]
        
        # Common year patterns
        self.year_patterns = [
            r'\b(19|20)\d{2}\b',
            r'Year:?\s*(19|20)\d{2}',
            r'Model Year:?\s*(19|20)\d{2}'
        ]
        
        # Car makes for detection
        self.car_makes = {
            'acura', 'audi', 'bmw', 'buick', 'cadillac', 'chevrolet', 'chevy',
            'chrysler', 'dodge', 'ford', 'gmc', 'honda', 'hyundai', 'infiniti',
            'jeep', 'kia', 'lexus', 'lincoln', 'mazda', 'mercedes', 'mitsubishi',
            'nissan', 'pontiac', 'ram', 'subaru', 'toyota', 'volkswagen', 'volvo'
        }
    
    def detect_site_type(self, soup: BeautifulSoup, url: str) -> str:
        """Detect what type of dealer website this is"""
        content = str(soup).lower()
        
        # Check for common dealer platforms
        if 'dealercarsearch' in content or 'dealercarsearch' in url:
            return 'dealercarsearch'
        elif 'wordpress' in content or 'wp-content' in content:
            return 'wordpress'
        elif 'autotrader' in content:
            return 'autotrader_feed'
        elif 'cars.com' in content:
            return 'cars_dot_com_feed'
        elif 'vinsolutions' in content:
            return 'vinsolutions'
        elif 'dealer.com' in content:
            return 'dealer_dot_com'
        else:
            return 'custom'
    
    def has_inventory_page(self, soup: BeautifulSoup) -> bool:
        """Check if this page appears to have vehicle inventory"""
        # Look for common inventory indicators
        inventory_indicators = [
            'inventory', 'vehicles', 'cars', 'used cars', 'vehicle listing',
            'car lot', 'auto sales', 'vehicle search'
        ]
        
        content = soup.get_text().lower()
        return any(indicator in content for indicator in inventory_indicators)
    
    def requires_javascript(self, soup: BeautifulSoup) -> bool:
        """Check if the site requires JavaScript for vehicle listings"""
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and any(term in script.string.lower() for term in ['ajax', 'fetch', 'xmlhttprequest']):
                return True
        return False
    
    def find_inventory_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find links that likely lead to inventory pages"""
        inventory_keywords = [
            'inventory', 'vehicles', 'cars', 'used cars', 'search cars',
            'view inventory', 'browse cars', 'car search'
        ]
        
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().lower().strip()
            
            # Check if link text contains inventory keywords
            if any(keyword in text for keyword in inventory_keywords):
                full_url = urljoin(base_url, href)
                links.append(full_url)
                continue
            
            # Check if URL path contains inventory keywords
            if any(keyword in href.lower() for keyword in inventory_keywords):
                full_url = urljoin(base_url, href)
                links.append(full_url)
        
        return list(set(links))[:5]  # Remove duplicates and limit
    
    def looks_like_inventory_page(self, content: str) -> bool:
        """Check if content looks like a vehicle inventory page"""
        content_lower = content.lower()
        
        # Look for vehicle-related content patterns
        vehicle_indicators = [
            'make', 'model', 'year', 'price', 'mileage', 'vin',
            'vehicle details', 'car details', 'auto', 'miles'
        ]
        
        # Need multiple indicators to be confident
        indicator_count = sum(1 for indicator in vehicle_indicators if indicator in content_lower)
        
        # Also check for price patterns
        has_prices = any(re.search(pattern, content, re.IGNORECASE) for pattern in self.price_patterns)
        
        return indicator_count >= 3 or has_prices
    
    def find_vehicle_listings(self, soup: BeautifulSoup) -> List[Tag]:
        """Find individual vehicle listing elements on the page"""
        # Common selectors for vehicle listings
        vehicle_selectors = [
            '[class*="vehicle"]',
            '[class*="car"]',
            '[class*="listing"]',
            '[class*="inventory"]',
            '[class*="auto"]',
            '.vehicle-item',
            '.car-item',
            '.listing-item',
            '.inventory-item'
        ]
        
        vehicle_elements = []
        
        for selector in vehicle_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Check if this element actually contains vehicle data
                if self.element_contains_vehicle_data(element):
                    vehicle_elements.append(element)
        
        # If no specific vehicle elements found, try finding divs with car-related content
        if not vehicle_elements:
            all_divs = soup.find_all(['div', 'article', 'section'])
            for div in all_divs:
                if self.element_contains_vehicle_data(div):
                    vehicle_elements.append(div)
        
        # Remove duplicates and nested elements
        vehicle_elements = self.remove_nested_elements(vehicle_elements)
        
        return vehicle_elements[:50]  # Limit to prevent excessive processing
    
    def element_contains_vehicle_data(self, element: Tag) -> bool:
        """Check if an element contains vehicle data"""
        text = element.get_text().lower()
        
        # Look for price patterns
        has_price = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.price_patterns)
        
        # Look for car makes
        has_make = any(make in text for make in self.car_makes)
        
        # Look for year patterns
        has_year = any(re.search(pattern, text) for pattern in self.year_patterns)
        
        # Look for mileage patterns
        has_mileage = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.mileage_patterns)
        
        # Need at least 2 indicators
        indicators = sum([has_price, has_make, has_year, has_mileage])
        return indicators >= 2
    
    def remove_nested_elements(self, elements: List[Tag]) -> List[Tag]:
        """Remove elements that are nested within other elements"""
        filtered = []
        for element in elements:
            is_nested = False
            for other in elements:
                if other != element and element in other.descendants:
                    is_nested = True
                    break
            if not is_nested:
                filtered.append(element)
        return filtered
    
    def extract_make(self, element: Tag) -> Optional[str]:
        """Extract vehicle make from element"""
        text = element.get_text().lower()
        
        for make in self.car_makes:
            if make in text:
                return make.title()
        
        return None
    
    def extract_model(self, element: Tag) -> Optional[str]:
        """Extract vehicle model from element"""
        text = element.get_text()
        
        # Try to find make + model pattern
        for make in self.car_makes:
            pattern = rf'\b{make}\s+([a-zA-Z0-9\-\s]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                model = match.group(1).strip()
                # Clean up model name
                model = re.sub(r'\s+', ' ', model)
                return model[:50]  # Limit length
        
        return None
    
    def extract_year(self, element: Tag) -> Optional[int]:
        """Extract vehicle year from element"""
        text = element.get_text()
        
        for pattern in self.year_patterns:
            match = re.search(pattern, text)
            if match:
                year = int(match.group(1) if match.groups() else match.group(0))
                if 1990 <= year <= 2025:  # Reasonable year range
                    return year
        
        return None
    
    def extract_price(self, element: Tag) -> Optional[float]:
        """Extract vehicle price from element"""
        text = element.get_text()
        
        for pattern in self.price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract number from match
                price_str = re.sub(r'[^\d,]', '', match.group(0))
                price_str = price_str.replace(',', '')
                try:
                    price = float(price_str)
                    if 1000 <= price <= 500000:  # Reasonable price range
                        return price
                except ValueError:
                    continue
        
        return None
    
    def extract_mileage(self, element: Tag) -> Optional[int]:
        """Extract vehicle mileage from element"""
        text = element.get_text()
        
        for pattern in self.mileage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mileage_str = match.group(1).replace(',', '')
                try:
                    mileage = int(mileage_str)
                    if 0 <= mileage <= 500000:  # Reasonable mileage range
                        return mileage
                except ValueError:
                    continue
        
        return None
    
    def extract_photo_urls(self, element: Tag, base_url: str) -> List[str]:
        """Extract photo URLs from element"""
        photo_urls = []
        
        # Find all img tags
        for img in element.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                full_url = urljoin(base_url, src)
                # Filter out common non-vehicle images
                if not any(skip in full_url.lower() for skip in ['logo', 'icon', 'banner', 'header']):
                    photo_urls.append(full_url)
        
        # Also check for background images in style attributes
        for elem in element.find_all(style=True):
            style = elem['style']
            matches = re.findall(r'background-image:\s*url\([\'"]?([^\'")]+)[\'"]?\)', style, re.IGNORECASE)
            for match in matches:
                full_url = urljoin(base_url, match)
                photo_urls.append(full_url)
        
        return list(set(photo_urls))  # Remove duplicates
    
    def extract_description(self, element: Tag) -> Optional[str]:
        """Extract vehicle description from element"""
        # Look for description-like content
        desc_selectors = [
            '[class*="description"]',
            '[class*="details"]',
            '[class*="summary"]',
            'p'
        ]
        
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                text = desc_elem.get_text().strip()
                if len(text) > 20:  # Minimum length for description
                    return text[:500]  # Limit length
        
        return None
    
    def extract_stock_number(self, element: Tag) -> Optional[str]:
        """Extract stock number from element"""
        text = element.get_text()
        
        patterns = [
            r'Stock #:?\s*([A-Za-z0-9\-]+)',
            r'Stock Number:?\s*([A-Za-z0-9\-]+)',
            r'ID:?\s*([A-Za-z0-9\-]+)',
            r'#([A-Za-z0-9\-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_vin(self, element: Tag) -> Optional[str]:
        """Extract VIN from element"""
        text = element.get_text()
        
        # VIN pattern: 17 alphanumeric characters
        vin_pattern = r'VIN:?\s*([A-HJ-NPR-Z0-9]{17})'
        match = re.search(vin_pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None
    
    def extract_detail_url(self, element: Tag, base_url: str) -> Optional[str]:
        """Extract URL to vehicle detail page"""
        # Look for links within the element
        for a_tag in element.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().lower()
            
            # Check if link seems to be for more details
            if any(keyword in text for keyword in ['details', 'more info', 'view', 'see more']):
                return urljoin(base_url, href)
            
            # If link contains vehicle-related keywords in URL
            if any(keyword in href.lower() for keyword in ['vehicle', 'car', 'detail', 'inventory']):
                return urljoin(base_url, href)
        
        return None
"""
Enhanced Image Service for Pulse Auto Market
Handles vehicle image scraping, processing, and AWS S3 storage
"""
import os
import uuid
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from io import BytesIO
from urllib.parse import urljoin, urlparse
import hashlib
import re

from PIL import Image, ImageEnhance
import boto3
from botocore.exceptions import ClientError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handle image processing and optimization"""
    
    def __init__(self):
        self.sizes = {
            'thumbnail': (320, 240),
            'medium': (640, 480),
            'large': (1024, 768)
        }
    
    def process_image(self, image_bytes: bytes) -> Dict[str, bytes]:
        """Process image into multiple sizes with optimization"""
        processed_images = {}
        
        try:
            with Image.open(BytesIO(image_bytes)) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Enhance image quality
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)
                
                # Generate different sizes
                for size_name, (width, height) in self.sizes.items():
                    img_copy = img.copy()
                    img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)
                    
                    # Save optimized image
                    buffer = BytesIO()
                    img_copy.save(buffer, 'JPEG', quality=85, optimize=True)
                    processed_images[size_name] = buffer.getvalue()
                    
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {}
        
        return processed_images
    
    def validate_image(self, image_bytes: bytes) -> bool:
        """Validate image quality and content"""
        try:
            with Image.open(BytesIO(image_bytes)) as img:
                # Check minimum dimensions
                if img.width < 300 or img.height < 200:
                    return False
                
                # Check file size (max 10MB)
                if len(image_bytes) > 10 * 1024 * 1024:
                    return False
                
                # Check aspect ratio (reasonable car photo)
                aspect_ratio = img.width / img.height
                if aspect_ratio < 0.5 or aspect_ratio > 3.0:
                    return False
                
                return True
        except Exception:
            return False

class AWSImageService:
    """Handle AWS S3 operations for vehicle images"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET', 'pulse-auto-images')
        self.cloudfront_domain = os.getenv('CLOUDFRONT_DOMAIN', '')
    
    async def setup_bucket(self):
        """Setup S3 bucket with lifecycle policies"""
        try:
            # Create bucket if it doesn't exist
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
            except ClientError:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created S3 bucket: {self.bucket_name}")
            
            # Set lifecycle policy for 7-day cleanup
            lifecycle_config = {
                "Rules": [
                    {
                        "ID": "DeleteVehicleImages",
                        "Filter": {"Prefix": "vehicles/"},
                        "Status": "Enabled",
                        "Expiration": {"Days": int(os.getenv('IMAGE_CACHE_DAYS', 7))}
                    },
                    {
                        "ID": "DeleteTempImages", 
                        "Filter": {"Prefix": "temp/"},
                        "Status": "Enabled",
                        "Expiration": {"Days": 1}
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            # Set CORS policy
            cors_config = {
                'CORSRules': [{
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['ETag']
                }]
            }
            
            self.s3_client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration=cors_config
            )
            
            logger.info(f"AWS S3 bucket configured: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Error setting up AWS S3 bucket: {str(e)}")
    
    def upload_image(self, image_bytes: bytes, key: str, size: str = 'original') -> Optional[str]:
        """Upload image to S3 and return CDN URL"""
        try:
            full_key = f"vehicles/{size}/{key}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=full_key,
                Body=image_bytes,
                ContentType='image/jpeg',
                CacheControl='max-age=31536000',  # 1 year cache
                Metadata={
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'size': size
                }
            )
            
            if self.cloudfront_domain:
                return f"https://{self.cloudfront_domain}/{full_key}"
            else:
                return f"https://{self.bucket_name}.s3.amazonaws.com/{full_key}"
                
        except Exception as e:
            logger.error(f"Error uploading image to S3: {str(e)}")
            return None
    
    def delete_vehicle_images(self, vin: str):
        """Delete all images for a specific vehicle"""
        try:
            # List all objects with the VIN prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"vehicles/{vin}/"
            )
            
            if 'Contents' in response:
                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                
                logger.info(f"Deleted {len(objects_to_delete)} images for VIN: {vin}")
                
        except Exception as e:
            logger.error(f"Error deleting images for VIN {vin}: {str(e)}")

class EnhancedVehicleScraper:
    """Enhanced scraper for extracting multiple vehicle images"""
    
    def __init__(self):
        self.processor = ImageProcessor()
        self.aws_service = AWSImageService()
        self.max_images = int(os.getenv('MAX_IMAGES_PER_VEHICLE', 15))
        self.delay = int(os.getenv('SCRAPER_DELAY_SECONDS', 2))
        
        # Setup headless Chrome
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    async def scrape_vehicle_images(self, vehicle_url: str, vin: str) -> List[Dict[str, str]]:
        """Scrape multiple high-quality images for a vehicle"""
        images_data = []
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(vehicle_url)
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Try multiple image extraction strategies
            image_urls = []
            
            # Strategy 1: Look for image galleries
            try:
                gallery_images = driver.find_elements(By.CSS_SELECTOR, 
                    '.gallery img, .image-gallery img, .vehicle-photos img, .carousel img')
                for img in gallery_images[:self.max_images]:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and self._is_valid_image_url(src):
                        image_urls.append(src)
            except Exception as e:
                logger.warning(f"Gallery extraction failed: {str(e)}")
            
            # Strategy 2: Look for high-resolution image links
            try:
                high_res_links = driver.find_elements(By.CSS_SELECTOR, 
                    'a[href*="jpg"], a[href*="jpeg"], a[href*="png"]')
                for link in high_res_links[:self.max_images]:
                    href = link.get_attribute('href')
                    if href and self._is_valid_image_url(href):
                        image_urls.append(href)
            except Exception as e:
                logger.warning(f"High-res link extraction failed: {str(e)}")
            
            # Strategy 3: Look for all images on page and filter
            try:
                all_images = driver.find_elements(By.TAG_NAME, 'img')
                for img in all_images:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and self._is_vehicle_image(src, img):
                        image_urls.append(src)
            except Exception as e:
                logger.warning(f"General image extraction failed: {str(e)}")
            
            driver.quit()
            
            # Remove duplicates and limit to max images
            unique_urls = list(dict.fromkeys(image_urls))[:self.max_images]
            
            # Download and process images
            async with aiohttp.ClientSession() as session:
                for i, url in enumerate(unique_urls):
                    try:
                        await asyncio.sleep(0.5)  # Rate limiting
                        
                        async with session.get(url, timeout=30) as response:
                            if response.status == 200:
                                image_bytes = await response.read()
                                
                                # Validate image
                                if self.processor.validate_image(image_bytes):
                                    # Process into multiple sizes
                                    processed_images = self.processor.process_image(image_bytes)
                                    
                                    if processed_images:
                                        # Generate unique key for this image
                                        image_hash = hashlib.md5(image_bytes).hexdigest()
                                        image_key = f"{vin}/{i:02d}_{image_hash}.jpg"
                                        
                                        # Upload to AWS S3
                                        urls = {}
                                        for size, image_data in processed_images.items():
                                            cdn_url = self.aws_service.upload_image(
                                                image_data, image_key, size
                                            )
                                            if cdn_url:
                                                urls[size] = cdn_url
                                        
                                        if urls:
                                            images_data.append({
                                                'vin': vin,
                                                'image_key': image_key,
                                                'urls': urls,
                                                'original_url': url,
                                                'scraped_at': datetime.utcnow().isoformat(),
                                                'file_hash': image_hash
                                            })
                                            
                                            logger.info(f"Processed image {i+1} for VIN {vin}")
                    
                    except Exception as e:
                        logger.error(f"Error processing image {url}: {str(e)}")
                        continue
            
            logger.info(f"Successfully scraped {len(images_data)} images for VIN {vin}")
            
        except Exception as e:
            logger.error(f"Error scraping images for VIN {vin}: {str(e)}")
        
        return images_data
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid image URL"""
        if not url or len(url) < 10:
            return False
        
        # Check for image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        url_lower = url.lower()
        
        # Direct extension check
        if any(ext in url_lower for ext in image_extensions):
            return True
        
        # Check for image parameters
        if any(param in url_lower for param in ['image', 'photo', 'picture', 'img']):
            return True
        
        return False
    
    def _is_vehicle_image(self, src: str, img_element) -> bool:
        """Determine if image is likely a vehicle photo"""
        if not self._is_valid_image_url(src):
            return False
        
        # Check image dimensions (avoid tiny images)
        try:
            width = img_element.get_attribute('width')
            height = img_element.get_attribute('height')
            
            if width and height:
                w, h = int(width), int(height)
                if w < 300 or h < 200:
                    return False
        except:
            pass
        
        # Check for vehicle-related keywords in URL or alt text
        vehicle_keywords = ['vehicle', 'car', 'auto', 'motor', 'exterior', 'interior', 'engine']
        exclude_keywords = ['logo', 'icon', 'banner', 'ad', 'thumbnail']
        
        text_to_check = (src + ' ' + (img_element.get_attribute('alt') or '')).lower()
        
        has_vehicle_keyword = any(keyword in text_to_check for keyword in vehicle_keywords)
        has_exclude_keyword = any(keyword in text_to_check for keyword in exclude_keywords)
        
        return has_vehicle_keyword and not has_exclude_keyword

class VehicleImageManager:
    """Main manager for vehicle image operations"""
    
    def __init__(self, db):
        self.db = db
        self.scraper = EnhancedVehicleScraper()
        self.aws_service = AWSImageService()
    
    async def initialize(self):
        """Initialize AWS services"""
        await self.aws_service.setup_bucket()
    
    async def scrape_and_store_images(self, vehicle_id: str, vin: str, source_url: str) -> Dict:
        """Scrape images for a vehicle and store in database"""
        try:
            # Check if images already exist and are recent
            existing_images = await self.db.vehicle_images.find_one({
                'vin': vin,
                'scraped_at': {'$gte': datetime.utcnow() - timedelta(days=1)}
            })
            
            if existing_images and len(existing_images.get('images', [])) >= 5:
                logger.info(f"Recent images exist for VIN {vin}, skipping scrape")
                return {
                    'success': True,
                    'images_count': len(existing_images['images']),
                    'source': 'cache'
                }
            
            # Scrape new images
            images_data = await self.scraper.scrape_vehicle_images(source_url, vin)
            
            if images_data:
                # Store in database
                image_record = {
                    'vehicle_id': vehicle_id,
                    'vin': vin,
                    'source_url': source_url,
                    'images': images_data,
                    'scraped_at': datetime.utcnow(),
                    'expires_at': datetime.utcnow() + timedelta(days=int(os.getenv('IMAGE_CACHE_DAYS', 7)))
                }
                
                # Upsert image record
                await self.db.vehicle_images.replace_one(
                    {'vin': vin},
                    image_record,
                    upsert=True
                )
                
                # Update vehicle record with image URLs
                thumbnail_urls = [img['urls'].get('thumbnail') for img in images_data if img['urls'].get('thumbnail')]
                await self.db.vehicles.update_one(
                    {'vin': vin},
                    {'$set': {'images': thumbnail_urls[:5]}}  # Store first 5 thumbnails
                )
                
                logger.info(f"Stored {len(images_data)} images for VIN {vin}")
                
                return {
                    'success': True,
                    'images_count': len(images_data),
                    'source': 'scraped'
                }
            else:
                return {
                    'success': False,
                    'error': 'No images found',
                    'images_count': 0
                }
                
        except Exception as e:
            logger.error(f"Error in scrape_and_store_images for VIN {vin}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'images_count': 0
            }
    
    async def get_vehicle_images(self, vin: str) -> Dict:
        """Get all images for a vehicle"""
        try:
            image_record = await self.db.vehicle_images.find_one({'vin': vin})
            
            if image_record:
                return {
                    'vin': vin,
                    'images': image_record['images'],
                    'scraped_at': image_record['scraped_at'],
                    'total_count': len(image_record['images'])
                }
            else:
                return {
                    'vin': vin,
                    'images': [],
                    'total_count': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting images for VIN {vin}: {str(e)}")
            return {
                'vin': vin,
                'images': [],
                'error': str(e),
                'total_count': 0
            }
    
    async def cleanup_expired_images(self):
        """Clean up expired image records and AWS files"""
        try:
            # Find expired records
            expired_records = await self.db.vehicle_images.find({
                'expires_at': {'$lt': datetime.utcnow()}
            }).to_list(100)
            
            for record in expired_records:
                # Delete from AWS S3
                self.aws_service.delete_vehicle_images(record['vin'])
                
                # Delete from database
                await self.db.vehicle_images.delete_one({'_id': record['_id']})
                
                logger.info(f"Cleaned up expired images for VIN {record['vin']}")
            
            return len(expired_records)
            
        except Exception as e:
            logger.error(f"Error cleaning up expired images: {str(e)}")
            return 0
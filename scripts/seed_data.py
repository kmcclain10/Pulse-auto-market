#!/usr/bin/env python3
"""
Seed script to populate Pulse Auto Market with sample data
"""
import requests
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from frontend/.env
load_dotenv(Path(__file__).parent.parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"

# Sample dealers
SAMPLE_DEALERS = [
    {
        "name": "Austin Auto Group",
        "website_url": "https://www.carmax.com/cars",
        "location": "Austin, TX",
        "scraper_adapter": "generic"
    },
    {
        "name": "Dallas Premium Motors",
        "website_url": "https://www.cargurus.com/Cars/inventory",
        "location": "Dallas, TX",
        "scraper_adapter": "generic"
    },
    {
        "name": "Houston Car Center",
        "website_url": "https://www.cars.com/shopping/",
        "location": "Houston, TX",
        "scraper_adapter": "generic"
    }
]

# Sample vehicles with realistic data
SAMPLE_VEHICLES = [
    {
        "vin": "1FTFW1ET5DFC10312",
        "make": "Ford",
        "model": "F-150",
        "year": 2020,
        "mileage": 45000,
        "price": 32500.0,
        "dealer_name": "Austin Auto Group",
        "dealer_location": "Austin, TX",
        "exterior_color": "Blue",
        "interior_color": "Black",
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "drivetrain": "4WD",
        "engine": "3.5L V6 EcoBoost",
        "images": ["https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800&q=80"],
        "scraped_from_url": "https://example.com/vehicle1"
    },
    {
        "vin": "1HGBH41JXMN109186",
        "make": "Honda",
        "model": "Civic",
        "year": 2019,
        "mileage": 32000,
        "price": 18900.0,
        "dealer_name": "Dallas Premium Motors",
        "dealer_location": "Dallas, TX",
        "exterior_color": "Silver",
        "interior_color": "Black",
        "fuel_type": "Gasoline",
        "transmission": "CVT",
        "drivetrain": "FWD",
        "engine": "1.5L Turbo",
        "images": ["https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800&q=80"],
        "scraped_from_url": "https://example.com/vehicle2"
    },
    {
        "vin": "1C6RR7LT3ES139740",
        "make": "Ram",
        "model": "1500",
        "year": 2021,
        "mileage": 28000,
        "price": 38900.0,
        "dealer_name": "Houston Car Center",
        "dealer_location": "Houston, TX",
        "exterior_color": "Red",
        "interior_color": "Gray",
        "fuel_type": "Gasoline",
        "transmission": "8-Speed Automatic",
        "drivetrain": "4WD",
        "engine": "5.7L V8 HEMI",
        "images": ["https://images.unsplash.com/photo-1562911791-c7a04a9e4d6d?w=800&q=80"],
        "scraped_from_url": "https://example.com/vehicle3"
    },
    {
        "vin": "1G1YY22G375100001",
        "make": "Chevrolet",
        "model": "Camaro",
        "year": 2018,
        "mileage": 55000,
        "price": 24500.0,
        "dealer_name": "Austin Auto Group",
        "dealer_location": "Austin, TX",
        "exterior_color": "Yellow",
        "interior_color": "Black",
        "fuel_type": "Gasoline",
        "transmission": "6-Speed Manual",
        "drivetrain": "RWD",
        "engine": "6.2L V8",
        "images": ["https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800&q=80"],
        "scraped_from_url": "https://example.com/vehicle4"
    },
    {
        "vin": "JF1VA1A60M9820001",
        "make": "Subaru",
        "model": "WRX",
        "year": 2021,
        "mileage": 18000,
        "price": 29900.0,
        "dealer_name": "Dallas Premium Motors",
        "dealer_location": "Dallas, TX",
        "exterior_color": "Blue",
        "interior_color": "Black",
        "fuel_type": "Gasoline",
        "transmission": "6-Speed Manual",
        "drivetrain": "AWD",
        "engine": "2.0L Turbo",
        "images": ["https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=800&q=80"],
        "scraped_from_url": "https://example.com/vehicle5"
    },
    {
        "vin": "1FMCU9HD5KUA00001",
        "make": "Ford",
        "model": "Escape",
        "year": 2019,
        "mileage": 42000,
        "price": 21500.0,
        "dealer_name": "Houston Car Center",
        "dealer_location": "Houston, TX",
        "exterior_color": "White",
        "interior_color": "Gray",
        "fuel_type": "Gasoline",
        "transmission": "8-Speed Automatic",
        "drivetrain": "AWD",
        "engine": "2.0L EcoBoost",
        "images": ["https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800&q=80"],
        "scraped_from_url": "https://example.com/vehicle6"
    },
    {
        "vin": "1N4AL3AP9JC100001",
        "make": "Nissan",
        "model": "Altima",
        "year": 2018,
        "mileage": 58000,
        "price": 16900.0,
        "dealer_name": "Austin Auto Group",
        "dealer_location": "Austin, TX",
        "exterior_color": "Gray",
        "interior_color": "Beige",
        "fuel_type": "Gasoline",
        "transmission": "CVT",
        "drivetrain": "FWD",
        "engine": "2.5L 4-Cylinder",
        "images": ["https://images.unsplash.com/photo-1563720223185-11003d516935?w=800&q=80"],
        "scraped_from_url": "https://example.com/vehicle7"
    },
    {
        "vin": "5NPE34AF6JH000001",
        "make": "Hyundai",
        "model": "Sonata",
        "year": 2020,
        "mileage": 25000,
        "price": 22900.0,
        "dealer_name": "Dallas Premium Motors",
        "dealer_location": "Dallas, TX",
        "exterior_color": "Black",
        "interior_color": "Black",
        "fuel_type": "Gasoline",
        "transmission": "8-Speed Automatic",
        "drivetrain": "FWD",
        "engine": "2.5L 4-Cylinder",
        "images": ["https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800&q=80"],
        "scraped_from_url": "https://example.com/vehicle8"
    }
]

def create_dealers():
    """Create sample dealers"""
    print("Creating sample dealers...")
    for dealer in SAMPLE_DEALERS:
        try:
            response = requests.post(f"{API_URL}/dealers", json=dealer)
            if response.status_code == 200:
                print(f"✅ Created dealer: {dealer['name']}")
            else:
                print(f"❌ Failed to create dealer {dealer['name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating dealer {dealer['name']}: {str(e)}")

def create_vehicles():
    """Create sample vehicles"""
    print("Creating sample vehicles...")
    for vehicle in SAMPLE_VEHICLES:
        try:
            response = requests.post(f"{API_URL}/vehicles", json=vehicle)
            if response.status_code == 200:
                data = response.json()
                rating = data.get('deal_pulse_rating', 'Unknown')
                print(f"✅ Created vehicle: {vehicle['year']} {vehicle['make']} {vehicle['model']} - Deal Rating: {rating}")
            else:
                print(f"❌ Failed to create vehicle {vehicle['make']} {vehicle['model']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating vehicle {vehicle['make']} {vehicle['model']}: {str(e)}")

def main():
    print("🚗 Seeding Pulse Auto Market with sample data...")
    print(f"API URL: {API_URL}")
    
    # Check if API is accessible
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code != 200:
            print(f"❌ API not accessible: {response.status_code}")
            sys.exit(1)
        print("✅ API is accessible")
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        sys.exit(1)
    
    # Create data
    create_dealers()
    create_vehicles()
    
    # Get final stats
    try:
        response = requests.get(f"{API_URL}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"\n📊 Final Stats:")
            print(f"   Total Vehicles: {stats.get('total_vehicles', 0)}")
            print(f"   Total Dealers: {stats.get('total_dealers', 0)}")
            print(f"   Great Deals: {stats.get('deal_pulse_stats', {}).get('great_deals', 0)}")
    except Exception as e:
        print(f"❌ Error getting final stats: {str(e)}")
    
    print("\n🎉 Sample data seeding completed!")

if __name__ == "__main__":
    main()
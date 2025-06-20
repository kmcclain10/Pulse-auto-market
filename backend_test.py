#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
import uuid
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from frontend/.env
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
print(f"Testing API at: {API_URL}")

# Test data
TEST_VIN = "1FTFW1ET5DFC10312"  # 2013 Ford F-150
TEST_VEHICLE = {
    "vin": TEST_VIN,
    "make": "Ford",
    "model": "F-150",
    "year": 2013,
    "mileage": 75000,
    "price": 22500.0,
    "dealer_name": "Test Dealer",
    "dealer_location": "Test City, CA",
    "exterior_color": "Blue",
    "interior_color": "Gray",
    "fuel_type": "Gasoline",
    "transmission": "Automatic",
    "drivetrain": "4WD",
    "engine": "3.5L V6",
    "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
    "scraped_from_url": "https://www.ford.com/trucks/f150/2013/"
}

TEST_DEALER = {
    "name": "Test Dealer " + str(uuid.uuid4())[:8],
    "website_url": "https://www.cargurus.com",
    "location": "Test City, CA",
    "scraper_adapter": "generic"
}

# Helper functions
def print_test_header(test_name):
    print("\n" + "=" * 80)
    print(f"TESTING: {test_name}")
    print("=" * 80)

def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def assert_status_code(response, expected_code):
    if response.status_code != expected_code:
        print(f"❌ Expected status code {expected_code}, got {response.status_code}")
        return False
    print(f"✅ Status code {expected_code} as expected")
    return True

def assert_json_response(response):
    try:
        response.json()
        print("✅ Response is valid JSON")
        return True
    except:
        print("❌ Response is not valid JSON")
        return False

def assert_field_exists(data, field):
    if field in data:
        print(f"✅ Field '{field}' exists in response")
        return True
    print(f"❌ Field '{field}' does not exist in response")
    return False

def assert_field_equals(data, field, expected_value):
    if field in data and data[field] == expected_value:
        print(f"✅ Field '{field}' equals '{expected_value}'")
        return True
    print(f"❌ Field '{field}' does not equal '{expected_value}', got '{data.get(field)}'")
    return False

def assert_field_type(data, field, expected_type):
    if field == "":
        if isinstance(data, expected_type):
            print(f"✅ Response is of type {expected_type.__name__}")
            return True
        print(f"❌ Response is not of type {expected_type.__name__}, got {type(data).__name__}")
        return False
    elif field in data and isinstance(data[field], expected_type):
        print(f"✅ Field '{field}' is of type {expected_type.__name__}")
        return True
    print(f"❌ Field '{field}' is not of type {expected_type.__name__}, got {type(data.get(field, None)).__name__}")
    return False

# Test functions
def test_health_check():
    print_test_header("Health Check (GET /api/)")
    response = requests.get(f"{API_URL}/")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "message")
    
    return success

def test_create_vehicle():
    print_test_header("Create Vehicle (POST /api/vehicles)")
    response = requests.post(f"{API_URL}/vehicles", json=TEST_VEHICLE)
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "id")
    success &= assert_field_exists(data, "vin")
    success &= assert_field_exists(data, "make")
    success &= assert_field_exists(data, "model")
    success &= assert_field_exists(data, "year")
    success &= assert_field_exists(data, "price")
    success &= assert_field_exists(data, "deal_pulse_rating")
    success &= assert_field_exists(data, "market_price_analysis")
    
    # Check new image-related fields
    success &= assert_field_exists(data, "images")
    success &= assert_field_exists(data, "image_count")
    
    # Check if VIN matches
    success &= assert_field_equals(data, "vin", TEST_VEHICLE["vin"])
    
    # Store the vehicle ID for later tests
    global created_vehicle_id
    created_vehicle_id = data["id"]
    
    return success

def test_get_vehicles():
    print_test_header("Get Vehicles (GET /api/vehicles)")
    response = requests.get(f"{API_URL}/vehicles")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_type(data, "", list)
    
    if len(data) > 0:
        vehicle = data[0]
        success &= assert_field_exists(vehicle, "id")
        success &= assert_field_exists(vehicle, "vin")
        success &= assert_field_exists(vehicle, "make")
        success &= assert_field_exists(vehicle, "model")
        success &= assert_field_exists(vehicle, "year")
        success &= assert_field_exists(vehicle, "price")
        
        # Check new image-related fields
        success &= assert_field_exists(vehicle, "images")
        success &= assert_field_exists(vehicle, "image_count")
    
    return success

def test_get_vehicle_by_vin():
    print_test_header(f"Get Vehicle by VIN (GET /api/vehicles/{TEST_VIN})")
    response = requests.get(f"{API_URL}/vehicles/{TEST_VIN}")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "id")
    success &= assert_field_exists(data, "vin")
    success &= assert_field_equals(data, "vin", TEST_VIN)
    
    return success

def test_get_vehicle_by_invalid_vin():
    print_test_header("Get Vehicle by Invalid VIN (GET /api/vehicles/INVALID)")
    response = requests.get(f"{API_URL}/vehicles/INVALID_VIN_12345")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 404)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "detail")
    
    return success

def test_get_available_makes():
    print_test_header("Get Available Makes (GET /api/vehicles/search/makes)")
    response = requests.get(f"{API_URL}/vehicles/search/makes")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "makes")
    success &= assert_field_type(data, "makes", list)
    
    return success

def test_get_available_models():
    print_test_header("Get Available Models (GET /api/vehicles/search/models)")
    response = requests.get(f"{API_URL}/vehicles/search/models")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "models")
    success &= assert_field_type(data, "models", list)
    
    # Test with make filter
    print("\nTesting with make filter:")
    response = requests.get(f"{API_URL}/vehicles/search/models?make=Ford")
    print_response(response)
    
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "models")
    success &= assert_field_type(data, "models", list)
    
    return success

def test_create_dealer():
    print_test_header("Create Dealer (POST /api/dealers)")
    response = requests.post(f"{API_URL}/dealers", json=TEST_DEALER)
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "id")
    success &= assert_field_exists(data, "name")
    success &= assert_field_exists(data, "website_url")
    success &= assert_field_exists(data, "location")
    success &= assert_field_exists(data, "scraper_adapter")
    
    # Check if name matches
    success &= assert_field_equals(data, "name", TEST_DEALER["name"])
    
    # Store the dealer ID for later tests
    global created_dealer_id
    created_dealer_id = data["id"]
    
    return success

def test_get_dealers():
    print_test_header("Get Dealers (GET /api/dealers)")
    response = requests.get(f"{API_URL}/dealers")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_type(data, "", list)
    
    if len(data) > 0:
        dealer = data[0]
        success &= assert_field_exists(dealer, "id")
        success &= assert_field_exists(dealer, "name")
        success &= assert_field_exists(dealer, "website_url")
        success &= assert_field_exists(dealer, "location")
    
    return success

def test_trigger_scraping():
    print_test_header(f"Trigger Scraping (POST /api/scrape/dealer/{created_dealer_id})")
    response = requests.post(f"{API_URL}/scrape/dealer/{created_dealer_id}")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "message")
    success &= assert_field_exists(data, "vehicles_found")
    success &= assert_field_exists(data, "vehicles_added")
    success &= assert_field_exists(data, "dealer")
    
    # Check new image-related field
    success &= assert_field_exists(data, "images_scraped")
    
    return success

def test_get_scrape_jobs():
    print_test_header("Get Scrape Jobs (GET /api/scrape/jobs)")
    response = requests.get(f"{API_URL}/scrape/jobs")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_type(data, "", list)
    
    if len(data) > 0:
        job = data[0]
        success &= assert_field_exists(job, "id")
        success &= assert_field_exists(job, "dealer_id")
        success &= assert_field_exists(job, "status")
        success &= assert_field_exists(job, "vehicles_found")
    
    return success

def test_get_stats():
    print_test_header("Get Stats (GET /api/stats)")
    response = requests.get(f"{API_URL}/stats")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "total_vehicles")
    success &= assert_field_exists(data, "total_dealers")
    success &= assert_field_exists(data, "deal_pulse_stats")
    success &= assert_field_exists(data, "top_makes")
    
    # Check deal_pulse_stats structure
    deal_pulse_stats = data["deal_pulse_stats"]
    success &= assert_field_exists(deal_pulse_stats, "great_deals")
    success &= assert_field_exists(deal_pulse_stats, "fair_prices")
    success &= assert_field_exists(deal_pulse_stats, "high_prices")
    
    return success

def test_vehicle_filtering():
    print_test_header("Vehicle Filtering (GET /api/vehicles with filters)")
    
    # Test make filter
    print("\nTesting make filter:")
    response = requests.get(f"{API_URL}/vehicles?make=Ford")
    print_response(response)
    success = assert_status_code(response, 200) and assert_json_response(response)
    
    # Test model filter
    print("\nTesting model filter:")
    response = requests.get(f"{API_URL}/vehicles?model=F-150")
    print_response(response)
    success &= assert_status_code(response, 200) and assert_json_response(response)
    
    # Test price range filter
    print("\nTesting price range filter:")
    response = requests.get(f"{API_URL}/vehicles?price_min=10000&price_max=50000")
    print_response(response)
    success &= assert_status_code(response, 200) and assert_json_response(response)
    
    # Test year range filter
    print("\nTesting year range filter:")
    response = requests.get(f"{API_URL}/vehicles?year_min=2010&year_max=2020")
    print_response(response)
    success &= assert_status_code(response, 200) and assert_json_response(response)
    
    # Test mileage filter
    print("\nTesting mileage filter:")
    response = requests.get(f"{API_URL}/vehicles?mileage_max=100000")
    print_response(response)
    success &= assert_status_code(response, 200) and assert_json_response(response)
    
    # Test location filter
    print("\nTesting location filter:")
    response = requests.get(f"{API_URL}/vehicles?location=Test")
    print_response(response)
    success &= assert_status_code(response, 200) and assert_json_response(response)
    
    # Test combined filters
    print("\nTesting combined filters:")
    response = requests.get(f"{API_URL}/vehicles?make=Ford&year_min=2010&price_max=50000&mileage_max=100000")
    print_response(response)
    success &= assert_status_code(response, 200) and assert_json_response(response)
    
    return success

def test_get_vehicle_images():
    print_test_header(f"Get Vehicle Images (GET /api/vehicles/{TEST_VIN}/images)")
    response = requests.get(f"{API_URL}/vehicles/{TEST_VIN}/images")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "vin")
    success &= assert_field_exists(data, "images")
    success &= assert_field_exists(data, "total_count")
    
    return success

def test_scrape_vehicle_images():
    print_test_header(f"Scrape Vehicle Images (POST /api/vehicles/{TEST_VIN}/scrape-images)")
    response = requests.post(f"{API_URL}/vehicles/{TEST_VIN}/scrape-images")
    print_response(response)
    
    # This might return 200 even if AWS credentials are missing
    # We're testing the API endpoint, not the actual scraping functionality
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "message")
    success &= assert_field_exists(data, "vin")
    
    return success

def test_get_image_stats():
    print_test_header("Get Image Stats (GET /api/images/stats)")
    response = requests.get(f"{API_URL}/images/stats")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "total_image_records")
    success &= assert_field_exists(data, "vehicles_with_images")
    success &= assert_field_exists(data, "average_images_per_vehicle")
    
    return success

def test_cleanup_images():
    print_test_header("Cleanup Images (POST /api/images/cleanup)")
    response = requests.post(f"{API_URL}/images/cleanup")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "message")
    success &= assert_field_exists(data, "cleaned_count")
    
    return success

def test_enhanced_stats():
    print_test_header("Enhanced Stats (GET /api/stats)")
    response = requests.get(f"{API_URL}/stats")
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "vehicles_with_images")
    success &= assert_field_exists(data, "image_coverage_percentage")
    
    return success

def test_enhanced_dealer_creation():
    print_test_header("Enhanced Dealer Creation (POST /api/dealers)")
    
    # Create a dealer with image scraping enabled
    enhanced_dealer = {
        "name": "Enhanced Test Dealer " + str(uuid.uuid4())[:8],
        "website_url": "https://www.cargurus.com",
        "location": "Test City, CA",
        "scraper_adapter": "generic",
        "image_scraping_enabled": True
    }
    
    response = requests.post(f"{API_URL}/dealers", json=enhanced_dealer)
    print_response(response)
    
    success = True
    success &= assert_status_code(response, 200)
    success &= assert_json_response(response)
    
    data = response.json()
    success &= assert_field_exists(data, "id")
    success &= assert_field_exists(data, "image_scraping_enabled")
    success &= assert_field_equals(data, "image_scraping_enabled", True)
    
    return success

def run_all_tests():
    test_results = {}
    
    # Initialize global variables
    global created_vehicle_id, created_dealer_id
    created_vehicle_id = None
    created_dealer_id = None
    
    # Run tests
    test_results["Health Check"] = test_health_check()
    test_results["Create Vehicle"] = test_create_vehicle()
    test_results["Get Vehicles"] = test_get_vehicles()
    test_results["Get Vehicle by VIN"] = test_get_vehicle_by_vin()
    test_results["Get Vehicle by Invalid VIN"] = test_get_vehicle_by_invalid_vin()
    test_results["Get Available Makes"] = test_get_available_makes()
    test_results["Get Available Models"] = test_get_available_models()
    test_results["Create Dealer"] = test_create_dealer()
    test_results["Get Dealers"] = test_get_dealers()
    
    # Only run scraping test if dealer was created successfully
    if created_dealer_id:
        test_results["Trigger Scraping"] = test_trigger_scraping()
    else:
        test_results["Trigger Scraping"] = False
        print("Skipping scraping test because dealer creation failed")
    
    test_results["Get Scrape Jobs"] = test_get_scrape_jobs()
    test_results["Get Stats"] = test_get_stats()
    test_results["Vehicle Filtering"] = test_vehicle_filtering()
    
    # New image-related tests
    test_results["Get Vehicle Images"] = test_get_vehicle_images()
    test_results["Scrape Vehicle Images"] = test_scrape_vehicle_images()
    test_results["Get Image Stats"] = test_get_image_stats()
    test_results["Cleanup Images"] = test_cleanup_images()
    test_results["Enhanced Stats"] = test_enhanced_stats()
    test_results["Enhanced Dealer Creation"] = test_enhanced_dealer_creation()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        if not result:
            all_passed = False
        print(f"{test_name}: {status}")
    
    print("\nOVERALL RESULT:", "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
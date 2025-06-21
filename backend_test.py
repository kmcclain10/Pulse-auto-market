#!/usr/bin/env python3
import requests
import time
import json
import os
import sys
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://d87d82a9-9679-4501-a166-e2b87606b639.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Test dealer URLs
TEST_DEALER_URLS = [
    "https://memorymotorstn.com/",
    "https://tnautotrade.com/",
    "https://usautomotors.com/"
]

def print_separator():
    print("\n" + "="*80 + "\n")

def test_health_check():
    """Test the API health check endpoint"""
    print("Testing API Health Check...")
    try:
        response = requests.get(f"{API_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and "message" in response.json():
            print("✅ Health check endpoint is working")
            return True
        else:
            print("❌ Health check endpoint is not working properly")
            return False
    except Exception as e:
        print(f"❌ Error testing health check endpoint: {str(e)}")
        return False

def test_get_scraping_jobs():
    """Test the get scraping jobs endpoint"""
    print("Testing Get Scraping Jobs...")
    try:
        response = requests.get(f"{API_URL}/scrape/jobs")
        print(f"Status Code: {response.status_code}")
        print(f"Found {len(response.json())} scraping jobs")
        
        if response.status_code == 200:
            print("✅ Get scraping jobs endpoint is working")
            return True
        else:
            print("❌ Get scraping jobs endpoint is not working properly")
            return False
    except Exception as e:
        print(f"❌ Error testing get scraping jobs endpoint: {str(e)}")
        return False

def test_get_vehicles():
    """Test the get vehicles endpoint"""
    print("Testing Get Vehicles...")
    try:
        response = requests.get(f"{API_URL}/vehicles")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Found {data.get('total', 0)} vehicles")
        
        if response.status_code == 200 and "vehicles" in data:
            print("✅ Get vehicles endpoint is working")
            return True
        else:
            print("❌ Get vehicles endpoint is not working properly")
            return False
    except Exception as e:
        print(f"❌ Error testing get vehicles endpoint: {str(e)}")
        return False

def test_get_dealer_stats():
    """Test the get dealer statistics endpoint"""
    print("Testing Get Dealer Statistics...")
    try:
        response = requests.get(f"{API_URL}/dealers/stats")
        print(f"Status Code: {response.status_code}")
        print(f"Found statistics for {len(response.json())} dealers")
        
        if response.status_code == 200:
            print("✅ Get dealer statistics endpoint is working")
            return True
        else:
            print("❌ Get dealer statistics endpoint is not working properly")
            return False
    except Exception as e:
        print(f"❌ Error testing get dealer statistics endpoint: {str(e)}")
        return False

def test_start_scraping_job():
    """Test starting a scraping job"""
    print("Testing Start Scraping Job...")
    try:
        payload = {
            "dealer_urls": TEST_DEALER_URLS,
            "max_vehicles_per_dealer": 5  # Limit to 5 vehicles per dealer for testing
        }
        
        response = requests.post(f"{API_URL}/scrape/start", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and "job_id" in response.json():
            job_id = response.json()["job_id"]
            print(f"✅ Start scraping job endpoint is working. Job ID: {job_id}")
            return job_id
        else:
            print("❌ Start scraping job endpoint is not working properly")
            return None
    except Exception as e:
        print(f"❌ Error testing start scraping job endpoint: {str(e)}")
        return None

def test_scraping_job_status(job_id):
    """Test getting the status of a scraping job"""
    print(f"Testing Scraping Job Status for job {job_id}...")
    try:
        response = requests.get(f"{API_URL}/scrape/status/{job_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and "status" in response.json():
            print(f"✅ Get scraping job status endpoint is working")
            return response.json()
        else:
            print("❌ Get scraping job status endpoint is not working properly")
            return None
    except Exception as e:
        print(f"❌ Error testing get scraping job status endpoint: {str(e)}")
        return None

def test_full_workflow():
    """Test the full workflow of starting a job and monitoring progress"""
    print_separator()
    print("TESTING FULL WORKFLOW")
    print_separator()
    
    # Start a scraping job
    job_id = test_start_scraping_job()
    if not job_id:
        print("❌ Full workflow test failed: Could not start scraping job")
        return False
    
    # Monitor job progress
    max_attempts = 10
    attempts = 0
    completed = False
    
    print("\nMonitoring job progress...")
    while attempts < max_attempts and not completed:
        attempts += 1
        print(f"\nCheck {attempts}/{max_attempts}:")
        
        status = test_scraping_job_status(job_id)
        if not status:
            print("❌ Could not get job status")
            time.sleep(5)
            continue
        
        if status["status"] in ["completed", "failed"]:
            completed = True
            print(f"Job {job_id} {status['status']} with {status.get('vehicles_scraped', 0)} vehicles scraped")
        else:
            print(f"Job status: {status['status']}, progress: {status.get('progress', 0)}%, vehicles scraped: {status.get('vehicles_scraped', 0)}")
            time.sleep(10)  # Wait 10 seconds before checking again
    
    # Check if we have vehicles
    print("\nChecking for scraped vehicles...")
    response = requests.get(f"{API_URL}/vehicles")
    if response.status_code == 200:
        data = response.json()
        total_vehicles = data.get("total", 0)
        print(f"Found {total_vehicles} vehicles in the database")
        
        if total_vehicles > 0:
            # Check a sample vehicle
            sample_vehicle = data["vehicles"][0]
            print("\nSample vehicle data:")
            for key in ["make", "model", "year", "price", "mileage", "dealer_name"]:
                if key in sample_vehicle:
                    print(f"  {key}: {sample_vehicle[key]}")
            
            # Check if photos were scraped
            photo_count = sample_vehicle.get("photo_count", 0)
            print(f"  photo_count: {photo_count}")
            
            if photo_count > 0:
                print("✅ Photos were successfully scraped and stored")
            else:
                print("⚠️ No photos were scraped for this vehicle")
        
        # Check dealer stats
        print("\nChecking dealer statistics...")
        response = requests.get(f"{API_URL}/dealers/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"Found statistics for {len(stats)} dealers")
            
            if len(stats) > 0:
                print("✅ Dealer statistics are available")
            else:
                print("⚠️ No dealer statistics available")
        
        return total_vehicles > 0
    else:
        print("❌ Could not retrieve vehicles")
        return False

def run_all_tests():
    """Run all tests and return results"""
    results = {}
    
    print_separator()
    print("STARTING API TESTS")
    print(f"Testing against API URL: {API_URL}")
    print_separator()
    
    # Test individual endpoints
    results["health_check"] = test_health_check()
    print_separator()
    
    results["get_scraping_jobs"] = test_get_scraping_jobs()
    print_separator()
    
    results["get_vehicles"] = test_get_vehicles()
    print_separator()
    
    results["get_dealer_stats"] = test_get_dealer_stats()
    print_separator()
    
    # Test full workflow
    results["full_workflow"] = test_full_workflow()
    
    # Print summary
    print_separator()
    print("TEST RESULTS SUMMARY")
    print_separator()
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    print_separator()
    if all_passed:
        print("🎉 ALL TESTS PASSED! The car scraper API is working correctly.")
    else:
        print("❌ SOME TESTS FAILED. Please check the logs for details.")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
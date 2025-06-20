#!/usr/bin/env python3
"""
Test AI CRM and Desking Tool functionality
"""
import requests
import json
import uuid
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from frontend/.env
load_dotenv(Path(__file__).parent.parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"

def test_ai_crm_features():
    """Test AI CRM functionality"""
    print("\n" + "="*60)
    print("TESTING AI CRM FEATURES")
    print("="*60)
    
    # Test 1: Create a lead inquiry
    print("\n1. Testing Lead Creation...")
    lead_data = {
        "customer_name": "John Smith",
        "customer_email": "john.smith@email.com",
        "customer_phone": "(555) 123-4567",
        "vehicle_vin": "1FTFW1ET5DFC10312",  # Use existing test VIN
        "message": "I'm interested in this F-150. What's your best price? I'm ready to buy this weekend and have financing pre-approved.",
        "dealer_id": "test-dealer-123",
        "dealer_name": "Test Motors"
    }
    
    response = requests.post(f"{API_URL}/leads", json=lead_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        lead = response.json()
        print(f"✅ Lead created: ID={lead['id']}")
        print(f"   Lead Score: {lead['lead_score']}")
        print(f"   Inquiry Type: {lead['inquiry_type']}")
        print(f"   AI Response Generated: {'Yes' if lead['ai_response'] else 'No'}")
        if lead['ai_response']:
            print(f"   AI Response Preview: {lead['ai_response'][:100]}...")
        
        lead_id = lead['id']
        conversation_id = lead['conversation_id']
        
        # Test 2: Get conversation history
        print(f"\n2. Testing Conversation History...")
        response = requests.get(f"{API_URL}/leads/{lead_id}/conversation")
        if response.status_code == 200:
            conversation = response.json()
            print(f"✅ Conversation retrieved: {len(conversation)} messages")
            for msg in conversation:
                print(f"   {msg['sender'].title()}: {msg['message'][:50]}...")
        
        # Test 3: Approve AI response
        print(f"\n3. Testing AI Response Approval...")
        response = requests.post(f"{API_URL}/leads/{lead_id}/approve-response", 
                               json={"approved": True})
        if response.status_code == 200:
            print(f"✅ AI response approved")
        
        # Test 4: Get dealer CRM stats
        print(f"\n4. Testing CRM Stats...")
        response = requests.get(f"{API_URL}/crm/dealer/test-dealer-123/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ CRM Stats retrieved:")
            print(f"   Total Leads: {stats.get('total_leads', 0)}")
            print(f"   Conversion Rate: {stats.get('conversion_rate', 0)}%")
            print(f"   AI Responses Generated: {stats.get('ai_responses_generated', 0)}")
    else:
        print(f"❌ Lead creation failed: {response.text}")

def test_desking_features():
    """Test Desking Tool functionality"""
    print("\n" + "="*60)
    print("TESTING DESKING TOOL FEATURES")
    print("="*60)
    
    # Test 1: Generate payment grid
    print("\n1. Testing Payment Grid Generation...")
    params = {
        "vehicle_price": 35000,
        "down_payment": 5000,
        "trade_value": 8000,
        "tax_rate": 8.25
    }
    
    response = requests.post(f"{API_URL}/deals/payment-grid", json=params)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        grid = response.json()
        print(f"✅ Payment grid generated")
        print(f"   Vehicle Price: ${grid['vehicle_price']:,.2f}")
        print(f"   Amount Financed: ${grid['amount_financed']:,.2f}")
        print(f"   Sample payments:")
        
        # Show sample payments
        for term in ['48', '60', '72']:
            if term in grid['grid']:
                rate_5_99 = grid['grid'][term].get('5.99', 0)
                print(f"     {term} months @ 5.99% APR: ${rate_5_99:,.2f}/month")
    else:
        print(f"❌ Payment grid failed: {response.text}")
    
    # Test 2: Create a deal calculation
    print("\n2. Testing Deal Calculation...")
    deal_data = {
        "dealer_id": "test-dealer-123",
        "vehicle_vin": "1FTFW1ET5DFC10312",
        "customer_name": "Jane Doe",
        "deal_type": "finance",
        "vehicle_price": 35000,
        "dealer_discount": 2000,
        "rebates": 1000,
        "finance_terms": {
            "loan_amount": 27000,
            "interest_rate": 5.99,
            "term_months": 60,
            "down_payment": 5000
        },
        "tax_info": {
            "state": "TX",
            "zip_code": "78701",
            "tax_rate": 8.25,
            "doc_fee": 199
        },
        "fi_products": []
    }
    
    response = requests.post(f"{API_URL}/deals", json=deal_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        deal = response.json()
        print(f"✅ Deal calculated: ID={deal['id']}")
        print(f"   Monthly Payment: ${deal['monthly_payment']:,.2f}")
        print(f"   Total Cost: ${deal['total_cost']:,.2f}")
        print(f"   Dealer Profit: ${deal['dealer_profit']:,.2f}")
        
        deal_id = deal['id']
        
        # Test 3: Get F&I products
        print(f"\n3. Testing F&I Products...")
        response = requests.get(f"{API_URL}/fi-products/dealer/test-dealer-123?vehicle_price=35000&term_months=60")
        if response.status_code == 200:
            products = response.json()
            print(f"✅ F&I Products retrieved: {len(products['products'])} products")
            for product in products['products']:
                print(f"   {product['name']}: ${product['customer_price']:,.2f}")
        
        # Test 4: Generate deal proposal
        print(f"\n4. Testing Deal Proposal...")
        response = requests.get(f"{API_URL}/deals/{deal_id}/proposal")
        if response.status_code == 200:
            proposal = response.json()
            print(f"✅ Deal proposal generated")
            print(f"   Customer: {proposal['customer_name']}")
            print(f"   Vehicle: {proposal['vehicle']['year']} {proposal['vehicle']['make']} {proposal['vehicle']['model']}")
            print(f"   Monthly Payment: {proposal['payment_info']['monthly_payment']}")
    else:
        print(f"❌ Deal calculation failed: {response.text}")

def test_payment_calculator():
    """Test standalone payment calculator"""
    print("\n3. Testing Payment Calculator...")
    params = {
        "principal": 30000,
        "rate": 5.99,
        "months": 60,
        "frequency": "monthly"
    }
    
    response = requests.post(f"{API_URL}/deals/calculate-payment", json=params)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Payment calculated:")
        print(f"   Loan Amount: ${result['principal']:,.2f}")
        print(f"   Term: {result['months']} months @ {result['rate']}% APR")
        print(f"   Monthly Payment: ${result['payment']:,.2f}")
    else:
        print(f"❌ Payment calculation failed: {response.text}")

def test_vehicle_inquiry():
    """Test vehicle inquiry that triggers AI CRM"""
    print("\n4. Testing Vehicle Inquiry (AI CRM Integration)...")
    inquiry_data = {
        "customer_name": "Mike Johnson",
        "customer_email": "mike.j@email.com",
        "customer_phone": "(555) 987-6543",
        "message": "Is this truck still available? I'd like to schedule a test drive for tomorrow.",
        "dealer_id": "test-dealer-123",
        "dealer_name": "Test Motors"
    }
    
    response = requests.post(f"{API_URL}/vehicles/1FTFW1ET5DFC10312/inquire", json=inquiry_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Vehicle inquiry processed:")
        print(f"   Lead ID: {result['lead_id']}")
        print(f"   Lead Score: {result['lead_score']}")
        print(f"   Inquiry Type: {result['inquiry_type']}")
        print(f"   AI Response Generated: {result['ai_response_generated']}")
    else:
        print(f"❌ Vehicle inquiry failed: {response.text}")

def main():
    print("🤖 TESTING AI CRM & ADVANCED DESKING TOOLS")
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
    
    # Run tests
    test_ai_crm_features()
    test_desking_features()
    test_payment_calculator()
    test_vehicle_inquiry()
    
    print("\n" + "="*60)
    print("🎉 AI CRM & DESKING TOOL TESTING COMPLETED!")
    print("="*60)
    print("\nNote: Some features require OpenAI API key to be configured.")
    print("      Tests show API structure and basic functionality.")

if __name__ == "__main__":
    main()
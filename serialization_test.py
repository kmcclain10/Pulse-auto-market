import requests
import json
import base64

# Get the backend URL from environment variable
BACKEND_URL = "https://a8223785-4b39-409d-a292-0a964f08dd99.preview.emergentagent.com/api"

def test_objectid_serialization():
    """Test ObjectId serialization in API responses"""
    print("Starting ObjectId serialization test...")
    
    # 1. Create a new deal
    deal_data = {
        "customer": {
            "first_name": "Serialization",
            "last_name": "Test",
            "email": "serialization.test@example.com",
            "phone": "555-123-4567",
            "address": "123 Test St",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94107",
            "credit_score": 750
        },
        "vehicle": {
            "vin": "1HGCM82633A654321",
            "year": 2023,
            "make": "Honda",
            "model": "Accord",
            "trim": "Touring",
            "condition": "new",
            "mileage": 100,
            "msrp": 38000.00,
            "invoice_price": 35000.00,
            "selling_price": 36500.00
        },
        "salesperson": "Serialization Agent"
    }
    
    print("Creating deal...")
    response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
    
    if response.status_code != 200:
        print(f"Failed to create deal: {response.text}")
        return
    
    deal_id = response.json()["id"]
    print(f"Deal created with ID: {deal_id}")
    
    # 2. Get all deals to check serialization
    print("Getting all deals...")
    response = requests.get(f"{BACKEND_URL}/deals")
    
    if response.status_code != 200:
        print(f"Failed to get deals: {response.text}")
        return
    
    deals = response.json()
    print(f"Retrieved {len(deals)} deals")
    
    # 3. Get specific deal
    print(f"Getting deal {deal_id}...")
    response = requests.get(f"{BACKEND_URL}/deals/{deal_id}")
    
    if response.status_code != 200:
        print(f"Failed to get deal: {response.text}")
        return
    
    deal = response.json()
    
    # 4. Check for any ObjectId serialization issues
    try:
        # Try to serialize the deal to JSON
        deal_json = json.dumps(deal)
        print("Successfully serialized deal to JSON")
        
        # Try to deserialize it back
        deal_dict = json.loads(deal_json)
        print("Successfully deserialized JSON back to dict")
        
        print("✅ ObjectId serialization test passed!")
    except Exception as e:
        print(f"❌ Serialization error: {str(e)}")
        return

def test_enterprise_workflow():
    """Test the complete enterprise workflow integration"""
    print("Starting enterprise workflow test...")
    
    # 1. Create a deal
    deal_data = {
        "customer": {
            "first_name": "Enterprise",
            "last_name": "Workflow",
            "email": "enterprise.workflow@example.com",
            "phone": "555-987-6543",
            "address": "789 Enterprise Ave",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "credit_score": 780
        },
        "vehicle": {
            "vin": "WAUYGAFC1CN123456",
            "year": 2023,
            "make": "Audi",
            "model": "A6",
            "trim": "Premium Plus",
            "condition": "new",
            "mileage": 50,
            "msrp": 58000.00,
            "invoice_price": 54000.00,
            "selling_price": 56000.00
        },
        "salesperson": "Enterprise Agent"
    }
    
    print("Creating deal...")
    response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
    
    if response.status_code != 200:
        print(f"Failed to create deal: {response.text}")
        return
    
    deal_id = response.json()["id"]
    print(f"Deal created with ID: {deal_id}")
    
    # 2. Add finance terms
    finance_data = {
        "loan_amount": 50000.00,
        "apr": 3.99,
        "term_months": 60,
        "down_payment": 6000.00
    }
    
    print("Adding finance terms...")
    response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/finance", json=finance_data)
    
    if response.status_code != 200:
        print(f"Failed to add finance terms: {response.text}")
        return
    
    print("Finance terms added successfully")
    
    # 3. Get F&I menu
    print("Getting F&I menu...")
    response = requests.get(f"{BACKEND_URL}/deals/{deal_id}/menu")
    
    if response.status_code != 200:
        print(f"Failed to get F&I menu: {response.text}")
        return
    
    menu = response.json()
    
    # Find Premium 60 months VSC
    vsc_id = None
    for vsc in menu["vsc_options"]:
        if vsc["coverage_type"] == "premium" and vsc["term"] == "60_months":
            vsc_id = vsc["id"]
            break
    
    if not vsc_id:
        print("Could not find Premium 60 months VSC option")
        return
    
    print(f"Found VSC option with ID: {vsc_id}")
    
    # 4. Select F&I products
    selection_data = {
        "deal_id": deal_id,
        "selected_vsc_id": vsc_id,
        "include_gap": True
    }
    
    print("Selecting F&I products...")
    response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/menu-selection", json=selection_data)
    
    if response.status_code != 200:
        print(f"Failed to select F&I products: {response.text}")
        return
    
    print("F&I products selected successfully")
    
    # 5. Get final deal
    print("Getting final deal...")
    response = requests.get(f"{BACKEND_URL}/deals/{deal_id}")
    
    if response.status_code != 200:
        print(f"Failed to get final deal: {response.text}")
        return
    
    final_deal = response.json()
    
    # Verify all components are present
    assert final_deal["finance_terms"] is not None
    assert final_deal["selected_vsc"] == vsc_id
    assert final_deal["gap_option"] is not None
    
    print("✅ Enterprise workflow integration test passed!")
    print("\n--- Enterprise Deal Summary ---")
    print(f"Customer: {final_deal['customer']['first_name']} {final_deal['customer']['last_name']}")
    print(f"Vehicle: {final_deal['vehicle']['year']} {final_deal['vehicle']['make']} {final_deal['vehicle']['model']}")
    print(f"Selling Price: ${final_deal['vehicle']['selling_price']:.2f}")
    print(f"F&I Products: ${final_deal['total_fi_products']:.2f}")
    print(f"Total Deal Amount: ${final_deal['total_deal_amount']:.2f}")
    print("-----------------------------")

if __name__ == "__main__":
    test_objectid_serialization()
    print("\n" + "="*50 + "\n")
    test_enterprise_workflow()
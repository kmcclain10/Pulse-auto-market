import requests
import json
import base64

# Get the backend URL from environment variable
BACKEND_URL = "https://a8223785-4b39-409d-a292-0a964f08dd99.preview.emergentagent.com/api"

# Test data for enterprise customer
test_enterprise_customer = {
    "first_name": "Enterprise",
    "last_name": "Test",
    "email": "enterprise.test@example.com",
    "phone": "555-987-6543",
    "address": "789 Corporate Blvd",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94107",
    "ssn_last_four": "9876",
    "credit_score": 750
}

# Test data for enterprise vehicle
test_enterprise_vehicle = {
    "vin": "5UXWX7C5*BA123456",
    "year": 2023,
    "make": "BMW",
    "model": "X5",
    "trim": "xDrive40i",
    "condition": "new",
    "mileage": 150,
    "msrp": 65000.00,
    "invoice_price": 60000.00,
    "selling_price": 45000.00
}

def test_document_generation():
    """Test document generation with fixed ObjectId serialization"""
    print("Starting document generation test...")
    
    # Create a new deal for document testing
    deal_data = {
        "customer": test_enterprise_customer,
        "vehicle": test_enterprise_vehicle,
        "salesperson": "Document Test Agent"
    }
    
    print("Creating deal...")
    response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
    print(f"Create deal response: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Failed to create deal: {response.text}")
        return
    
    deal_id = response.json()["id"]
    print(f"Deal created with ID: {deal_id}")
    
    # Add finance terms to the deal
    finance_data = {
        "loan_amount": 40000.00,
        "apr": 4.99,
        "term_months": 60,
        "down_payment": 5000.00
    }
    
    print("Adding finance terms...")
    response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/finance", json=finance_data)
    print(f"Add finance response: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Failed to add finance terms: {response.text}")
        return
    
    # Generate documents
    document_request = {
        "document_types": [
            "purchase_agreement",
            "odometer_disclosure",
            "truth_in_lending",
            "bill_of_sale"
        ]
    }
    
    print("Generating documents...")
    response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/documents/generate", json=document_request)
    print(f"Document generation response: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Document generation failed: {response.text}")
        return
    
    result = response.json()
    print(f"Document generation result: {json.dumps(result, indent=2)}")
    
    if "documents" not in result:
        print("No documents in response")
        return
    
    print(f"Generated {len(result['documents'])} documents")
    
    # Get the first document ID
    document_id = result["documents"][0]["id"]
    
    # Verify documents were added to the deal
    print("Verifying documents were added to the deal...")
    response = requests.get(f"{BACKEND_URL}/deals/{deal_id}")
    
    if response.status_code != 200:
        print(f"Failed to get deal: {response.text}")
        return
    
    deal = response.json()
    print(f"Deal has {len(deal['documents'])} documents")
    print(f"docs_generated flag: {deal['docs_generated']}")
    
    # Test retrieving documents for the deal
    print("Getting all documents for the deal...")
    response = requests.get(f"{BACKEND_URL}/deals/{deal_id}/documents")
    
    if response.status_code != 200:
        print(f"Failed to get documents: {response.text}")
        return
    
    documents = response.json()
    print(f"Retrieved {len(documents)} documents")
    
    # Test retrieving PDF content
    print(f"Getting PDF content for document {document_id}...")
    response = requests.get(f"{BACKEND_URL}/documents/{document_id}/pdf")
    
    if response.status_code != 200:
        print(f"Failed to get PDF content: {response.text}")
        return
    
    pdf_result = response.json()
    
    if "pdf_content" not in pdf_result:
        print("No PDF content in response")
        return
    
    pdf_content = pdf_result["pdf_content"]
    print(f"PDF content length: {len(pdf_content)}")
    
    # Verify it's a valid base64 encoded PDF
    try:
        pdf_bytes = base64.b64decode(pdf_content)
        if pdf_bytes[:4] == b'%PDF':
            print("Valid PDF content confirmed")
        else:
            print(f"Invalid PDF header: {pdf_bytes[:20]}")
    except Exception as e:
        print(f"Error decoding PDF: {str(e)}")
        return
    
    print("✅ Document generation test passed successfully!")

if __name__ == "__main__":
    test_document_generation()
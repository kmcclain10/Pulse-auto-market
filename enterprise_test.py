import requests
import json
import pytest
import os
import base64
from pprint import pprint

# Get the backend URL from environment variable
BACKEND_URL = "https://a8223785-4b39-409d-a292-0a964f08dd99.preview.emergentagent.com/api"

# Test data
test_customer = {
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@example.com",
    "phone": "555-123-4567",
    "address": "123 Main St",
    "city": "Los Angeles",
    "state": "CA",
    "zip_code": "90001",
    "ssn_last_four": "1234",
    "credit_score": 720
}

test_vehicle = {
    "vin": "1HGCM82633A123456",
    "year": 2022,
    "make": "Toyota",
    "model": "Camry",
    "trim": "XLE",
    "condition": "new",
    "mileage": 5000,
    "msrp": 28000.00,
    "invoice_price": 26500.00,
    "selling_price": 25000.00
}

test_trade_in = {
    "vin": "5FNRL38477B091142",
    "year": 2018,
    "make": "Honda",
    "model": "Accord",
    "mileage": 45000,
    "condition": "good",
    "estimated_value": 15000.00,
    "payoff_amount": 10000.00,
    "net_trade_value": 5000.00
}

# Test data for credit application
test_credit_application = {
    "ssn": "123-45-6789",
    "date_of_birth": "1980-01-01T00:00:00.000Z",
    "employment_status": "employed",
    "employer_name": "Acme Corporation",
    "monthly_income": 6500.00,
    "housing_status": "own",
    "monthly_housing_payment": 1500.00,
    "requested_amount": 25000.00,
    "requested_term": 60,
    "down_payment": 5000.00
}

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

class TestEnterpriseFeatures:
    deal_id = None
    enterprise_deal_id = None
    document_id = None
    form_id = None
    credit_app_id = None
    signature_request_id = None
    
    def test_create_deal(self):
        """Create a basic deal for testing"""
        deal_data = {
            "customer": test_customer,
            "vehicle": test_vehicle,
            "salesperson": "Jane Doe"
        }
        
        response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
        assert response.status_code == 200
        
        # Save deal ID for later tests
        TestEnterpriseFeatures.deal_id = response.json()["id"]
        print(f"✅ Created test deal - ID: {TestEnterpriseFeatures.deal_id}")
    
    def test_forms_management(self):
        """Test the forms management system"""
        print("\n--- Testing Forms Management System ---")
        
        # 1. Get form templates by state
        states = ["CA", "TX", "FL", "NY"]
        
        for state in states:
            response = requests.get(f"{BACKEND_URL}/forms/templates?state={state}")
            assert response.status_code == 200
            templates = response.json()
            assert len(templates) > 0
            print(f"✅ Retrieved {len(templates)} form templates for {state}")
            
            # Verify template structure
            template = templates[0]
            assert "form_type" in template
            assert "title" in template
            assert "description" in template
            assert "fields" in template
        
        # 2. Get state requirements
        for state in states:
            response = requests.get(f"{BACKEND_URL}/forms/requirements/{state}")
            assert response.status_code == 200
            requirements = response.json()
            assert "required_forms" in requirements
            assert len(requirements["required_forms"]) > 0
            print(f"✅ Retrieved form requirements for {state}")
        
        # 3. Create deal forms
        assert TestEnterpriseFeatures.deal_id is not None, "Deal ID not set, create deal test must run first"
        
        form_data = {
            "template_id": "purchase_agreement_template",
            "form_type": "purchase_agreement",
            "field_values": {
                "dealer_name": "ABC Motors",
                "dealer_address": "123 Main St, Los Angeles, CA",
                "dealer_license": "DL12345",
                "customer_name": f"{test_customer['first_name']} {test_customer['last_name']}",
                "customer_address": test_customer["address"],
                "customer_phone": test_customer["phone"],
                "vehicle_year": test_vehicle["year"],
                "vehicle_make": test_vehicle["make"],
                "vehicle_model": test_vehicle["model"],
                "vehicle_vin": test_vehicle["vin"],
                "vehicle_mileage": test_vehicle["mileage"],
                "purchase_price": test_vehicle["selling_price"],
                "sales_tax": 1812.50,  # 7.25% of 25000
                "title_fee": 23.00,
                "license_fee": 65.00,
                "doc_fee": 85.00,
                "total_amount": 26985.50,
                "financing": True,
                "delivery_date": "2023-12-01"
            }
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.deal_id}/forms", json=form_data)
        assert response.status_code == 200
        TestEnterpriseFeatures.form_id = response.json()["id"]
        print(f"✅ Created deal form - ID: {TestEnterpriseFeatures.form_id}")
        
        # 4. Update forms
        update_data = {
            "field_values": {
                "delivery_date": "2023-12-15"  # Changed delivery date
            },
            "status": "pending_signature"
        }
        
        response = requests.put(f"{BACKEND_URL}/forms/{TestEnterpriseFeatures.form_id}", json=update_data)
        assert response.status_code == 200
        print(f"✅ Updated form")
        
        # 5. Get deal forms
        response = requests.get(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.deal_id}/forms")
        assert response.status_code == 200
        forms = response.json()
        assert len(forms) > 0
        assert forms[0]["id"] == TestEnterpriseFeatures.form_id
        print(f"✅ Retrieved {len(forms)} forms for deal")
        
        print("✅ Forms management system test passed")
    
    def test_document_generation(self):
        """Test the document generation system"""
        print("\n--- Testing Document Generation System ---")
        
        # 1. Generate multiple document types
        assert TestEnterpriseFeatures.deal_id is not None, "Deal ID not set, create deal test must run first"
        
        document_types = ["purchase_agreement", "odometer_disclosure", "truth_in_lending", "bill_of_sale"]
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.deal_id}/documents/generate", 
                                json={"document_types": document_types})
        print(f"Document generation response: {response.status_code}")
        print(f"Response content: {response.text}")
        assert response.status_code == 200
        result = response.json()
        assert "documents" in result
        assert len(result["documents"]) == len(document_types)
        
        # Save document ID for later tests
        TestEnterpriseFeatures.document_id = result["documents"][0]["id"]
        print(f"✅ Generated {len(result['documents'])} documents")
        
        # 2. Get deal documents
        response = requests.get(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.deal_id}/documents")
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) >= len(document_types)
        print(f"✅ Retrieved {len(documents)} documents for deal")
        
        # 3. Download PDF document
        response = requests.get(f"{BACKEND_URL}/documents/{TestEnterpriseFeatures.document_id}/pdf")
        assert response.status_code == 200
        pdf_data = response.json()
        assert "pdf_content" in pdf_data
        assert pdf_data["pdf_content"] is not None
        assert len(pdf_data["pdf_content"]) > 0
        
        # Verify it's a valid base64 encoded PDF
        try:
            pdf_bytes = base64.b64decode(pdf_data["pdf_content"])
            assert pdf_bytes[:4] == b'%PDF'  # PDF magic number
            print(f"✅ Downloaded valid PDF document")
        except Exception as e:
            assert False, f"Invalid PDF content: {str(e)}"
        
        print("✅ Document generation system test passed")
    
    def test_bank_integration(self):
        """Test the bank integration platform"""
        print("\n--- Testing Bank Integration Platform ---")
        
        # 1. Get available lenders
        response = requests.get(f"{BACKEND_URL}/lenders")
        assert response.status_code == 200
        lenders = response.json()
        assert len(lenders) > 0
        
        # Verify lender structure
        lender = lenders[0]
        assert "id" in lender
        assert "name" in lender
        assert "code" in lender
        assert "interest_rates" in lender
        print(f"✅ Retrieved {len(lenders)} available lenders")
        
        # 2. Create credit application
        assert TestEnterpriseFeatures.deal_id is not None, "Deal ID not set, create deal test must run first"
        
        credit_app_data = test_credit_application.copy()
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.deal_id}/credit-application", 
                                json=credit_app_data)
        assert response.status_code == 200
        credit_app = response.json()
        assert credit_app["deal_id"] == TestEnterpriseFeatures.deal_id
        assert credit_app["monthly_income"] == credit_app_data["monthly_income"]
        print(f"✅ Created credit application - ID: {credit_app['id']}")
        
        # 3. Submit to multiple lenders
        lender_ids = [lender["id"] for lender in lenders[:2]]  # Submit to first 2 lenders
        submission_data = {
            "lender_ids": lender_ids,
            "loan_amount": 20000.00,
            "loan_term": 60
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.deal_id}/submit-to-lenders", 
                                json=submission_data)
        assert response.status_code == 200
        result = response.json()
        assert "submissions" in result
        assert len(result["submissions"]) == len(lender_ids)
        print(f"✅ Submitted to {len(lender_ids)} lenders")
        
        # 4. Get lender responses
        response = requests.get(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.deal_id}/lender-responses")
        assert response.status_code == 200
        responses = response.json()
        assert len(responses) >= len(lender_ids)
        
        # Verify response structure
        lender_response = responses[0]
        assert "lender_id" in lender_response
        assert "status" in lender_response
        assert lender_response["deal_id"] == TestEnterpriseFeatures.deal_id
        print(f"✅ Retrieved {len(responses)} lender responses")
        
        # Verify lender response simulation
        statuses = [resp["status"] for resp in responses]
        print(f"Lender response statuses: {statuses}")
        assert any(status in ["approved", "conditional", "declined"] for status in statuses)
        
        print("✅ Bank integration platform test passed")
    
    def test_esignature_platform(self):
        """Test the e-signature platform"""
        print("\n--- Testing E-Signature Platform ---")
        
        # 1. Create signature request
        assert TestEnterpriseFeatures.document_id is not None, "Document ID not set, document generation test must run first"
        
        signature_data = {
            "signers": [
                {
                    "name": f"{test_customer['first_name']} {test_customer['last_name']}",
                    "email": test_customer["email"],
                    "role": "customer"
                },
                {
                    "name": "Dealer Representative",
                    "email": "dealer@example.com",
                    "role": "dealer"
                }
            ],
            "signing_order": ["customer", "dealer"]
        }
        
        response = requests.post(f"{BACKEND_URL}/documents/{TestEnterpriseFeatures.document_id}/signature-request", 
                                json=signature_data)
        assert response.status_code == 200
        signature_request = response.json()
        TestEnterpriseFeatures.signature_request_id = signature_request["id"]
        assert len(signature_request["signers"]) == 2
        print(f"✅ Created signature request - ID: {TestEnterpriseFeatures.signature_request_id}")
        
        # 2. Submit signatures
        signature_data = {
            "signer_email": test_customer["email"],
            "signer_name": f"{test_customer['first_name']} {test_customer['last_name']}",
            "signature_data": "base64encodedSignatureData",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "legal_notice_acknowledged": True
        }
        
        response = requests.post(f"{BACKEND_URL}/signature-requests/{TestEnterpriseFeatures.signature_request_id}/sign", 
                                json=signature_data)
        assert response.status_code == 200
        print(f"✅ Submitted customer signature")
        
        # 3. Get signature status
        assert TestEnterpriseFeatures.deal_id is not None, "Deal ID not set, create deal test must run first"
        
        response = requests.get(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.deal_id}/signature-status")
        assert response.status_code == 200
        status = response.json()
        assert "signature_requests" in status
        assert len(status["signature_requests"]) > 0
        print(f"✅ Retrieved signature status")
        
        print("✅ E-signature platform test passed")
        
    def test_enterprise_workflow(self):
        """Test the complete enterprise workflow"""
        print("\n--- Testing Complete Enterprise Workflow ---")
        
        # 1. Create a comprehensive deal
        deal_data = {
            "customer": test_enterprise_customer,
            "vehicle": test_enterprise_vehicle,
            "salesperson": "Enterprise Sales Rep"
        }
        
        response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
        assert response.status_code == 200
        
        TestEnterpriseFeatures.enterprise_deal_id = response.json()["id"]
        print(f"✅ Created enterprise deal - ID: {TestEnterpriseFeatures.enterprise_deal_id}")
        
        # 2. Create credit application with employment/income details
        credit_app_data = test_credit_application.copy()
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.enterprise_deal_id}/credit-application", 
                                json=credit_app_data)
        assert response.status_code == 200
        TestEnterpriseFeatures.credit_app_id = response.json()["id"]
        print(f"✅ Created credit application - ID: {TestEnterpriseFeatures.credit_app_id}")
        
        # 3. Submit to all 4 lenders
        lender_submission_data = {
            "lender_ids": ["chase_auto", "wells_fargo", "capital_one", "santander"],
            "loan_amount": 40000.00,
            "loan_term": 60
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.enterprise_deal_id}/submit-to-lenders", 
                                json=lender_submission_data)
        assert response.status_code == 200
        print(f"✅ Submitted to lenders - {len(response.json()['submissions'])} submissions created")
        
        # 4. Generate all document types
        document_types = ["purchase_agreement", "odometer_disclosure", "truth_in_lending", "bill_of_sale"]
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.enterprise_deal_id}/documents/generate", 
                                json=document_types)
        assert response.status_code == 200
        generated_docs = response.json()["documents"]
        assert len(generated_docs) == len(document_types)
        print(f"✅ Generated {len(generated_docs)} documents")
        
        # 5. Create signature requests for all documents
        for doc in generated_docs:
            signature_data = {
                "signers": [
                    {
                        "name": f"{test_enterprise_customer['first_name']} {test_enterprise_customer['last_name']}",
                        "email": test_enterprise_customer["email"],
                        "role": "customer"
                    },
                    {
                        "name": "F&I Manager",
                        "email": "fi.manager@dealership.com",
                        "role": "dealer"
                    }
                ]
            }
            
            response = requests.post(f"{BACKEND_URL}/documents/{doc['id']}/signature-request", 
                                    json=signature_data)
            assert response.status_code == 200
        
        print(f"✅ Created signature requests for all documents")
        
        # 6. Simulate signatures from customer and F&I manager
        # Get signature requests for the deal
        response = requests.get(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.enterprise_deal_id}/signature-status")
        assert response.status_code == 200
        signature_requests = response.json()["signature_requests"]
        
        for sig_req in signature_requests:
            # Customer signature
            signature_data = {
                "signer_email": test_enterprise_customer["email"],
                "signer_name": f"{test_enterprise_customer['first_name']} {test_enterprise_customer['last_name']}",
                "signature_data": "base64encodedSignatureData",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "legal_notice_acknowledged": True
            }
            
            response = requests.post(f"{BACKEND_URL}/signature-requests/{sig_req['id']}/sign", 
                                    json=signature_data)
            assert response.status_code == 200
            
            # F&I Manager signature
            signature_data = {
                "signer_email": "fi.manager@dealership.com",
                "signer_name": "F&I Manager",
                "signature_data": "base64encodedSignatureData",
                "ip_address": "192.168.1.2",
                "user_agent": "Mozilla/5.0",
                "legal_notice_acknowledged": True
            }
            
            response = requests.post(f"{BACKEND_URL}/signature-requests/{sig_req['id']}/sign", 
                                    json=signature_data)
            assert response.status_code == 200
        
        print(f"✅ Simulated signatures for all documents")
        
        # 7. Verify workflow tracking
        response = requests.get(f"{BACKEND_URL}/deals/{TestEnterpriseFeatures.enterprise_deal_id}")
        assert response.status_code == 200
        
        deal = response.json()
        print("\n--- Enterprise Deal Workflow Status ---")
        print(f"Forms Completed: {deal.get('forms_completed', False)}")
        print(f"Docs Generated: {deal.get('docs_generated', False)}")
        print(f"Signatures Completed: {deal.get('signatures_completed', False)}")
        print(f"Funding Completed: {deal.get('funding_completed', False)}")
        
        # Verify deal includes all the new arrays
        assert "forms" in deal
        assert "documents" in deal
        assert "credit_applications" in deal
        assert "lender_submissions" in deal
        
        print("✅ Complete enterprise workflow test passed")

# Run the tests
if __name__ == "__main__":
    print("Starting Enterprise F&I Desking Tool API Tests...")
    
    test = TestEnterpriseFeatures()
    
    # Run tests in sequence
    try:
        test.test_create_deal()
        test.test_forms_management()
        test.test_document_generation()
        test.test_bank_integration()
        test.test_esignature_platform()
        test.test_enterprise_workflow()
        
        print("\n✅ All enterprise feature tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise
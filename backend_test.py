import requests
import json
import pytest
import os
from pprint import pprint
import base64
import time

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

# Test class for F&I Desking Tool API
class TestFIDesking:
    deal_id = None
    enterprise_deal_id = None
    document_id = None
    form_id = None
    credit_app_id = None
    signature_request_id = None
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = requests.get(f"{BACKEND_URL}/")
        assert response.status_code == 200
        assert "Dealer Management System API" in response.json()["message"]
        print("✅ Root endpoint test passed")
    
    def test_create_deal(self):
        """Test creating a new deal"""
        # Test case 1: Create deal with customer and vehicle only
        deal_data = {
            "customer": test_customer,
            "vehicle": test_vehicle,
            "salesperson": "Jane Doe"
        }
        
        response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
        assert response.status_code == 200
        
        # Save deal ID for later tests
        TestFIDesking.deal_id = response.json()["id"]
        
        # Verify response structure
        deal = response.json()
        assert deal["customer"]["first_name"] == "John"
        assert deal["vehicle"]["make"] == "Toyota"
        assert deal["tax_calculation"]["sales_tax_rate"] == 0.0725  # CA tax rate
        assert len(deal["vsc_options"]) > 0  # VSC options should be generated
        assert deal["total_vehicle_price"] == 25000.00
        assert deal["total_deal_amount"] == deal["total_vehicle_price"] + deal["total_fees_taxes"]
        
        print(f"✅ Create deal test passed - Deal ID: {TestFIDesking.deal_id}")
        
        # Test case 2: Create deal with trade-in
        deal_data_with_trade = {
            "customer": test_customer,
            "vehicle": test_vehicle,
            "trade_in": test_trade_in,
            "salesperson": "Jane Doe"
        }
        
        response = requests.post(f"{BACKEND_URL}/deals", json=deal_data_with_trade)
        assert response.status_code == 200
        
        # Verify trade-in calculations
        deal = response.json()
        assert deal["trade_in"]["net_trade_value"] == 5000.00
        assert deal["total_vehicle_price"] == 20000.00  # 25000 - 5000 trade-in value
        
        print("✅ Create deal with trade-in test passed")
    
    def test_get_deals(self):
        """Test retrieving all deals"""
        response = requests.get(f"{BACKEND_URL}/deals")
        assert response.status_code == 200
        
        deals = response.json()
        assert isinstance(deals, list)
        assert len(deals) > 0
        
        print(f"✅ Get deals test passed - Found {len(deals)} deals")
    
    def test_get_deal_by_id(self):
        """Test retrieving a specific deal"""
        assert TestFIDesking.deal_id is not None, "Deal ID not set, create deal test must run first"
        
        response = requests.get(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}")
        assert response.status_code == 200
        
        deal = response.json()
        assert deal["id"] == TestFIDesking.deal_id
        
        print(f"✅ Get deal by ID test passed")
        
        # Test non-existent deal
        response = requests.get(f"{BACKEND_URL}/deals/nonexistent-id")
        assert response.status_code == 404
        
        print("✅ Get non-existent deal test passed (404 response)")
    
    def test_finance_calculator(self):
        """Test finance calculator"""
        # Test case 1: Standard financing
        finance_data = {
            "loan_amount": 20000.00,
            "apr": 5.99,
            "term_months": 60,
            "down_payment": 5000.00
        }
        
        response = requests.post(f"{BACKEND_URL}/finance/calculate", json=finance_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["loan_amount"] == 20000.00
        assert result["apr"] == 5.99
        assert result["term_months"] == 60
        assert result["down_payment"] == 5000.00
        assert result["monthly_payment"] > 0
        assert result["total_interest"] > 0
        assert result["total_cost"] == result["loan_amount"] + result["total_interest"]
        
        print(f"✅ Finance calculator test passed - Monthly payment: ${result['monthly_payment']:.2f}")
        
        # Test case 2: Zero APR financing
        zero_apr_data = {
            "loan_amount": 20000.00,
            "apr": 0,
            "term_months": 60,
            "down_payment": 5000.00
        }
        
        response = requests.post(f"{BACKEND_URL}/finance/calculate", json=zero_apr_data)
        assert response.status_code == 200
        
        result = response.json()
        # For zero APR, monthly payment should be close to loan amount / term
        assert abs(result["monthly_payment"] - (20000.00 / 60)) < 0.1
        assert result["total_interest"] == 0
        assert result["total_cost"] == 20000.00
        
        print("✅ Zero APR finance calculator test passed")
    
    def test_add_finance_to_deal(self):
        """Test adding finance terms to a deal"""
        assert TestFIDesking.deal_id is not None, "Deal ID not set, create deal test must run first"
        
        finance_data = {
            "loan_amount": 20000.00,
            "apr": 5.99,
            "term_months": 60,
            "down_payment": 5000.00
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}/finance", json=finance_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["loan_amount"] == 20000.00
        assert result["apr"] == 5.99
        assert result["term_months"] == 60
        
        # Verify deal was updated with finance terms
        deal_response = requests.get(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}")
        deal = deal_response.json()
        assert deal["finance_terms"] is not None
        assert deal["finance_terms"]["loan_amount"] == 20000.00
        
        print("✅ Add finance to deal test passed")
    
    def test_tax_calculations(self):
        """Test tax calculations for different states"""
        # Test different states
        states = ["CA", "TX", "FL", "NY"]
        
        for state in states:
            # Create a deal with customer in different state
            customer_copy = test_customer.copy()
            customer_copy["state"] = state
            
            deal_data = {
                "customer": customer_copy,
                "vehicle": test_vehicle,
                "salesperson": "Jane Doe"
            }
            
            response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
            assert response.status_code == 200
            
            deal = response.json()
            
            # Verify tax rates match expected values
            tax_rates = {
                "CA": 0.0725,
                "TX": 0.0625,
                "FL": 0.06,
                "NY": 0.08
            }
            
            assert deal["tax_calculation"]["sales_tax_rate"] == tax_rates[state]
            assert deal["tax_calculation"]["sales_tax_amount"] == round(test_vehicle["selling_price"] * tax_rates[state], 2)
            
            print(f"✅ Tax calculation test for {state} passed - Rate: {tax_rates[state]}")
    
    def test_get_deal_menu(self):
        """Test retrieving F&I menu for a deal"""
        assert TestFIDesking.deal_id is not None, "Deal ID not set, create deal test must run first"
        
        response = requests.get(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}/menu")
        assert response.status_code == 200
        
        menu = response.json()
        assert menu["deal_id"] == TestFIDesking.deal_id
        assert len(menu["vsc_options"]) > 0
        assert menu["gap_option"] is not None
        
        # Verify VSC options structure
        vsc = menu["vsc_options"][0]
        assert "coverage_type" in vsc
        assert "term" in vsc
        assert "base_cost" in vsc
        assert "markup" in vsc
        assert "final_price" in vsc
        
        # Verify GAP option structure
        gap = menu["gap_option"]
        assert "base_cost" in gap
        assert "markup" in gap
        assert "final_price" in gap
        assert "loan_to_value_ratio" in gap
        
        print("✅ Get deal menu test passed")
        
        # Test VSC pricing logic
        powertrain_options = [vsc for vsc in menu["vsc_options"] if vsc["coverage_type"] == "powertrain"]
        bumper_options = [vsc for vsc in menu["vsc_options"] if vsc["coverage_type"] == "bumper_to_bumper"]
        premium_options = [vsc for vsc in menu["vsc_options"] if vsc["coverage_type"] == "premium"]
        
        assert len(powertrain_options) > 0
        assert len(bumper_options) > 0
        assert len(premium_options) > 0
        
        # Verify pricing tiers (premium > bumper > powertrain)
        for term in ["12_months", "36_months", "60_months"]:
            pt_price = next((vsc["final_price"] for vsc in powertrain_options if vsc["term"] == term), 0)
            bb_price = next((vsc["final_price"] for vsc in bumper_options if vsc["term"] == term), 0)
            pr_price = next((vsc["final_price"] for vsc in premium_options if vsc["term"] == term), 0)
            
            assert pr_price > bb_price > pt_price, f"Pricing tiers incorrect for {term}"
        
        print("✅ VSC pricing logic test passed")
    
    def test_menu_selection(self):
        """Test selecting F&I products for a deal"""
        assert TestFIDesking.deal_id is not None, "Deal ID not set, create deal test must run first"
        
        # First get the menu to find a VSC option ID
        menu_response = requests.get(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}/menu")
        menu = menu_response.json()
        
        # Find a Bumper-to-Bumper 36 months VSC option
        vsc_id = None
        for vsc in menu["vsc_options"]:
            if vsc["coverage_type"] == "bumper_to_bumper" and vsc["term"] == "36_months":
                vsc_id = vsc["id"]
                vsc_price = vsc["final_price"]
                break
        
        assert vsc_id is not None, "Could not find Bumper-to-Bumper 36 months VSC option"
        
        # Get GAP price
        gap_price = menu["gap_option"]["final_price"]
        
        # Test case 1: Select VSC only
        selection_data = {
            "deal_id": TestFIDesking.deal_id,
            "selected_vsc_id": vsc_id,
            "include_gap": False
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}/menu-selection", json=selection_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["total_fi_products"] == vsc_price
        
        # Verify deal was updated
        deal_response = requests.get(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}")
        deal = deal_response.json()
        assert deal["selected_vsc"] == vsc_id
        assert deal["gap_option"] is None
        assert deal["total_fi_products"] == vsc_price
        assert deal["total_deal_amount"] == deal["total_vehicle_price"] + deal["total_fees_taxes"] + deal["total_fi_products"]
        
        print("✅ Menu selection with VSC only test passed")
        
        # Test case 2: Select VSC and GAP
        selection_data = {
            "deal_id": TestFIDesking.deal_id,
            "selected_vsc_id": vsc_id,
            "include_gap": True
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}/menu-selection", json=selection_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["total_fi_products"] == vsc_price + gap_price
        
        # Verify deal was updated
        deal_response = requests.get(f"{BACKEND_URL}/deals/{TestFIDesking.deal_id}")
        deal = deal_response.json()
        assert deal["selected_vsc"] == vsc_id
        assert deal["gap_option"] is not None
        assert deal["total_fi_products"] == vsc_price + gap_price
        assert deal["total_deal_amount"] == deal["total_vehicle_price"] + deal["total_fees_taxes"] + deal["total_fi_products"]
        
        print("✅ Menu selection with VSC and GAP test passed")
    
    def test_complete_deal_flow(self):
        """Test a complete deal flow from creation to F&I product selection"""
        # 1. Create a deal
        deal_data = {
            "customer": {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
                "phone": "555-987-6543",
                "address": "456 Oak St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94107",
                "ssn_last_four": "4321",
                "credit_score": 750
            },
            "vehicle": {
                "vin": "5YJSA1E40FF123456",
                "year": 2022,
                "make": "Toyota",
                "model": "Camry",
                "trim": "SE",
                "condition": "new",
                "mileage": 100,
                "msrp": 27000.00,
                "invoice_price": 25500.00,
                "selling_price": 25000.00
            },
            "salesperson": "Bob Johnson"
        }
        
        response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
        assert response.status_code == 200
        
        deal_id = response.json()["id"]
        initial_deal = response.json()
        
        # 2. Add finance terms
        finance_data = {
            "loan_amount": 20000.00,
            "apr": 5.99,
            "term_months": 60,
            "down_payment": 5000.00
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/finance", json=finance_data)
        assert response.status_code == 200
        
        # 3. Get F&I menu
        response = requests.get(f"{BACKEND_URL}/deals/{deal_id}/menu")
        assert response.status_code == 200
        
        menu = response.json()
        
        # Find Bumper-to-Bumper 36 months VSC
        vsc_id = None
        for vsc in menu["vsc_options"]:
            if vsc["coverage_type"] == "bumper_to_bumper" and vsc["term"] == "36_months":
                vsc_id = vsc["id"]
                break
        
        assert vsc_id is not None
        
        # 4. Select F&I products
        selection_data = {
            "deal_id": deal_id,
            "selected_vsc_id": vsc_id,
            "include_gap": True
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/menu-selection", json=selection_data)
        assert response.status_code == 200
        
        # 5. Verify final deal
        response = requests.get(f"{BACKEND_URL}/deals/{deal_id}")
        assert response.status_code == 200
        
        final_deal = response.json()
        
        # Verify all components are present and calculations are correct
        assert final_deal["customer"]["first_name"] == "Jane"
        assert final_deal["vehicle"]["make"] == "Toyota"
        assert final_deal["finance_terms"] is not None
        assert final_deal["finance_terms"]["apr"] == 5.99
        assert final_deal["selected_vsc"] == vsc_id
        assert final_deal["gap_option"] is not None
        assert final_deal["total_fi_products"] > 0
        assert final_deal["total_deal_amount"] == final_deal["total_vehicle_price"] + final_deal["total_fees_taxes"] + final_deal["total_fi_products"]
        
        print("✅ Complete deal flow test passed")
        
        # Print summary of the deal
        print("\n--- Deal Summary ---")
        print(f"Customer: {final_deal['customer']['first_name']} {final_deal['customer']['last_name']}")
        print(f"Vehicle: {final_deal['vehicle']['year']} {final_deal['vehicle']['make']} {final_deal['vehicle']['model']}")
        print(f"Selling Price: ${final_deal['vehicle']['selling_price']:.2f}")
        print(f"Tax & Fees: ${final_deal['total_fees_taxes']:.2f}")
        print(f"F&I Products: ${final_deal['total_fi_products']:.2f}")
        print(f"Total Deal Amount: ${final_deal['total_deal_amount']:.2f}")
        print(f"Monthly Payment: ${final_deal['finance_terms']['monthly_payment']:.2f}")
        print("--------------------")
    
    def test_document_generation(self):
        """Test document generation with fixed ObjectId serialization"""
        # Create a new deal for document testing
        deal_data = {
            "customer": test_enterprise_customer,
            "vehicle": test_enterprise_vehicle,
            "salesperson": "Document Test Agent"
        }
        
        response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
        assert response.status_code == 200
        
        TestFIDesking.enterprise_deal_id = response.json()["id"]
        deal_id = TestFIDesking.enterprise_deal_id
        
        # Add finance terms to the deal
        finance_data = {
            "loan_amount": 40000.00,
            "apr": 4.99,
            "term_months": 60,
            "down_payment": 5000.00
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/finance", json=finance_data)
        assert response.status_code == 200
        
        # Generate documents
        document_request = {
            "document_types": [
                "purchase_agreement",
                "odometer_disclosure",
                "truth_in_lending",
                "bill_of_sale"
            ]
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/documents/generate", json=document_request)
        assert response.status_code == 200
        
        result = response.json()
        assert "documents" in result
        assert len(result["documents"]) == 4
        
        # Save a document ID for later testing
        TestFIDesking.document_id = result["documents"][0]["id"]
        
        print(f"✅ Document generation test passed - Generated {len(result['documents'])} documents")
        
        # Verify documents were added to the deal
        response = requests.get(f"{BACKEND_URL}/deals/{deal_id}")
        assert response.status_code == 200
        
        deal = response.json()
        assert len(deal["documents"]) >= 4
        assert deal["docs_generated"] is True
        
        print("✅ Document association with deal test passed")
    
    def test_get_documents(self):
        """Test retrieving documents for a deal"""
        assert TestFIDesking.enterprise_deal_id is not None, "Enterprise deal ID not set"
        
        response = requests.get(f"{BACKEND_URL}/deals/{TestFIDesking.enterprise_deal_id}/documents")
        assert response.status_code == 200
        
        documents = response.json()
        assert isinstance(documents, list)
        assert len(documents) > 0
        
        # Verify document structure
        doc = documents[0]
        assert "id" in doc
        assert "title" in doc
        assert "document_type" in doc
        assert "status" in doc
        assert "pdf_content" in doc
        
        print(f"✅ Get documents test passed - Found {len(documents)} documents")
    
    def test_get_document_pdf(self):
        """Test retrieving PDF content of a document"""
        assert TestFIDesking.document_id is not None, "Document ID not set"
        
        response = requests.get(f"{BACKEND_URL}/documents/{TestFIDesking.document_id}/pdf")
        assert response.status_code == 200
        
        result = response.json()
        assert "pdf_content" in result
        assert result["pdf_content"] is not None
        assert len(result["pdf_content"]) > 0
        
        # Verify it's a valid base64 encoded PDF
        try:
            pdf_bytes = base64.b64decode(result["pdf_content"])
            assert pdf_bytes[:4] == b'%PDF'  # PDF magic number
            print("✅ PDF content validation passed")
        except Exception as e:
            assert False, f"Invalid PDF content: {str(e)}"
        
        print("✅ Get document PDF test passed")
    
    def test_enterprise_workflow(self):
        """Test the complete enterprise workflow with all components"""
        # Create a new deal for the enterprise workflow
        deal_data = {
            "customer": {
                "first_name": "Enterprise",
                "last_name": "Customer",
                "email": "enterprise@example.com",
                "phone": "555-123-9876",
                "address": "789 Enterprise Ave",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "ssn_last_four": "5678",
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
        
        response = requests.post(f"{BACKEND_URL}/deals", json=deal_data)
        assert response.status_code == 200
        
        deal_id = response.json()["id"]
        
        # Step 1: Add finance terms
        finance_data = {
            "loan_amount": 50000.00,
            "apr": 3.99,
            "term_months": 60,
            "down_payment": 6000.00
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/finance", json=finance_data)
        assert response.status_code == 200
        
        # Step 2: Create credit application
        credit_app_data = {
            "ssn": "123-45-6789",
            "date_of_birth": "1975-05-15T00:00:00.000Z",
            "employment_status": "employed",
            "employer_name": "Enterprise Corp",
            "monthly_income": 9500.00,
            "housing_status": "own",
            "monthly_housing_payment": 2500.00,
            "requested_amount": 50000.00,
            "requested_term": 60,
            "down_payment": 6000.00
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/credit-application", json=credit_app_data)
        assert response.status_code == 200
        
        credit_app = response.json()
        assert credit_app["deal_id"] == deal_id
        
        # Step 3: Submit to lenders
        lender_response = requests.get(f"{BACKEND_URL}/lenders")
        assert lender_response.status_code == 200
        
        lenders = lender_response.json()
        lender_ids = [lender["id"] for lender in lenders[:2]]  # Submit to first two lenders
        
        submission_data = {
            "lender_ids": lender_ids,
            "loan_amount": 50000.00,
            "loan_term": 60
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/submit-to-lenders", json=submission_data)
        assert response.status_code == 200
        
        submission_result = response.json()
        assert "submissions" in submission_result
        assert len(submission_result["submissions"]) == 2
        
        # Step 4: Select F&I products
        menu_response = requests.get(f"{BACKEND_URL}/deals/{deal_id}/menu")
        assert menu_response.status_code == 200
        
        menu = menu_response.json()
        
        # Find Premium 60 months VSC
        vsc_id = None
        for vsc in menu["vsc_options"]:
            if vsc["coverage_type"] == "premium" and vsc["term"] == "60_months":
                vsc_id = vsc["id"]
                break
        
        assert vsc_id is not None
        
        selection_data = {
            "deal_id": deal_id,
            "selected_vsc_id": vsc_id,
            "include_gap": True
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/menu-selection", json=selection_data)
        assert response.status_code == 200
        
        # Step 5: Generate documents
        document_request = {
            "document_types": [
                "purchase_agreement",
                "odometer_disclosure",
                "truth_in_lending",
                "bill_of_sale"
            ]
        }
        
        response = requests.post(f"{BACKEND_URL}/deals/{deal_id}/documents/generate", json=document_request)
        assert response.status_code == 200
        
        doc_result = response.json()
        assert "documents" in doc_result
        assert len(doc_result["documents"]) == 4
        
        # Step 6: Verify all components are integrated
        response = requests.get(f"{BACKEND_URL}/deals/{deal_id}")
        assert response.status_code == 200
        
        final_deal = response.json()
        
        # Verify all components are present
        assert final_deal["finance_terms"] is not None
        assert len(final_deal["documents"]) >= 4
        assert final_deal["docs_generated"] is True
        assert final_deal["selected_vsc"] == vsc_id
        assert final_deal["gap_option"] is not None
        
        # Get lender responses
        response = requests.get(f"{BACKEND_URL}/deals/{deal_id}/lender-responses")
        assert response.status_code == 200
        
        lender_responses = response.json()
        assert len(lender_responses) == 2
        
        # Get documents
        response = requests.get(f"{BACKEND_URL}/deals/{deal_id}/documents")
        assert response.status_code == 200
        
        documents = response.json()
        assert len(documents) >= 4
        
        # Verify PDF content for each document
        for doc in documents[:2]:  # Test first two documents
            response = requests.get(f"{BACKEND_URL}/documents/{doc['id']}/pdf")
            assert response.status_code == 200
            
            pdf_result = response.json()
            assert "pdf_content" in pdf_result
            assert pdf_result["pdf_content"] is not None
            assert len(pdf_result["pdf_content"]) > 0
            
            # Verify it's a valid base64 encoded PDF
            try:
                pdf_bytes = base64.b64decode(pdf_result["pdf_content"])
                assert pdf_bytes[:4] == b'%PDF'  # PDF magic number
            except Exception as e:
                assert False, f"Invalid PDF content for document {doc['title']}: {str(e)}"
        
        print("✅ Complete enterprise workflow integration test passed")
        print("\n--- Enterprise Deal Summary ---")
        print(f"Customer: {final_deal['customer']['first_name']} {final_deal['customer']['last_name']}")
        print(f"Vehicle: {final_deal['vehicle']['year']} {final_deal['vehicle']['make']} {final_deal['vehicle']['model']}")
        print(f"Selling Price: ${final_deal['vehicle']['selling_price']:.2f}")
        print(f"F&I Products: ${final_deal['total_fi_products']:.2f}")
        print(f"Total Deal Amount: ${final_deal['total_deal_amount']:.2f}")
        print(f"Documents Generated: {len(documents)}")
        print(f"Lender Submissions: {len(lender_responses)}")
        print("-----------------------------")


# Run the tests
if __name__ == "__main__":
    print("Starting F&I Desking Tool API Tests...")
    
    test = TestFIDesking()
    
    # Run tests in sequence
    try:
        test.test_root_endpoint()
        test.test_create_deal()
        test.test_get_deals()
        test.test_get_deal_by_id()
        test.test_finance_calculator()
        test.test_add_finance_to_deal()
        test.test_tax_calculations()
        test.test_get_deal_menu()
        test.test_menu_selection()
        test.test_complete_deal_flow()
        
        print("\n✅ All tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise
import requests
import json
import os
from pprint import pprint
import base64
import time
from datetime import datetime, timedelta

# Get the backend URL from environment variable
BACKEND_URL = "https://a8223785-4b39-409d-a292-0a964f08dd99.preview.emergentagent.com/api"

# Test data for CRM
test_lead_high_quality = {
    "first_name": "John",
    "last_name": "Customer",
    "email": "john@example.com",
    "phone": "555-123-4567",
    "address": "123 Main St",
    "city": "Los Angeles",
    "state": "CA",
    "zip_code": "90001",
    "source": "website",
    "status": "new",
    "interested_vehicles": ["BMW X5", "Audi Q7"],
    "budget_min": 50000.00,
    "budget_max": 80000.00,
    "preferred_contact_method": "email"
}

test_lead_medium_quality = {
    "first_name": "Sarah",
    "last_name": "Johnson",
    "email": "sarah@example.com",
    "phone": "555-987-6543",
    "city": "Chicago",
    "state": "IL",
    "source": "social_media",
    "status": "new",
    "interested_vehicles": ["Honda Accord"],
    "budget_min": 25000.00,
    "budget_max": 35000.00
}

test_lead_low_quality = {
    "first_name": "Anonymous",
    "last_name": "User",
    "email": "anon@example.com",
    "source": "website",
    "status": "new"
}

test_communication = {
    "type": "email",
    "direction": "outbound",
    "subject": "Vehicle Information",
    "content": "Thank you for your interest in our vehicles. Here is the information you requested.",
    "to_email": "customer@example.com",
    "staff_member": "Jane Doe"
}

test_task = {
    "title": "Follow up with customer",
    "description": "Call customer to discuss vehicle options",
    "type": "follow_up",
    "priority": "high",
    "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
}

# Test vehicle for lead conversion
test_vehicle = {
    "vin": "5UXWX7C5*BA654321",
    "year": 2023,
    "make": "BMW",
    "model": "X5",
    "trim": "xDrive40i",
    "condition": "new",
    "mileage": 150,
    "msrp": 65000.00,
    "invoice_price": 60000.00,
    "selling_price": 62000.00
}

# Test class for AI Communication CRM System
class TestAICRM:
    lead_id = None
    high_quality_lead_id = None
    medium_quality_lead_id = None
    low_quality_lead_id = None
    communication_id = None
    task_id = None
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = requests.get(f"{BACKEND_URL}/")
        assert response.status_code == 200
        assert "Dealer Management System API" in response.json()["message"]
        print("✅ Root endpoint test passed")
    
    def test_lead_management(self):
        """Test lead management with AI scoring"""
        print("\n--- Testing Lead Management with AI Scoring ---")
        
        # Test case 1: Create high-quality lead
        response = requests.post(f"{BACKEND_URL}/leads", json=test_lead_high_quality)
        assert response.status_code == 200
        
        lead = response.json()
        TestAICRM.high_quality_lead_id = lead["id"]
        TestAICRM.lead_id = lead["id"]  # Save for other tests
        
        assert lead["first_name"] == "John"
        assert lead["last_name"] == "Customer"
        assert lead["score"] > 0  # AI should assign a score
        
        print(f"✅ Create high-quality lead test passed - Lead ID: {TestAICRM.high_quality_lead_id}, Score: {lead['score']}")
        
        # Test case 2: Create medium-quality lead
        response = requests.post(f"{BACKEND_URL}/leads", json=test_lead_medium_quality)
        assert response.status_code == 200
        
        lead = response.json()
        TestAICRM.medium_quality_lead_id = lead["id"]
        
        assert lead["first_name"] == "Sarah"
        assert lead["score"] > 0  # AI should assign a score
        
        print(f"✅ Create medium-quality lead test passed - Lead ID: {TestAICRM.medium_quality_lead_id}, Score: {lead['score']}")
        
        # Test case 3: Create low-quality lead
        response = requests.post(f"{BACKEND_URL}/leads", json=test_lead_low_quality)
        assert response.status_code == 200
        
        lead = response.json()
        TestAICRM.low_quality_lead_id = lead["id"]
        
        assert lead["first_name"] == "Anonymous"
        assert lead["score"] >= 0  # AI should assign a score
        
        print(f"✅ Create low-quality lead test passed - Lead ID: {TestAICRM.low_quality_lead_id}, Score: {lead['score']}")
        
        # Test case 4: Get leads with filtering
        response = requests.get(f"{BACKEND_URL}/leads")
        assert response.status_code == 200
        
        leads = response.json()
        assert isinstance(leads, list)
        assert len(leads) >= 3  # At least our 3 test leads
        
        print(f"✅ Get leads test passed - Found {len(leads)} leads")
        
        # Test filtering by status
        response = requests.get(f"{BACKEND_URL}/leads?status=new")
        assert response.status_code == 200
        
        new_leads = response.json()
        assert all(lead["status"] == "new" for lead in new_leads)
        
        print(f"✅ Get leads with status filter test passed")
        
        # Test filtering by min_score
        if lead["score"] > 20:  # Only test if we have a lead with score > 20
            response = requests.get(f"{BACKEND_URL}/leads?min_score=20")
            assert response.status_code == 200
            
            high_score_leads = response.json()
            assert all(lead["score"] >= 20 for lead in high_score_leads)
            
            print(f"✅ Get leads with min_score filter test passed")
        
        # Test case 5: Update lead status
        status_data = {"status": "qualified"}
        response = requests.put(f"{BACKEND_URL}/leads/{TestAICRM.lead_id}/status", json=status_data)
        assert response.status_code == 200
        
        # Verify lead status was updated
        response = requests.get(f"{BACKEND_URL}/leads/{TestAICRM.lead_id}")
        assert response.status_code == 200
        
        lead = response.json()
        assert lead["status"] == "qualified"
        
        print(f"✅ Update lead status test passed")
        
        # Test case 6: Get tasks to verify automation
        time.sleep(1)  # Wait for async task creation
        response = requests.get(f"{BACKEND_URL}/tasks?lead_id={TestAICRM.lead_id}")
        assert response.status_code == 200
        
        tasks = response.json()
        assert len(tasks) > 0
        assert any(task["is_ai_generated"] for task in tasks)
        
        print(f"✅ Automatic task creation test passed - {len(tasks)} tasks created")
    
    def test_ai_communication(self):
        """Test AI communication system"""
        print("\n--- Testing AI Communication System ---")
        
        # Test case 1: Create communication record
        comm_data = test_communication.copy()
        comm_data["lead_id"] = TestAICRM.lead_id
        
        response = requests.post(f"{BACKEND_URL}/communications", json=comm_data)
        assert response.status_code == 200
        
        communication = response.json()
        TestAICRM.communication_id = communication["id"]
        
        assert communication["lead_id"] == TestAICRM.lead_id
        assert communication["type"] == "email"
        assert communication["content"] == test_communication["content"]
        
        print(f"✅ Create communication record test passed - Communication ID: {TestAICRM.communication_id}")
        
        # Test case 2: Get communications with filtering
        response = requests.get(f"{BACKEND_URL}/communications?lead_id={TestAICRM.lead_id}")
        assert response.status_code == 200
        
        communications = response.json()
        assert isinstance(communications, list)
        assert len(communications) > 0
        assert all(comm["lead_id"] == TestAICRM.lead_id for comm in communications)
        
        print(f"✅ Get communications with lead_id filter test passed - Found {len(communications)} communications")
        
        # Test case 3: Generate AI response
        request_data = {
            "prompt": "Customer is asking about financing options for a luxury vehicle",
            "context": {
                "customer_name": "John Customer",
                "vehicle_of_interest": "BMW X5",
                "budget": "$50k-80k"
            },
            "type": "email"
        }
        
        response = requests.post(f"{BACKEND_URL}/communications/ai-response", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "response" in result
        assert len(result["response"]) > 0
        assert result["type"] == "email"
        
        print(f"✅ Generate AI response test passed - Generated {len(result['response'])} characters")
        
        # Test case 4: Generate AI SMS response (should be shorter)
        request_data["type"] = "sms"
        
        response = requests.post(f"{BACKEND_URL}/communications/ai-response", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "response" in result
        assert len(result["response"]) > 0
        assert result["type"] == "sms"
        assert len(result["response"]) < 160  # SMS should be under 160 characters
        
        print(f"✅ Generate AI SMS response test passed - Generated {len(result['response'])} characters")
        
        # Test case 5: Auto-respond to inquiry
        request_data = {
            "inquiry": "I'm interested in the BMW X5 you have listed. Can you tell me more about financing options?",
            "lead_id": TestAICRM.lead_id
        }
        
        response = requests.post(f"{BACKEND_URL}/communications/auto-respond", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "response" in result
        assert len(result["response"]) > 0
        assert "message" in result
        
        print(f"✅ Auto-respond to inquiry test passed")
    
    def test_task_automation(self):
        """Test task automation"""
        print("\n--- Testing Task Automation ---")
        
        # Test case 1: Create task
        task_data = test_task.copy()
        task_data["lead_id"] = TestAICRM.lead_id
        
        response = requests.post(f"{BACKEND_URL}/tasks", json=task_data)
        assert response.status_code == 200
        
        task = response.json()
        TestAICRM.task_id = task["id"]
        
        assert task["lead_id"] == TestAICRM.lead_id
        assert task["title"] == test_task["title"]
        assert task["status"] == "pending"
        
        print(f"✅ Create task test passed - Task ID: {TestAICRM.task_id}")
        
        # Test case 2: Get tasks with filtering
        response = requests.get(f"{BACKEND_URL}/tasks?lead_id={TestAICRM.lead_id}")
        assert response.status_code == 200
        
        tasks = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert all(task["lead_id"] == TestAICRM.lead_id for task in tasks)
        
        print(f"✅ Get tasks with lead_id filter test passed - Found {len(tasks)} tasks")
        
        # Test filtering by status
        response = requests.get(f"{BACKEND_URL}/tasks?status=pending")
        assert response.status_code == 200
        
        pending_tasks = response.json()
        assert all(task["status"] == "pending" for task in pending_tasks)
        
        print(f"✅ Get tasks with status filter test passed")
        
        # Test case 3: Complete task
        response = requests.put(f"{BACKEND_URL}/tasks/{TestAICRM.task_id}/complete")
        assert response.status_code == 200
        
        # Verify task was completed
        response = requests.get(f"{BACKEND_URL}/tasks?lead_id={TestAICRM.lead_id}")
        assert response.status_code == 200
        
        tasks = response.json()
        completed_task = next((task for task in tasks if task["id"] == TestAICRM.task_id), None)
        assert completed_task is not None
        assert completed_task["status"] == "completed"
        assert completed_task["completed_at"] is not None
        
        print(f"✅ Complete task test passed")
    
    def test_ai_analytics(self):
        """Test AI analytics and insights"""
        print("\n--- Testing AI Analytics & Insights ---")
        
        # Test case 1: Get lead insights
        response = requests.get(f"{BACKEND_URL}/analytics/lead-insights/{TestAICRM.lead_id}")
        assert response.status_code == 200
        
        insights = response.json()
        assert "lead_score" in insights
        assert "communication_count" in insights
        assert "ai_insights" in insights
        
        print(f"✅ Get lead insights test passed - Score: {insights['lead_score']}")
        
        # Test case 2: Get dashboard analytics
        response = requests.get(f"{BACKEND_URL}/analytics/dashboard")
        assert response.status_code == 200
        
        dashboard = response.json()
        assert "total_leads" in dashboard
        assert "new_leads" in dashboard
        assert "qualified_leads" in dashboard
        assert "conversion_rate" in dashboard
        assert "recent_communications" in dashboard
        assert "pending_tasks" in dashboard
        
        print(f"✅ Get dashboard analytics test passed - {dashboard['total_leads']} leads, {dashboard['recent_communications']} communications")
    
    def test_complete_ai_crm_workflow(self):
        """Test complete AI CRM workflow"""
        print("\n--- Testing Complete AI CRM Workflow ---")
        
        # Step 1: Create a new lead
        lead_data = {
            "first_name": "John",
            "last_name": "Customer",
            "email": "john@example.com",
            "phone": "555-123-4567",
            "address": "123 Main St",
            "city": "Los Angeles",
            "state": "CA",
            "zip_code": "90001",
            "source": "website",
            "status": "new",
            "interested_vehicles": ["BMW X5", "Audi Q7"],
            "budget_min": 50000.00,
            "budget_max": 80000.00,
            "preferred_contact_method": "email"
        }
        
        response = requests.post(f"{BACKEND_URL}/leads", json=lead_data)
        assert response.status_code == 200
        
        lead = response.json()
        lead_id = lead["id"]
        
        print(f"✅ Step 1: Created lead - ID: {lead_id}, Score: {lead['score']}")
        
        # Step 2: Generate AI response to initial inquiry
        request_data = {
            "prompt": "Customer is asking about BMW X5 availability and pricing",
            "context": {
                "customer_name": f"{lead['first_name']} {lead['last_name']}",
                "vehicle_of_interest": "BMW X5",
                "budget": "$50k-80k"
            },
            "type": "email"
        }
        
        response = requests.post(f"{BACKEND_URL}/communications/ai-response", json=request_data)
        assert response.status_code == 200
        
        ai_response = response.json()["response"]
        
        # Step 3: Create communication record with AI response
        comm_data = {
            "lead_id": lead_id,
            "type": "email",
            "direction": "outbound",
            "subject": "BMW X5 Information",
            "content": ai_response,
            "to_email": lead["email"],
            "staff_member": "AI Test Agent",
            "is_ai_generated": True
        }
        
        response = requests.post(f"{BACKEND_URL}/communications", json=comm_data)
        assert response.status_code == 200
        
        print(f"✅ Step 2-3: Generated and saved AI response")
        
        # Step 4: Update lead status to qualified
        status_data = {"status": "qualified"}
        response = requests.put(f"{BACKEND_URL}/leads/{lead_id}/status", json=status_data)
        assert response.status_code == 200
        
        # Step 5: Verify auto-task creation
        time.sleep(1)  # Wait for async task creation
        response = requests.get(f"{BACKEND_URL}/tasks?lead_id={lead_id}")
        assert response.status_code == 200
        
        tasks = response.json()
        assert len(tasks) > 0
        assert any(task["is_ai_generated"] for task in tasks)
        
        print(f"✅ Step 4-5: Updated lead status and verified auto-task creation")
        
        # Step 6: Convert lead to deal
        conversion_data = {
            "vehicle": test_vehicle
        }
        
        response = requests.post(f"{BACKEND_URL}/leads/{lead_id}/convert", json=conversion_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "deal_id" in result
        deal_id = result["deal_id"]
        
        # Step 7: Verify lead was converted
        response = requests.get(f"{BACKEND_URL}/leads/{lead_id}")
        assert response.status_code == 200
        
        lead = response.json()
        assert lead["status"] == "sold"
        assert lead["converted_deal_id"] == deal_id
        
        # Step 8: Verify deal was created with customer info
        response = requests.get(f"{BACKEND_URL}/deals/{deal_id}")
        assert response.status_code == 200
        
        deal = response.json()
        assert deal["customer"]["first_name"] == "John"
        assert deal["customer"]["last_name"] == "Customer"
        assert deal["vehicle"]["make"] == "BMW"
        assert deal["vehicle"]["model"] == "X5"
        
        print(f"✅ Step 6-8: Converted lead to deal - Deal ID: {deal_id}")
        
        print("\n✅ Complete AI CRM workflow test passed")
        print("\n--- AI CRM Workflow Summary ---")
        print(f"Lead: {lead['first_name']} {lead['last_name']}")
        print(f"Lead Score: {lead['score']}")
        print(f"Lead Status: {lead['status']}")
        print(f"Converted to Deal: {deal_id}")
        print(f"Vehicle: {deal['vehicle']['year']} {deal['vehicle']['make']} {deal['vehicle']['model']}")
        print(f"Selling Price: ${deal['vehicle']['selling_price']:.2f}")
        print("-----------------------------")


# Run the tests
if __name__ == "__main__":
    print("Starting AI Communication CRM System Tests...")
    
    # AI Communication CRM tests
    print("\n--- Testing AI Communication CRM System ---")
    crm_test = TestAICRM()
    
    try:
        # Test the root endpoint to make sure the API is accessible
        crm_test.test_root_endpoint()
        
        # Run CRM tests
        crm_test.test_lead_management()
        crm_test.test_ai_communication()
        crm_test.test_task_automation()
        crm_test.test_ai_analytics()
        crm_test.test_complete_ai_crm_workflow()
        
        print("\n✅ All AI Communication CRM tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise
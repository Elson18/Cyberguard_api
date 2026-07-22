import json
import urllib.request
import urllib.error
import time
import sys

BASE_URL = "http://127.0.0.1:5000"

def make_request(path, method="GET", body=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            res_body = res.read().decode("utf-8")
            return res.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        res_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(res_body)
        except Exception:
            return e.code, {"success": False, "message": res_body}
    except Exception as e:
        print(f"Network error on {method} {path}: {str(e)}")
        return 0, {"success": False, "message": str(e)}

def run_tests():
    print("==================================================")
    print("STARTING FEES MODULE INTEGRATION VERIFICATION TESTS")
    print("==================================================")

    # 1. Login as Admin
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "admin",
        "password": "Admin@123"
    })
    if status != 200:
        print("FAIL: Admin Login failed.")
        return False
    admin_token = res["data"]["token"]
    print("SUCCESS: Admin logged in.")

    # 2. Create Class
    class_name = "FeesClass"
    section = "Y"
    status, res = make_request("/api/admin/create-class", "POST", {
        "className": class_name,
        "section": section
    }, token=admin_token)
    if status not in (200, 201) and "already exists" not in res.get("message", ""):
        print(f"FAIL: Create class failed: {res}")
        return False
    
    # Retrieve the class ID
    class_id = res.get("data", {}).get("_id")
    if not class_id:
        status, cls_list_res = make_request("/api/classes", "GET", token=admin_token)
        for cls in cls_list_res.get("data", []):
            if cls.get("className") == class_name and cls.get("section") == section:
                class_id = cls.get("_id")
                break
    if not class_id:
        print("FAIL: Could not retrieve class ID.")
        return False
    print(f"SUCCESS: Class verified. ID: {class_id}")

    # 3. Create Teacher
    teacher_uid = "fees_teacher"
    teacher_tid = "T_FEES"
    status, res = make_request("/api/admin/create-teacher", "POST", {
        "userId": teacher_uid,
        "password": "Password123",
        "name": "Teacher Alice",
        "department": "Mathematics",
        "teacherId": teacher_tid
    }, token=admin_token)
    if status not in (200, 201) and "already exists" not in res.get("message", ""):
        print(f"FAIL: Create teacher failed: {res}")
        return False
    print("SUCCESS: Teacher verified.")

    # Assign Teacher to Class
    status, res = make_request("/api/admin/assign-teacher", "POST", {
        "teacherId": teacher_tid,
        "classId": class_id
    }, token=admin_token)
    if status != 200:
        print(f"FAIL: Teacher assignment failed: {res}")
        return False
    print("SUCCESS: Teacher assigned to class.")

    # 4. Create Students
    students_info = [
        {"userId": "fees_stud1", "studentId": "FS001", "name": "Student Alpha", "rollNumber": "501"},
        {"userId": "fees_stud2", "studentId": "FS002", "name": "Student Beta", "rollNumber": "502"}
    ]
    for stud in students_info:
        status, res = make_request("/api/admin/create-student", "POST", {
            "userId": stud["userId"],
            "password": "Password123",
            "name": stud["name"],
            "classId": class_id,
            "rollNumber": stud["rollNumber"],
            "studentId": stud["studentId"]
        }, token=admin_token)
        if status not in (200, 201) and "already exists" not in res.get("message", ""):
            print(f"FAIL: Create student {stud['name']} failed: {res}")
            return False
    print("SUCCESS: Students created and verified.")

    # 5. Create Fee Structure
    fee_struct_req = {
        "title": "Term 1 Admission Fees",
        "academicYear": "2026-2027",
        "classIds": [class_id],
        "feeItems": [
            {"name": "Tuition Fee", "amount": 10000.0},
            {"name": "Lab Fee", "amount": 2000.0}
        ],
        "dueDate": "2026-09-15"
    }
    status, res = make_request("/api/admin/fees", "POST", fee_struct_req, token=admin_token)
    if status != 201:
        # Check if already exists from previous runs. If so, let's try to update or delete and recreate
        if "already exists" in res.get("message", ""):
            # Retrieve its ID and let's delete it so tests are clean
            print("INFO: Fee structure already exists. Fetching to clean up...")
            status_list, res_list = make_request("/api/admin/fees", "GET", token=admin_token)
            fee_struct_id = None
            for fs in res_list.get("data", []):
                if fs.get("title") == "Term 1 Admission Fees":
                    fee_struct_id = fs.get("feeStructureId")
                    break
            
            if fee_struct_id:
                # Delete any payments to allow deletion
                print(f"INFO: Cleaning up old structure {fee_struct_id}")
                # We can delete it directly
                status_del, res_del = make_request(f"/api/admin/fees/{fee_struct_id}", "DELETE", token=admin_token)
                if status_del != 200:
                    print(f"WARNING: Cleanup delete failed: {res_del}")
                # Re-try creation
                status, res = make_request("/api/admin/fees", "POST", fee_struct_req, token=admin_token)
                if status != 201:
                    print(f"FAIL: Create fee structure after cleanup failed: {res}")
                    return False
            else:
                print("FAIL: Could not resolve old fee structure ID.")
                return False
        else:
            print(f"FAIL: Create fee structure failed: {res}")
            return False

    fee_structure_id = res["data"]["feeStructureId"]
    print(f"SUCCESS: Fee Structure created. ID: {fee_structure_id}")

    # 6. Retrieve Fee Structures
    status, res = make_request("/api/admin/fees", "GET", token=admin_token)
    if status != 200 or not res.get("data"):
        print("FAIL: Get fee structures failed.")
        return False
    print("SUCCESS: Get fee structures list.")

    # 7. Get Single Fee Structure
    status, res = make_request(f"/api/admin/fees/{fee_structure_id}", "GET", token=admin_token)
    if status != 200 or res["data"]["feeStructureId"] != fee_structure_id:
        print("FAIL: Get single fee structure failed.")
        return False
    print("SUCCESS: Get single fee structure details.")

    # 8. Update Fee Structure (succeeds since no payments exist yet)
    update_req = {
        "title": "Term 1 Admission Fees Updated",
        "academicYear": "2026-2027",
        "classIds": [class_id],
        "feeItems": [
            {"name": "Tuition Fee", "amount": 11000.0},
            {"name": "Lab Fee", "amount": 1000.0}
        ],
        "dueDate": "2026-09-20"
    }
    status, res = make_request(f"/api/admin/fees/{fee_structure_id}", "PUT", update_req, token=admin_token)
    if status != 200:
        print(f"FAIL: Update fee structure failed: {res}")
        return False
    print("SUCCESS: Update fee structure.")

    # 9. Get student fees list to verify assignments (should have 2 assignments of 12000 total each)
    status, res = make_request("/api/admin/fees/students", "GET", token=admin_token)
    if status != 200:
        print("FAIL: Get student fee list failed.")
        return False
    assignments = [rec for rec in res["data"] if rec["feeStructureId"] == fee_structure_id]
    if len(assignments) != 2:
        print(f"FAIL: Expected 2 student fee assignments, found {len(assignments)}")
        return False
    for rec in assignments:
        if rec["totalAmount"] != 12000.0 or rec["status"] != "UNPAID":
            print(f"FAIL: Invalid initial values: {rec}")
            return False
    print("SUCCESS: Student fee assignments verified.")

    # 10. Get Dashboard
    status, res = make_request("/api/admin/fees/dashboard", "GET", token=admin_token)
    if status != 200 or "totalFees" not in res.get("data", {}):
        print(f"FAIL: Get dashboard failed: {res}")
        return False
    print(f"SUCCESS: Dashboard fetched. Data: {res['data']}")

    # 11. Send reminder to FS001
    reminder_req = {
        "studentIds": ["FS001"],
        "message": "Please pay your Term 1 Admission Fees soon."
    }
    status, res = make_request("/api/admin/fees/reminder", "POST", reminder_req, token=admin_token)
    if status != 200:
        print(f"FAIL: Send reminder failed: {res}")
        return False
    # Verify reminder updated lastReminderAt in student_fees
    status_list, res_list = make_request("/api/admin/fees/students", "GET", token=admin_token)
    fs001_fee = next(rec for rec in res_list["data"] if rec["studentId"] == "FS001" and rec["feeStructureId"] == fee_structure_id)
    if not fs001_fee.get("lastReminderAt"):
        print("FAIL: lastReminderAt not updated on student fee.")
        return False
    print("SUCCESS: Send reminder and lastReminderAt verification.")

    # 12. Record Payment 1 (Partial payment)
    payment_req = {
        "studentId": "FS001",
        "feeStructureId": fee_structure_id,
        "amount": 5000.0,
        "paymentMode": "Cash",
        "transactionId": "TXN_FEES_TEST_001"
    }
    status, res = make_request("/api/admin/fees/payment", "POST", payment_req, token=admin_token)
    if status != 201:
        print(f"FAIL: Record payment 1 failed: {res}")
        return False
    # Verify student fee totals updated
    status_list, res_list = make_request("/api/admin/fees/students", "GET", token=admin_token)
    fs001_fee = next(rec for rec in res_list["data"] if rec["studentId"] == "FS001" and rec["feeStructureId"] == fee_structure_id)
    if fs001_fee["paidAmount"] != 5000.0 or fs001_fee["pendingAmount"] != 7000.0 or fs001_fee["status"] != "PARTIALLY_PAID":
        print(f"FAIL: Invalid updated fee status/amounts after partial payment: {fs001_fee}")
        return False
    print("SUCCESS: Record partial payment and check values.")

    # 13. Record payment with duplicate transactionId (should fail)
    payment_req_dup = {
        "studentId": "FS002",
        "feeStructureId": fee_structure_id,
        "amount": 4000.0,
        "paymentMode": "Online",
        "transactionId": "TXN_FEES_TEST_001"
    }
    status, res = make_request("/api/admin/fees/payment", "POST", payment_req_dup, token=admin_token)
    if status == 201:
        print("FAIL: Expected duplicate transaction check to fail, but it succeeded.")
        return False
    print(f"SUCCESS: Duplicate transaction check verified (rejected with status {status}).")

    # 14. Record payment exceeding pending amount (should fail)
    payment_req_excess = {
        "studentId": "FS001",
        "feeStructureId": fee_structure_id,
        "amount": 8000.0,
        "paymentMode": "Cash",
        "transactionId": "TXN_FEES_TEST_002"
    }
    status, res = make_request("/api/admin/fees/payment", "POST", payment_req_excess, token=admin_token)
    if status == 201:
        print("FAIL: Expected payment exceeding pending amount to fail, but it succeeded.")
        return False
    print(f"SUCCESS: Excess payment check verified (rejected with status {status}).")

    # 15. Attempt to update structure when payments exist (should fail)
    status, res = make_request(f"/api/admin/fees/{fee_structure_id}", "PUT", update_req, token=admin_token)
    if status == 200:
        print("FAIL: Expected update to fail when payments exist, but it succeeded.")
        return False
    print(f"SUCCESS: Update block verification (rejected with status {status}).")

    # 16. Attempt to delete structure when payments exist (should fail)
    status, res = make_request(f"/api/admin/fees/{fee_structure_id}", "DELETE", token=admin_token)
    if status == 200:
        print("FAIL: Expected delete to fail when payments exist, but it succeeded.")
        return False
    print(f"SUCCESS: Delete block verification (rejected with status {status}).")

    # 17. Record Payment 2 (Clear balance for FS001)
    payment_req_full = {
        "studentId": "FS001",
        "feeStructureId": fee_structure_id,
        "amount": 7000.0,
        "paymentMode": "Online",
        "transactionId": "TXN_FEES_TEST_003"
    }
    status, res = make_request("/api/admin/fees/payment", "POST", payment_req_full, token=admin_token)
    if status != 201:
        print(f"FAIL: Record full payment failed: {res}")
        return False
    status_list, res_list = make_request("/api/admin/fees/students", "GET", token=admin_token)
    fs001_fee = next(rec for rec in res_list["data"] if rec["studentId"] == "FS001" and rec["feeStructureId"] == fee_structure_id)
    if fs001_fee["status"] != "PAID" or fs001_fee["pendingAmount"] != 0:
        print(f"FAIL: Expected PAID status, got {fs001_fee['status']}")
        return False
    print("SUCCESS: Record full payment and verify PAID status.")

    # 18. Get Payments history
    status, res = make_request("/api/admin/fees/payments", "GET", token=admin_token)
    if status != 200 or len(res.get("data", [])) < 2:
        print(f"FAIL: Get payments failed: {res}")
        return False
    print("SUCCESS: Get payments history verified.")

    # 19. Login as Teacher to view fees overview
    status, res = make_request("/api/auth/login", "POST", {
        "userId": teacher_uid,
        "password": "Password123"
    })
    if status != 200:
        print("FAIL: Teacher login failed.")
        return False
    teacher_token = res["data"]["token"]
    print("SUCCESS: Teacher logged in.")

    # 20. Teacher View Fees Overview
    status, res = make_request("/api/teacher/fees", "GET", token=teacher_token)
    if status != 200 or len(res.get("data", [])) < 2:
        print(f"FAIL: Teacher fee overview failed: {res}")
        return False
    print("SUCCESS: Teacher fee overview verified.")

    # 21. Teacher View Student details
    status, res = make_request(f"/api/teacher/fees/FS001", "GET", token=teacher_token)
    if status != 200 or len(res.get("data", [])) < 1:
        print(f"FAIL: Teacher student details failed: {res}")
        return False
    print("SUCCESS: Teacher student details read-only query verified.")

    # 22. Login as Student FS001
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "fees_stud1",
        "password": "Password123"
    })
    if status != 200:
        print("FAIL: Student 1 login failed.")
        return False
    stud_token = res["data"]["token"]
    print("SUCCESS: Student 1 logged in.")

    # 23. Student view my fees
    status, res = make_request("/api/student/fees", "GET", token=stud_token)
    if status != 200 or len(res.get("data", [])) < 1:
        print(f"FAIL: Student view fees failed: {res}")
        return False
    print("SUCCESS: Student view fees verified.")

    # 24. Student view my payments
    status, res = make_request("/api/student/fees/payments", "GET", token=stud_token)
    if status != 200 or len(res.get("data", [])) < 2:
        print(f"FAIL: Student view payments failed: {res}")
        return False
    print("SUCCESS: Student view payments verified.")

    # 25. Student view notifications
    status, res = make_request("/api/student/fees/notifications", "GET", token=stud_token)
    if status != 200 or len(res.get("data", [])) < 1:
        print(f"FAIL: Student view notifications failed: {res}")
        return False
    print("SUCCESS: Student view notifications verified.")

    print("==================================================")
    print("ALL FEES MODULE INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
    print("==================================================")
    return True

if __name__ == "__main__":
    if not run_tests():
        sys.exit(1)

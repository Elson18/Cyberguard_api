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
    print("STARTING DISCUSSION MODULE VERIFICATION TESTS")
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
    class_name = "DiscussionClass"
    section = "X"
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
    teacher_uid = "disc_teacher"
    teacher_tid = "T_DISC"
    status, res = make_request("/api/admin/create-teacher", "POST", {
        "userId": teacher_uid,
        "password": "Password123",
        "name": "Teacher Bob",
        "department": "Science",
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

    # 4. Create Student
    student_uid = "disc_student"
    student_sid = "S_DISC"
    status, res = make_request("/api/admin/create-student", "POST", {
        "userId": student_uid,
        "password": "Password123",
        "name": "Student Alice",
        "classId": class_id,
        "rollNumber": "42",
        "studentId": student_sid
    }, token=admin_token)
    if status not in (200, 201) and "already exists" not in res.get("message", ""):
        print(f"FAIL: Create student failed: {res}")
        return False
    print("SUCCESS: Student verified.")

    # 5. Login as Student
    status, res = make_request("/api/auth/login", "POST", {
        "userId": student_uid,
        "password": "Password123"
    })
    if status != 200:
        print(f"FAIL: Student login failed: {res}")
        return False
    student_token = res["data"]["token"]
    print("SUCCESS: Student logged in.")

    # 6. Student creates discussion
    status, res = make_request("/api/discussions", "POST", {
        "title": "Need help in Physics",
        "category": "ACADEMIC",
        "priority": "HIGH",
        "message": "I do not understand the theory of relativity."
    }, token=student_token)
    if status not in (200, 201):
        print(f"FAIL: Create discussion failed: {res}")
        return False
    print("SUCCESS: Student created discussion.")

    # 7. Student retrieves their discussions
    status, res = make_request("/api/student/discussions", "GET", token=student_token)
    if status != 200 or len(res.get("data", [])) == 0:
        print(f"FAIL: Student get discussions failed: {res}")
        return False
    
    discussion = res["data"][0]
    disc_id = discussion["discussionId"]
    print(f"SUCCESS: Student discussions retrieved. New ID: {disc_id}")

    # Check status and priority
    if discussion["status"] != "OPEN" or discussion["priority"] != "HIGH" or discussion["category"] != "ACADEMIC":
        print(f"FAIL: Invalid fields on created discussion: {discussion}")
        return False

    # 8. Student retrieves details of the discussion
    status, res = make_request(f"/api/discussions/{disc_id}", "GET", token=student_token)
    if status != 200:
        print(f"FAIL: Student get discussion details failed: {res}")
        return False
    if len(res["data"]["messages"]) != 1 or res["data"]["messages"][0]["message"] != "I do not understand the theory of relativity.":
        print(f"FAIL: Discussion messages check failed: {res}")
        return False
    print("SUCCESS: Student retrieved discussion details and messages.")

    # 9. Login as Teacher
    status, res = make_request("/api/auth/login", "POST", {
        "userId": teacher_uid,
        "password": "Password123"
    })
    if status != 200:
        print("FAIL: Teacher login failed.")
        return False
    teacher_token = res["data"]["token"]
    print("SUCCESS: Teacher logged in.")

    # 10. Teacher views assigned discussions
    status, res = make_request("/api/teacher/discussions", "GET", token=teacher_token)
    if status != 200 or len(res.get("data", [])) == 0:
        print(f"FAIL: Teacher get discussions failed: {res}")
        return False
    print("SUCCESS: Teacher retrieved assigned discussions.")

    # 11. Teacher replies to discussion
    status, res = make_request(f"/api/teacher/discussions/{disc_id}/reply", "POST", {
        "message": "It says E=mc^2. Refer to page 45."
    }, token=teacher_token)
    if status != 200:
        print(f"FAIL: Teacher reply failed: {res}")
        return False
    print("SUCCESS: Teacher replied.")

    # Check status is now IN_PROGRESS
    status, res = make_request(f"/api/teacher/discussions/{disc_id}", "GET", token=teacher_token)
    if status != 200 or res["data"]["discussion"]["status"] != "IN_PROGRESS":
        print(f"FAIL: Status not updated to IN_PROGRESS after teacher reply: {res}")
        return False
    print("SUCCESS: Discussion status updated to IN_PROGRESS.")

    # 12. Teacher resolves discussion
    status, res = make_request(f"/api/teacher/discussions/{disc_id}/status", "PUT", {
        "status": "RESOLVED"
    }, token=teacher_token)
    if status != 200:
        print(f"FAIL: Teacher mark resolved failed: {res}")
        return False
    print("SUCCESS: Teacher marked resolved.")

    # Verify status is RESOLVED
    status, res = make_request(f"/api/teacher/discussions/{disc_id}", "GET", token=teacher_token)
    if status != 200 or res["data"]["discussion"]["status"] != "RESOLVED":
        print(f"FAIL: Discussion status is not RESOLVED: {res}")
        return False
    print("SUCCESS: Discussion status resolved.")

    # 13. Student tries to delete a resolved discussion (should fail)
    status, res = make_request(f"/api/discussions/{disc_id}", "DELETE", token=student_token)
    if status == 200 or res.get("success") is True:
        print(f"FAIL: Allowed student to delete discussion with replies/status resolved: {res}")
        return False
    print("SUCCESS: Student blocked from deleting discussion with replies/status resolved.")

    # 14. Student replies to discussion
    status, res = make_request(f"/api/discussions/{disc_id}/reply", "POST", {
        "message": "Ah, got it. Thank you!"
    }, token=student_token)
    if status != 200:
        print(f"FAIL: Student reply failed: {res}")
        return False
    print("SUCCESS: Student replied.")

    # 15. Admin views all discussions with filter
    status, res = make_request(f"/api/admin/discussions?Student={student_sid}&Status=RESOLVED", "GET", token=admin_token)
    if status != 200:
        print(f"FAIL: Admin list discussions failed: {res}")
        return False
    print("SUCCESS: Admin listed discussions with filters.")

    # 16. Admin replies to discussion
    status, res = make_request(f"/api/admin/discussions/{disc_id}/reply", "POST", {
        "message": "Closing this discussion as resolved."
    }, token=admin_token)
    if status != 200:
        print(f"FAIL: Admin reply failed: {res}")
        return False
    print("SUCCESS: Admin replied.")

    # 17. Admin closes discussion
    status, res = make_request(f"/api/admin/discussions/{disc_id}/status", "PUT", {
        "status": "CLOSED"
    }, token=admin_token)
    if status != 200:
        print(f"FAIL: Admin status close failed: {res}")
        return False
    print("SUCCESS: Admin closed discussion.")

    # 18. Student tries to reply to CLOSED discussion (should fail)
    status, res = make_request(f"/api/discussions/{disc_id}/reply", "POST", {
        "message": "Reopening?"
    }, token=student_token)
    if status == 200:
        print("FAIL: Allowed reply to CLOSED discussion.")
        return False
    print("SUCCESS: Reply to CLOSED discussion blocked.")

    # 19. Get Statistics
    status, res = make_request("/api/discussions/statistics", "GET", token=student_token)
    if status != 200 or "data" not in res:
        print(f"FAIL: Get statistics failed: {res}")
        return False
    stats = res["data"]
    if stats.get("closed") < 1:
        print(f"FAIL: Statistics not accurate: {stats}")
        return False
    print(f"SUCCESS: Statistics verified: {stats}")

    # 20. Admin deletes discussion
    status, res = make_request(f"/api/admin/discussions/{disc_id}", "DELETE", token=admin_token)
    if status != 200:
        print(f"FAIL: Admin delete discussion failed: {res}")
        return False
    print("SUCCESS: Admin deleted discussion.")

    # Verify deleted
    status, res = make_request(f"/api/discussions/{disc_id}", "GET", token=student_token)
    if status != 404:
        print(f"FAIL: Deleted discussion still accessible: {status}, {res}")
        return False
    print("SUCCESS: Verified discussion deletion.")

    # 21. Validation tests
    # Invalid category
    status, res = make_request("/api/discussions", "POST", {
        "title": "Invalid Category Test",
        "category": "SPORTS",
        "priority": "HIGH",
        "message": "test"
    }, token=student_token)
    if status != 400 or "Validation error" not in res.get("message", ""):
        print(f"FAIL: Expected validation error for invalid category: {status}, {res}")
        return False
    print("SUCCESS: Invalid category validation test passed.")

    # Empty message
    status, res = make_request("/api/discussions", "POST", {
        "title": "Invalid Message Test",
        "category": "ACADEMIC",
        "priority": "HIGH",
        "message": "   "
    }, token=student_token)
    if status != 400 or "Validation error" not in res.get("message", ""):
        print(f"FAIL: Expected validation error for empty message: {status}, {res}")
        return False
    print("SUCCESS: Empty message validation test passed.")

    print("==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
    return True

if __name__ == "__main__":
    if not run_tests():
        sys.exit(1)

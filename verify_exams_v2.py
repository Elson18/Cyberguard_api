import json
import urllib.request
import urllib.error
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
    print("Starting Phase 3 verification tests for Exams, PDF & Dashboard...")
    
    # 1. Login as Super Admin
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "admin",
        "password": "Admin@123"
    })
    print(f"Admin Login: {status}")
    if status != 200:
        print("FAIL: Super Admin login failed.")
        return False
    admin_token = res["data"]["token"]
    
    # Clean up previous exam run
    make_request("/api/exams/EXM_TEST_V2", "DELETE", token=admin_token)
    
    # Resolve class ID
    status, cls_res = make_request("/api/classes", "GET", token=admin_token)
    class_id = None
    for cls in cls_res.get("data", []):
        if cls.get("className") == "Class 11" and cls.get("section") == "B":
            class_id = cls["_id"]
            break
            
    if not class_id:
        print("FAIL: Class 11-B not found. Ensure previous verification scripts ran.")
        return False
        
    # Resolve subjects
    status, subs_res = make_request("/api/subjects", "GET", token=admin_token)
    sub_maths_id = None
    sub_science_id = None
    for s in subs_res.get("data", []):
        if s.get("subjectName") == "Maths 11":
            sub_maths_id = s["_id"]
        elif s.get("subjectName") == "Science 11":
            sub_science_id = s["_id"]
            
    # Login as Teacher 2
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "teacher2",
        "password": "Password@123"
    })
    teacher_token = res["data"]["token"]
    
    # 2. Validation Checks: PassMarks > MaxMarks
    invalid_payload = {
        "examId": "EXM_TEST_V2",
        "examName": "Final Term 11",
        "classId": class_id,
        "academicYear": "2026",
        "term": "Term 2",
        "maxMarks": 100,
        "passMarks": 120, # Invalid!
        "startDate": "2026-11-01",
        "endDate": "2026-11-10"
    }
    status, res = make_request("/api/exams", "POST", invalid_payload, token=teacher_token)
    print(f"Validation (PassMarks > MaxMarks) Status: {status}, Msg: {res.get('message')}")
    if status == 201 or status == 200:
        print("FAIL: Validation should block passMarks > maxMarks.")
        return False
        
    # Validation Checks: Invalid Date
    invalid_date_payload = invalid_payload.copy()
    invalid_date_payload["passMarks"] = 35
    invalid_date_payload["startDate"] = "invalid-date"
    status, res = make_request("/api/exams", "POST", invalid_date_payload, token=teacher_token)
    print(f"Validation (Invalid Date Format) Status: {status}, Msg: {res.get('message')}")
    if status == 201 or status == 200:
        print("FAIL: Validation should block incorrect date formats.")
        return False
        
    # 3. Create Valid Exam
    valid_payload = invalid_payload.copy()
    valid_payload["passMarks"] = 35
    valid_payload["startDate"] = "2026-11-01"
    valid_payload["endDate"] = "2026-11-10"
    status, res = make_request("/api/exams", "POST", valid_payload, token=teacher_token)
    print(f"Create Valid Exam Status: {status}")
    if status != 201:
        print("FAIL: Valid exam creation failed.")
        return False
        
    # 4. Duplicate Exam check
    status, res = make_request("/api/exams", "POST", valid_payload, token=teacher_token)
    print(f"Create Duplicate Exam Status: {status}, Msg: {res.get('message')}")
    if status == 201 or status == 200:
        print("FAIL: Duplicate exam checking failed.")
        return False
        
    # 5. Bulk enter draft marks
    bulk_payload = {
        "students": [
            {
                "studentId": "student3",
                "subjects": [
                    {"subjectId": sub_maths_id, "marks": 85},
                    {"subjectId": sub_science_id, "marks": 75}
                ]
            },
            {
                "studentId": "student4",
                "subjects": [
                    {"subjectId": sub_maths_id, "marks": 60},
                    {"subjectId": sub_science_id, "marks": 50}
                ]
            }
        ]
    }
    status, res = make_request("/api/exams/EXM_TEST_V2/marks/bulk", "POST", bulk_payload, token=teacher_token)
    print(f"Bulk Marks Entry Status: {status}")
    
    # 6. Single Student Update (PUT /api/exams/{examId}/students/{studentId})
    # Update student3 Science to 95 and Maths to 98
    update_student_payload = {
        "subjects": [
            {"subjectId": sub_maths_id, "marks": 98},
            {"subjectId": sub_science_id, "marks": 95}
        ]
    }
    status, res = make_request("/api/exams/EXM_TEST_V2/students/student3", "PUT", update_student_payload, token=teacher_token)
    print(f"Update Student 3 Marks Status: {status}")
    if status != 200:
        print("FAIL: Single student update failed.")
        return False
        
    # Verify Single Student limits checking: marks > maxMarks
    invalid_marks_payload = {
        "subjects": [
            {"subjectId": sub_maths_id, "marks": 150} # > maxMarks
        ]
    }
    status, res = make_request("/api/exams/EXM_TEST_V2/students/student3", "PUT", invalid_marks_payload, token=teacher_token)
    print(f"Update Student Marks (> MaxMarks) Status: {status}, Msg: {res.get('message')}")
    if status == 200:
        print("FAIL: Marks limit validation failed.")
        return False
        
    # Verify Single Student limits checking: negative marks
    invalid_neg_payload = {
        "subjects": [
            {"subjectId": sub_maths_id, "marks": -5} # negative
        ]
    }
    status, res = make_request("/api/exams/EXM_TEST_V2/students/student3", "PUT", invalid_neg_payload, token=teacher_token)
    print(f"Update Student Marks (Negative Marks) Status: {status}, Msg: {res.get('message')}")
    if status == 200:
        print("FAIL: Negative marks validation failed.")
        return False
        
    # 7. Delete restrictions test (Status DRAFT but contains marks)
    status, res = make_request("/api/exams/EXM_TEST_V2", "DELETE", token=teacher_token)
    print(f"Delete Exam with Marks (Teacher) Status: {status}, Msg: {res.get('message')}")
    if status == 200:
        print("FAIL: Teachers should not be allowed to delete exams containing marks data.")
        return False
        
    # 8. Publish Exam (calculates totals, percentage, grade, rank, saves report cards and locks exam)
    status, res = make_request("/api/exams/EXM_TEST_V2/publish", "POST", token=teacher_token)
    print(f"Publish Exam Status: {status}")
    if status != 200:
        print("FAIL: Publish failed.")
        return False
        
    # Confirm locked status
    status, res = make_request("/api/exams/EXM_TEST_V2", "GET", token=teacher_token)
    print(f"Exam status after publish: {res.get('data', {}).get('status')}")
    if res.get("data", {}).get("status") != "LOCKED":
        print("FAIL: Exam status should be LOCKED.")
        return False
        
    # 9. Verify Stats Endpoint returns Top 10
    status, res = make_request("/api/exams/EXM_TEST_V2/statistics", "GET", token=teacher_token)
    print(f"Statistics Status: {status}")
    top_students = res.get("data", {}).get("topStudents", [])
    print(f"Top Students count: {len(top_students)}")
    if not top_students:
        print("FAIL: Statistics top student lists missing.")
        return False
        
    # 10. Login as Student 3
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "student3",
        "password": "Password@123"
    })
    print(f"Student 3 Login Status: {status}")
    student_token = res["data"]["token"]
    
    # 11. Student Dashboard View
    status, res = make_request("/api/student/dashboard", "GET", token=student_token)
    print(f"Student Dashboard Status: {status}")
    dashboard_data = res.get("data", {})
    if status != 200 or not dashboard_data.get("latestExam") or not dashboard_data.get("summary"):
        print("FAIL: Student dashboard data loading failed.")
        return False
    print(f"Dashboard Stats: Total Exams={dashboard_data['summary']['totalExams']}, Pass Rate={dashboard_data['summary']['passRate']}%")
    
    # 12. Student PDF Download
    url = f"{BASE_URL}/api/student/report-card/pdf/EXM_TEST_V2"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {student_token}"})
    try:
        with urllib.request.urlopen(req) as pdf_res:
            content_type = pdf_res.headers.get("Content-Type")
            pdf_bytes = pdf_res.read()
            print(f"PDF Download status: {pdf_res.status}, MimeType: {content_type}, Size: {len(pdf_bytes)} bytes")
            if pdf_res.status != 200 or content_type != "application/pdf" or len(pdf_bytes) < 1000:
                print("FAIL: PDF report card download failed or returned invalid bytes.")
                return False
    except Exception as e:
        print(f"FAIL: PDF download request exception: {e}")
        return False
        
    print("PASS: Report Card PDF successfully compiled, downloaded, and verified.")
    
    # 13. Super Admin Unlock
    status, res = make_request("/api/exams/EXM_TEST_V2/unlock", "POST", token=admin_token)
    print(f"Super Admin Unlock Status: {status}")
    if status != 200:
        print("FAIL: Unlock failed.")
        return False
        
    # Verify status changed back to DRAFT
    status, res = make_request("/api/exams/EXM_TEST_V2", "GET", token=teacher_token)
    print(f"Exam status after unlocking: {res.get('data', {}).get('status')}")
    if res.get("data", {}).get("status") != "DRAFT":
        print("FAIL: Unlocked exam should change status back to DRAFT.")
        return False
        
    print("SUCCESS: All Phase 3 Exam, Dashboard, and PDF verification tests passed successfully!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

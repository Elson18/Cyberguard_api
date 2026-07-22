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
    print("Starting Phase 2 verification tests for Exam Management...")
    
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
    
    # Clean up previous exam runs to make test repeatable
    make_request("/api/exams/EXM_TEST_001", "DELETE", token=admin_token)
    
    # 2. Create Class
    status, res = make_request("/api/admin/create-class", "POST", {
        "className": "Class 11",
        "section": "B"
    }, token=admin_token)
    print(f"Create Class: {status}")
    class_id = res.get("data", {}).get("_id")
    if not class_id:
        # Resolve class ID
        status, cls_res = make_request("/api/classes", "GET", token=admin_token)
        for cls in cls_res.get("data", []):
            if cls.get("className") == "Class 11" and cls.get("section") == "B":
                class_id = cls["_id"]
                break
    print(f"Class 11 ID: {class_id}")
    
    # 3. Create Subjects
    status, res = make_request("/api/admin/create-subject", "POST", {
        "subjectName": "Maths 11"
    }, token=admin_token)
    sub_maths_id = res.get("data", {}).get("_id")
    if not sub_maths_id:
        status, subs_res = make_request("/api/subjects", "GET", token=admin_token)
        for s in subs_res.get("data", []):
            if s.get("subjectName") == "Maths 11":
                sub_maths_id = s["_id"]
                break
                
    status, res = make_request("/api/admin/create-subject", "POST", {
        "subjectName": "Science 11"
    }, token=admin_token)
    sub_science_id = res.get("data", {}).get("_id")
    if not sub_science_id:
        status, subs_res = make_request("/api/subjects", "GET", token=admin_token)
        for s in subs_res.get("data", []):
            if s.get("subjectName") == "Science 11":
                sub_science_id = s["_id"]
                break
    print(f"Subjects: Maths={sub_maths_id}, Science={sub_science_id}")
    
    # 4. Create Teacher
    status, res = make_request("/api/admin/create-teacher", "POST", {
        "userId": "teacher2",
        "password": "Password@123",
        "name": "Jane Roe",
        "department": "Science Department",
        "teacherId": "teacher2"
    }, token=admin_token)
    print(f"Create Teacher: {status}")
    
    # Assign teacher to class
    status, res = make_request("/api/admin/assign-teacher", "POST", {
        "teacherId": "teacher2",
        "classId": class_id
    }, token=admin_token)
    print(f"Assign Teacher: {status}")
    
    # 5. Create Students
    # student3
    status, res = make_request("/api/admin/create-student", "POST", {
        "userId": "student3",
        "password": "Password@123",
        "name": "Charlie Brown",
        "classId": class_id,
        "rollNumber": "201",
        "studentId": "student3"
    }, token=admin_token)
    # student4
    status, res = make_request("/api/admin/create-student", "POST", {
        "userId": "student4",
        "password": "Password@123",
        "name": "Diana Prince",
        "classId": class_id,
        "rollNumber": "202",
        "studentId": "student4"
    }, token=admin_token)
    # student5
    status, res = make_request("/api/admin/create-student", "POST", {
        "userId": "student5",
        "password": "Password@123",
        "name": "Ethan Hunt",
        "classId": class_id,
        "rollNumber": "203",
        "studentId": "student5"
    }, token=admin_token)
    print("Students student3, student4, student5 created.")
    
    # 6. Login as Teacher 2
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "teacher2",
        "password": "Password@123"
    })
    print(f"Teacher 2 Login: {status}")
    teacher_token = res["data"]["token"]
    
    # 7. Create Exam
    exam_payload = {
        "examId": "EXM_TEST_001",
        "examName": "Mid Term 11",
        "classId": class_id,
        "academicYear": "2026",
        "term": "Term 1",
        "maxMarks": 100,
        "passMarks": 40
    }
    status, res = make_request("/api/exams", "POST", exam_payload, token=teacher_token)
    print(f"Create Exam Status: {status}, Response: {res}")
    if status != 201 and "already exists" not in res.get("message", ""):
        print("FAIL: Exam creation failed.")
        return False
        
    # Verify GET single and list
    status, res = make_request("/api/exams/EXM_TEST_001", "GET", token=teacher_token)
    print(f"Get single exam: {status}, status = {res.get('data', {}).get('status')}")
    
    # 8. Bulk Save Marks
    bulk_marks_payload = {
        "students": [
            {
                "studentId": "student3",
                "subjects": [
                    {"subjectId": sub_maths_id, "marks": 90},
                    {"subjectId": sub_science_id, "marks": 80}
                ]
            },
            {
                "studentId": "student4",
                "subjects": [
                    {"subjectId": sub_maths_id, "marks": 90},
                    {"subjectId": sub_science_id, "marks": 80}
                ]
            },
            {
                "studentId": "student5",
                "subjects": [
                    {"subjectId": sub_maths_id, "marks": 70},
                    {"subjectId": sub_science_id, "marks": 75}
                ]
            }
        ]
    }
    status, res = make_request("/api/exams/EXM_TEST_001/marks/bulk", "POST", bulk_marks_payload, token=teacher_token)
    print(f"Bulk Save Marks Status: {status}, Response: {res}")
    if status != 200:
        print("FAIL: Bulk save marks failed.")
        return False
        
    # 9. Get Mark Entry Sheet
    status, res = make_request("/api/exams/EXM_TEST_001/marksheet", "GET", token=teacher_token)
    print(f"Get Marksheet Status: {status}")
    if status != 200 or len(res.get("data", {}).get("existingMarks", [])) < 6:
        print("FAIL: Marksheet loading failed or missing entries.")
        return False
        
    # 10. Publish Exam
    status, res = make_request("/api/exams/EXM_TEST_001/publish", "POST", token=teacher_token)
    print(f"Publish Exam Status: {status}")
    if status != 200:
        print("FAIL: Publish failed.")
        return False
        
    # 11. Verify Dense Rankings
    status, res = make_request(f"/api/teacher/rankings/{class_id}?exam=Mid%20Term%2011&academicYear=2026", "GET", token=teacher_token)
    print(f"Get class rankings: {status}")
    rankings = res.get("data", [])
    print(f"Rankings Count: {len(rankings)}")
    for r in rankings:
        print(f"Student: {r['name']}, Total: {r['totalMarks']}, Rank: {r['rank']}, Grade: {r['grade']}, Passed: {r['passed']}")
        
    # Verify rankings logic:
    # student3 and student4 should have Rank 1 (total 170)
    # student5 should have Rank 2 (total 145) -> Dense Ranking!
    ranks = {r["studentId"]: r["rank"] for r in rankings}
    if ranks.get("student3") != 1 or ranks.get("student4") != 1 or ranks.get("student5") != 2:
        print("FAIL: Dense ranking logic check failed. Ranks received:", ranks)
        return False
    print("PASS: Dense ranking verified (Rank 1, 1, 2).")
    
    # 12. Attempt edit when published (should fail)
    status, res = make_request("/api/exams/EXM_TEST_001/marks/bulk", "POST", bulk_marks_payload, token=teacher_token)
    print(f"Attempt edit when published Status: {status}, Response: {res}")
    if status == 200:
        print("FAIL: Edits should not be allowed on published exam.")
        return False
        
    # 13. Super Admin Unlock
    status, res = make_request("/api/exams/EXM_TEST_001/unlock", "POST", token=admin_token)
    print(f"Super Admin Unlock Status: {status}")
    if status != 200:
        print("FAIL: Unlock failed.")
        return False
        
    # 14. Teacher edits marks after unlock
    # student5 Maths -> 85 (new total: 160)
    edit_payload = {
        "students": [
            {
                "studentId": "student5",
                "subjects": [
                    {"subjectId": sub_maths_id, "marks": 85}
                ]
            }
        ]
    }
    status, res = make_request("/api/exams/EXM_TEST_001/marks/bulk", "POST", edit_payload, token=teacher_token)
    print(f"Edit after unlock Status: {status}")
    if status != 200:
        print("FAIL: Save failed after unlocking.")
        return False
        
    # Re-publish to update stats
    status, res = make_request("/api/exams/EXM_TEST_001/publish", "POST", token=teacher_token)
    
    # 15. Verify statistics endpoint
    status, res = make_request("/api/exams/EXM_TEST_001/statistics", "GET", token=teacher_token)
    print(f"Statistics Status: {status}")
    stats = res.get("data", {})
    print(f"Stats: Highest={stats.get('highestMark')}, Lowest={stats.get('lowestMark')}, Avg={stats.get('average')}")
    print(f"Stats Grade Dist: {stats.get('gradeDistribution')}")
    print(f"Stats Subject Avgs: {stats.get('subjectWiseAverage')}")
    
    if stats.get("highestMark") != 170.0 or stats.get("lowestMark") != 160.0:
        print("FAIL: Incorrect stats calculation.")
        return False
        
    print("SUCCESS: All Phase 2 Exam Management tests passed successfully!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

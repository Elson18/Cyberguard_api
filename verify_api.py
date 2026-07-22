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

def test_flow():
    print("Starting integration verification tests...")
    
    # 1. Login as Super Admin
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "admin",
        "password": "Admin@123"
    })
    print(f"Admin Login Status: {status}, Response: {res}")
    if status != 200:
        print("FAIL: Super Admin login failed. Is Flask running and seeded?")
        return False
        
    admin_token = res["data"]["token"]
    
    # 2. Create Class
    status, res = make_request("/api/admin/create-class", "POST", {
        "className": "Class 10",
        "section": "A"
    }, token=admin_token)
    print(f"Create Class Status: {status}, Response: {res}")
    if status not in (200, 201) and "already exists" not in res.get("message", ""):
        print("FAIL: Create Class failed.")
        return False
        
    # Resolve the class _id
    class_id = res.get("data", {}).get("_id")
    if not class_id:
        status, cls_list_res = make_request("/api/classes", "GET", token=admin_token)
        for cls in cls_list_res.get("data", []):
            if cls.get("className") == "Class 10" and cls.get("section") == "A":
                class_id = cls.get("_id")
                break
    print(f"Class ID: {class_id}")
    if not class_id:
        print("FAIL: Could not determine Class ID.")
        return False
        
    # 3. Create Subject Mathematics
    status, res = make_request("/api/admin/create-subject", "POST", {
        "subjectName": "Mathematics"
    }, token=admin_token)
    print(f"Create Subject Status: {status}, Response: {res}")
    subject_id = res.get("data", {}).get("_id")
    if not subject_id:
        status, sub_list_res = make_request("/api/subjects", "GET", token=admin_token)
        for sub in sub_list_res.get("data", []):
            if sub.get("subjectName") == "Mathematics":
                subject_id = sub.get("_id")
                break
    print(f"Subject ID (Mathematics): {subject_id}")
    
    # Create Subject Science
    status, res2 = make_request("/api/admin/create-subject", "POST", {
        "subjectName": "Science"
    }, token=admin_token)
    print(f"Create Subject Science Status: {status}, Response: {res2}")
    subject_id_sci = res2.get("data", {}).get("_id")
    if not subject_id_sci:
        status, sub_list_res = make_request("/api/subjects", "GET", token=admin_token)
        for sub in sub_list_res.get("data", []):
            if sub.get("subjectName") == "Science":
                subject_id_sci = sub.get("_id")
                break
    print(f"Subject ID (Science): {subject_id_sci}")

    if not subject_id or not subject_id_sci:
        print("FAIL: Could not determine Subject IDs.")
        return False

    # 4. Create Teacher
    status, res = make_request("/api/admin/create-teacher", "POST", {
        "userId": "teacher1",
        "password": "Password@123",
        "name": "John Doe",
        "department": "Science & Maths"
    }, token=admin_token)
    print(f"Create Teacher Status: {status}, Response: {res}")
    
    # 5. Assign Teacher to Class
    status, res = make_request("/api/admin/assign-teacher", "POST", {
        "teacherId": "teacher1",
        "classId": class_id
    }, token=admin_token)
    print(f"Assign Teacher Status: {status}, Response: {res}")
    if status != 200:
        print("FAIL: Assign Teacher failed.")
        return False
        
    # 6. Create Student 1 (Alice)
    status, res = make_request("/api/admin/create-student", "POST", {
        "userId": "student1",
        "password": "Password@123",
        "name": "Alice Smith",
        "classId": class_id,
        "rollNumber": "101"
    }, token=admin_token)
    print(f"Create Student 1 Status: {status}, Response: {res}")
    
    # 7. Create Student 2 (Bob)
    status, res = make_request("/api/admin/create-student", "POST", {
        "userId": "student2",
        "password": "Password@123",
        "name": "Bob Jones",
        "classId": class_id,
        "rollNumber": "102"
    }, token=admin_token)
    print(f"Create Student 2 Status: {status}, Response: {res}")
    
    # 8. Login as Teacher
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "teacher1",
        "password": "Password@123"
    })
    print(f"Teacher Login Status: {status}, Response: {res}")
    if status != 200:
        print("FAIL: Teacher login failed.")
        return False
    teacher_token = res["data"]["token"]
    
    # 9. Enter Marks for Student 1 (Alice)
    # Math: 95, Science: 85 -> Total: 180
    status, res = make_request("/api/marks", "POST", {
        "studentId": "student1",
        "classId": class_id,
        "subjectId": subject_id,
        "exam": "Final",
        "marks": 95,
        "academicYear": "2026"
    }, token=teacher_token)
    print(f"Enter Student 1 Math Marks Status: {status}, Response: {res}")
    
    status, res = make_request("/api/marks", "POST", {
        "studentId": "student1",
        "classId": class_id,
        "subjectId": subject_id_sci,
        "exam": "Final",
        "marks": 85,
        "academicYear": "2026"
    }, token=teacher_token)
    print(f"Enter Student 1 Science Marks Status: {status}, Response: {res}")
    
    # 10. Enter Marks for Student 2 (Bob)
    # Math: 70, Science: 80 -> Total: 150
    status, res = make_request("/api/marks", "POST", {
        "studentId": "student2",
        "classId": class_id,
        "subjectId": subject_id,
        "exam": "Final",
        "marks": 70,
        "academicYear": "2026"
    }, token=teacher_token)
    print(f"Enter Student 2 Math Marks Status: {status}, Response: {res}")
    
    status, res = make_request("/api/marks", "POST", {
        "studentId": "student2",
        "classId": class_id,
        "subjectId": subject_id_sci,
        "exam": "Final",
        "marks": 80,
        "academicYear": "2026"
    }, token=teacher_token)
    print(f"Enter Student 2 Science Marks Status: {status}, Response: {res}")
    
    # 11. Publish Marks
    status, res = make_request("/api/marks/publish", "POST", {
        "classId": class_id,
        "exam": "Final",
        "academicYear": "2026"
    }, token=teacher_token)
    print(f"Publish Marks Status: {status}, Response: {res}")
    if status != 200:
        print("FAIL: Publish Marks failed.")
        return False
        
    # 12. Check Rankings (from teacher side)
    status, res = make_request(f"/api/teacher/rankings/{class_id}?exam=Final&academicYear=2026", "GET", token=teacher_token)
    print(f"Teacher view Rankings Status: {status}, Response: {res}")
    if status != 200 or len(res.get("data", [])) < 2:
        print("FAIL: View rankings returned incorrect data.")
        return False
        
    rankings = res["data"]
    print(f"Rank 1: {rankings[0]['name']} (Rank: {rankings[0]['rank']}, Total: {rankings[0]['totalMarks']})")
    print(f"Rank 2: {rankings[1]['name']} (Rank: {rankings[1]['rank']}, Total: {rankings[1]['totalMarks']})")
    
    if rankings[0]["studentId"] != "student1" or rankings[0]["rank"] != 1:
        print("FAIL: Ranking sorting or values are incorrect.")
        return False
        
    # 13. Login as Student 2 (Bob)
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "student2",
        "password": "Password@123"
    })
    print(f"Student 2 Login Status: {status}, Response: {res}")
    student_token = res["data"]["token"]
    
    # Retrieve Bob's marks to find mark IDs
    status, res = make_request("/api/student/marks?exam=Final&academicYear=2026", "GET", token=student_token)
    print(f"Student 2 View Marks: {res}")
    bob_math_mark_id = None
    bob_sci_mark_id = None
    for mark in res.get("data", []):
        if mark.get("subjectId") == subject_id:
            bob_math_mark_id = mark.get("_id")
        elif mark.get("subjectId") == subject_id_sci:
            bob_sci_mark_id = mark.get("_id")
            
    print(f"Bob Math Mark ID: {bob_math_mark_id}, Science ID: {bob_sci_mark_id}")
    
    # Edit Bob's marks to make him beat Alice: Math -> 100, Science -> 90 (Bob Total: 190)
    status, res = make_request(f"/api/marks/{bob_math_mark_id}", "PUT", {
        "marks": 100
    }, token=teacher_token)
    print(f"Edit Marks (Bob Math -> 100) Status: {status}, Response: {res}")
    
    status, res = make_request(f"/api/marks/{bob_sci_mark_id}", "PUT", {
        "marks": 90
    }, token=teacher_token)
    print(f"Edit Marks (Bob Science -> 90) Status: {status}, Response: {res}")
    
    # Now check rankings again! Since we updated Bob's marks, rankings should update automatically!
    status, res = make_request(f"/api/teacher/rankings/{class_id}?exam=Final&academicYear=2026", "GET", token=teacher_token)
    rankings = res.get("data", [])
    print(f"New Rank 1: {rankings[0]['name']} (Rank: {rankings[0]['rank']}, Total: {rankings[0]['totalMarks']})")
    print(f"New Rank 2: {rankings[1]['name']} (Rank: {rankings[1]['rank']}, Total: {rankings[1]['totalMarks']})")
    
    if rankings[0]["studentId"] != "student2" or rankings[0]["rank"] != 1:
        print("FAIL: Auto-update of rankings failed or incorrect ranking assigned.")
        return False
        
    # 14. Verify student profile view, report card, and rank
    status, res = make_request("/api/student/profile", "GET", token=student_token)
    print(f"Student Profile Status: {status}, Response: {res}")
    if status != 200 or res["data"]["name"] != "Bob Jones":
        print("FAIL: Student Profile view failed.")
        return False
        
    status, res = make_request("/api/student/report-card?exam=Final&academicYear=2026", "GET", token=student_token)
    print(f"Student Report Card Status: {status}, Response: {res}")
    if status != 200 or not res["data"] or res["data"][0]["rank"] != 1:
        print("FAIL: Student Report Card view failed or rank incorrect.")
        return False
        
    status, res = make_request("/api/student/rank?exam=Final&academicYear=2026", "GET", token=student_token)
    print(f"Student Rank View Status: {status}, Response: {res}")
    if status != 200 or not res["data"] or res["data"][0]["rank"] != 1:
        print("FAIL: Student Rank view failed.")
        return False
        
    print("SUCCESS: All verification flows passed successfully!")
    return True

if __name__ == "__main__":
    success = test_flow()
    sys.exit(0 if success else 1)

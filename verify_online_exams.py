import json
import urllib.request
import urllib.error
import sys
import time

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
    print("=" * 70)
    print("STARTING ONLINE EXAMINATION MODULE VERIFICATION TESTS")
    print("=" * 70)
    
    # 1. Login as Super Admin
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "admin",
        "password": "Admin@123"
    })
    print(f"[Admin Login] Status: {status}")
    if status != 200:
        print("FAIL: Super Admin login failed.")
        return False
    admin_token = res["data"]["token"]
    
    # 2. Setup Class (Class 10A) and Subject (Maths 10)
    # Get existing classes
    status, cls_res = make_request("/api/classes", "GET", token=admin_token)
    class_id = None
    for cls in cls_res.get("data", []):
        if cls.get("className") == "Class 10A":
            class_id = cls["_id"]
            break
            
    if not class_id:
        status, res = make_request("/api/admin/create-class", "POST", {
            "className": "Class 10A",
            "section": "A"
        }, token=admin_token)
        print(f"[Create Class 10A] Status: {status}")
        class_id = res.get("data", {}).get("_id")
        
    # Get existing subjects
    status, sub_res = make_request("/api/subjects", "GET", token=admin_token)
    sub_id = None
    for s in sub_res.get("data", []):
        if s.get("subjectName") == "Maths 10":
            sub_id = s["_id"]
            break
            
    if not sub_id:
        status, res = make_request("/api/admin/create-subject", "POST", {
            "subjectName": "Maths 10"
        }, token=admin_token)
        print(f"[Create Subject Maths 10] Status: {status}")
        sub_id = res.get("data", {}).get("_id")
        
    print(f"Class ID: {class_id}, Subject ID: {sub_id}")

    # 3. Create Teacher & Student for testing
    # Teacher
    status, res = make_request("/api/admin/create-teacher", "POST", {
        "userId": "teacher_test",
        "password": "Password@123",
        "name": "John Doe",
        "department": "Mathematics",
        "teacherId": "teacher_test"
    }, token=admin_token)
    print(f"[Create Teacher] Status: {status}")
    
    # Assign teacher to Class 10A
    status, res = make_request("/api/admin/assign-teacher", "POST", {
        "teacherId": "teacher_test",
        "classId": class_id
    }, token=admin_token)
    print(f"[Assign Teacher] Status: {status}")
    
    # Student
    status, res = make_request("/api/admin/create-student", "POST", {
        "userId": "student_test",
        "password": "Password@123",
        "name": "Alice Smith",
        "classId": class_id,
        "rollNumber": "101",
        "studentId": "student_test"
    }, token=admin_token)
    print(f"[Create Student] Status: {status}")
    
    # 4. Create Online Exam Validation Checks (Errors)
    exam_id = f"EXAM_ON_TEST_{int(time.time())}"
    
    # Validation Check A: startDateTime after endDateTime
    payload_invalid_date = {
        "examId": exam_id,
        "title": "Maths Unit Test 1",
        "subjectId": sub_id,
        "classIds": [class_id],
        "academicYear": "2026-2027",
        "duration": 60,
        "passingMarks": 12,
        "startDateTime": "2026-09-10T10:00:00Z",
        "endDateTime": "2026-09-10T09:00:00Z", # Invalid!
        "instructions": "Attempt all questions.",
        "questions": [
            {
                "question": "What is 15 x 5?",
                "type": "MCQ",
                "options": ["55", "65", "75", "85"],
                "correctAnswer": "75",
                "marks": 5
            }
        ]
    }
    status, res = make_request("/api/admin/exams", "POST", payload_invalid_date, token=admin_token)
    print(f"[Validate startDateTime < endDateTime] Status: {status}, Msg: {res.get('message')}")
    if status == 201 or status == 200:
        print("FAIL: Validation should block startDateTime after endDateTime.")
        return False
        
    # Validation Check B: MCQ with less than two options
    payload_invalid_mcq = payload_invalid_date.copy()
    payload_invalid_mcq["endDateTime"] = "2026-09-10T11:00:00Z"
    payload_invalid_mcq["questions"] = [
        {
            "question": "What is 15 x 5?",
            "type": "MCQ",
            "options": ["75"], # Invalid!
            "correctAnswer": "75",
            "marks": 5
        }
    ]
    status, res = make_request("/api/admin/exams", "POST", payload_invalid_mcq, token=admin_token)
    print(f"[Validate MCQ Options >= 2] Status: {status}, Msg: {res.get('message')}")
    if status == 201 or status == 200:
        print("FAIL: Validation should block MCQ with < 2 options.")
        return False

    # Validation Check C: Multiple Select with less than two correct answers
    payload_invalid_ms = payload_invalid_date.copy()
    payload_invalid_ms["endDateTime"] = "2026-09-10T11:00:00Z"
    payload_invalid_ms["questions"] = [
        {
            "question": "Select primes.",
            "type": "MULTIPLE_SELECT",
            "options": ["2", "3", "4", "6"],
            "correctAnswer": "2", # Invalid! Must be at least 2 correct answers
            "marks": 5
        }
    ]
    status, res = make_request("/api/admin/exams", "POST", payload_invalid_ms, token=admin_token)
    print(f"[Validate MULTIPLE_SELECT correct answers >= 2] Status: {status}, Msg: {res.get('message')}")
    if status == 201 or status == 200:
        print("FAIL: Validation should block Multiple Select with < 2 correct answers.")
        return False

    # 5. Create Valid Online Exam
    # Current testing window: start in past, end in future so student can take it now
    now_epoch = int(time.time())
    start_dt = datetime.fromtimestamp(now_epoch - 3600, timezone.utc).isoformat().replace("+00:00", "Z")
    end_dt = datetime.fromtimestamp(now_epoch + 3600, timezone.utc).isoformat().replace("+00:00", "Z")

    valid_payload = {
        "examId": exam_id,
        "title": "Mathematics Online Test",
        "subjectId": sub_id,
        "classIds": [class_id],
        "academicYear": "2026-2027",
        "duration": 60,
        "passingMarks": 10,
        "startDateTime": start_dt,
        "endDateTime": end_dt,
        "instructions": "All objective questions.",
        "questions": [
            {
                "question": "What is 15 x 5?",
                "type": "MCQ",
                "options": ["55", "65", "75", "85"],
                "correctAnswer": "75",
                "marks": 5,
                "negativeMarks": 1,
                "explanation": "15 times 5 is 75."
            },
            {
                "question": "The sun rises in the east.",
                "type": "TRUE_FALSE",
                "options": ["True", "False"],
                "correctAnswer": "True",
                "marks": 5,
                "negativeMarks": 0,
                "explanation": "Scientific fact."
            },
            {
                "question": "Select prime numbers.",
                "type": "MULTIPLE_SELECT",
                "options": ["2", "3", "4", "6"],
                "correctAnswer": ["2", "3"],
                "marks": 10,
                "negativeMarks": 2,
                "explanation": "2 and 3 are prime."
            }
        ]
    }
    status, res = make_request("/api/admin/exams", "POST", valid_payload, token=admin_token)
    print(f"[Create Valid Online Exam] Status: {status}")
    if status != 201:
        print(f"FAIL: Exam creation failed. Msg: {res.get('message')}")
        return False
        
    # Check duplicate titles
    status, res_dup = make_request("/api/admin/exams", "POST", valid_payload, token=admin_token)
    print(f"[Duplicate Exam Title Check] Status: {status}, Msg: {res_dup.get('message')}")
    if status == 201 or status == 200:
        print("FAIL: Duplicate titles should be blocked.")
        return False

    # 6. Update Exam in DRAFT mode
    status, res = make_request(f"/api/admin/exams/{exam_id}", "PUT", {
        "instructions": "Updated: Answer all questions carefully."
    }, token=admin_token)
    print(f"[Update Exam in DRAFT] Status: {status}")
    if status != 200:
        print("FAIL: Updating exam in DRAFT failed.")
        return False

    # 7. Publish Exam
    status, res = make_request(f"/api/admin/exams/{exam_id}/publish", "POST", token=admin_token)
    print(f"[Publish Exam] Status: {status}")
    if status != 200:
        print("FAIL: Publishing exam failed.")
        return False

    # Verify update is now disabled
    status, res = make_request(f"/api/admin/exams/{exam_id}", "PUT", {
        "instructions": "Fail update"
    }, token=admin_token)
    print(f"[Validate Update Blocked in PUBLISHED] Status: {status}, Msg: {res.get('message')}")
    if status == 200:
        print("FAIL: Updates should be disabled after publication.")
        return False

    # 8. Student Login & Exams retrieval
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "student_test",
        "password": "Password@123"
    })
    print(f"[Student Login] Status: {status}")
    student_token = res["data"]["token"]

    status, res = make_request("/api/student/exams", "GET", token=student_token)
    print(f"[Student Retrieve Exams] Status: {status}, Count: {len(res.get('data', []))}")
    found = False
    for ex in res.get("data", []):
        if ex.get("examId") == exam_id:
            found = True
            break
    if not found:
        print("FAIL: Student did not receive the published exam.")
        return False

    # 9. Student Start Exam Attempt
    status, res = make_request(f"/api/student/exams/{exam_id}/start", "POST", token=student_token)
    print(f"[Student Start Exam] Status: {status}")
    if status not in [200, 201]:
        print("FAIL: Student failed to start the exam.")
        return False

    # 10. Student Retrieve Questions (Strips correct Answers/Explanations/Marks)
    status, res_questions = make_request(f"/api/student/exams/{exam_id}", "GET", token=student_token)
    print(f"[Student Get Questions] Status: {status}")
    if status != 200:
        print("FAIL: Student could not fetch exam questions.")
        return False
        
    for q in res_questions.get("data", []):
        if "correctAnswer" in q or "explanation" in q or "marks" in q:
            print("FAIL: Sensitive fields (correctAnswer, explanation, marks) were leaked to student!")
            return False
    print("SUCCESS: Question security details correctly stripped.")

    # 11. Student Save Answers (Auto-Save)
    # Question 1: MCQ - Correct answer "75"
    q1_id = res_questions["data"][0]["questionId"]
    status, res = make_request(f"/api/student/exams/{exam_id}/save-answer", "POST", {
        "questionId": q1_id,
        "selectedAnswer": "75"
    }, token=student_token)
    print(f"[Student Save Answer Q1] Status: {status}")

    # Question 2: TRUE_FALSE - Incorrect answer "False" (Correct is "True") -> tests negative marks
    q2_id = res_questions["data"][1]["questionId"]
    status, res = make_request(f"/api/student/exams/{exam_id}/save-answer", "POST", {
        "questionId": q2_id,
        "selectedAnswer": "False"
    }, token=student_token)
    print(f"[Student Save Answer Q2] Status: {status}")

    # Question 3: MULTIPLE_SELECT - Correct answer ["2", "3"]
    q3_id = res_questions["data"][2]["questionId"]
    status, res = make_request(f"/api/student/exams/{exam_id}/save-answer", "POST", {
        "questionId": q3_id,
        "selectedAnswer": ["2", "3"]
    }, token=student_token)
    print(f"[Student Save Answer Q3] Status: {status}")

    # 12. Student Submit Exam
    status, res = make_request(f"/api/student/exams/{exam_id}/submit", "POST", token=student_token)
    print(f"[Student Submit Exam] Status: {status}")
    if status != 200:
        print("FAIL: Student failed to submit exam.")
        return False

    # 13. Student View Results (Verify results not published yet block)
    status, res = make_request(f"/api/student/exams/{exam_id}/result", "GET", token=student_token)
    print(f"[Student View Result (Before Publish)] Status: {status}, Msg: {res.get('message')}")
    if res.get("success") is True or res.get("data") is not None:
        print("FAIL: Results should not be viewable before admin publishes them.")
        return False

    # 14. Teacher Login & Live Monitoring & Attempts
    status, res = make_request("/api/auth/login", "POST", {
        "userId": "teacher_test",
        "password": "Password@123"
    })
    print(f"[Teacher Login] Status: {status}")
    teacher_token = res["data"]["token"]

    # View assigned exams
    status, res = make_request("/api/teacher/exams", "GET", token=teacher_token)
    print(f"[Teacher View Exams] Status: {status}, Count: {len(res.get('data', []))}")

    # Live monitoring
    status, res = make_request(f"/api/teacher/exams/{exam_id}/live", "GET", token=teacher_token)
    print(f"[Teacher Live Monitoring] Status: {status}, Data: {res.get('data')}")
    if status != 200 or not res.get("data"):
        print("FAIL: Teacher live monitoring failed.")
        return False

    # Attempts
    status, res = make_request(f"/api/teacher/exams/{exam_id}/attempts", "GET", token=teacher_token)
    print(f"[Teacher View Attempts] Status: {status}, Count: {len(res.get('data', []))}")
    if status != 200:
        print("FAIL: Teacher view attempts failed.")
        return False

    # 15. Admin Publish Results
    status, res = make_request(f"/api/admin/exams/{exam_id}/publish-results", "POST", token=admin_token)
    print(f"[Admin Publish Results] Status: {status}")
    if status != 200:
        print("FAIL: Admin publish results failed.")
        return False

    # 16. Student View Results (After Publish)
    status, res = make_request(f"/api/student/exams/{exam_id}/result", "GET", token=student_token)
    print(f"[Student View Result (After Publish)] Status: {status}")
    if status != 200 or not res.get("data"):
        print("FAIL: Student failed to view result after publication.")
        return False
        
    result_data = res["data"]
    # Q1: Correct (+5)
    # Q2: Incorrect (-0 negative marks, so 0)
    # Q3: Correct (+10)
    # Total Score: 5 + 0 + 10 = 15. Total Marks: 20. Passing: 10. Pass: True.
    print(f"Result details: Score={result_data['score']}, Percent={result_data['percentage']}%, Grade={result_data['grade']}, Passed={result_data['passed']}")
    if result_data["score"] != 15 or result_data["passed"] is not True:
        print("FAIL: Evaluation engine scored incorrect values.")
        return False
    print("SUCCESS: Evaluation engine values verified correctly.")

    # 17. Close Exam
    # Make a new exam and start attempt
    exam_close_id = f"EXAM_CL_TEST_{int(time.time())}"
    valid_payload["examId"] = exam_close_id
    valid_payload["title"] = "Exam to Close Test"
    
    make_request("/api/admin/exams", "POST", valid_payload, token=admin_token)
    make_request(f"/api/admin/exams/{exam_close_id}/publish", "POST", token=admin_token)
    make_request(f"/api/student/exams/{exam_close_id}/start", "POST", token=student_token)
    
    # Save one answer
    make_request(f"/api/student/exams/{exam_close_id}/save-answer", "POST", {
        "questionId": "Q001",
        "selectedAnswer": "75"
    }, token=student_token)
    
    # Close exam
    status, res = make_request(f"/api/admin/exams/{exam_close_id}/close", "POST", token=admin_token)
    print(f"[Admin Close Exam] Status: {status}")
    if status != 200:
        print("FAIL: Closing exam failed.")
        return False
        
    # Check if student attempt is now SUBMITTED
    status, res = make_request(f"/api/teacher/exams/{exam_close_id}/attempts", "GET", token=teacher_token)
    attempts = res.get("data", [])
    if len(attempts) != 1 or attempts[0]["status"] != "SUBMITTED":
        print("FAIL: Closing exam did not automatically submit in-progress attempts.")
        return False
    print("SUCCESS: Auto-submission on close verified successfully.")

    # Clean up test accounts (optional, we leave them or let them be)
    print("=" * 70)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = run_tests()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Exception during verification: {str(e)}")
        sys.exit(1)

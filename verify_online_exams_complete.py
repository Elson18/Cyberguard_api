import os
import sys
import time
import json
import threading
from datetime import datetime, timezone, timedelta
import pymongo

# Import Flask app directly
from app import app
from database.mongodb import db_wrapper


class MockCursor:
    def __init__(self, docs):
        self.docs = docs
    def sort(self, key, direction=1):
        reverse = (direction == -1)
        self.docs.sort(key=lambda x: x.get(key, 0), reverse=reverse)
        return self
    def limit(self, n):
        if n > 0:
            return MockCursor(self.docs[:n])
        return self
    def __iter__(self):
        return iter(self.docs)
    def __len__(self):
        return len(self.docs)

def match_query(doc, query):
    if not query:
        return True
    for k, v in query.items():
        if k == "$or" and isinstance(v, list):
            if not any(match_query(doc, cond) for cond in v):
                return False
            continue
        val = doc.get(k)
        if isinstance(v, dict):
            if "$in" in v:
                if isinstance(val, list):
                    if not any(item in v["$in"] for item in val): return False
                else:
                    if val not in v["$in"]: return False
            if "$ne" in v:
                if val == v["$ne"]: return False
            if "$gt" in v:
                if not (val is not None and val > v["$gt"]): return False
            if "$gte" in v:
                if not (val is not None and val >= v["$gte"]): return False
            if "$lt" in v:
                if not (val is not None and val < v["$lt"]): return False
            if "$lte" in v:
                if not (val is not None and val <= v["$lte"]): return False
            if "$exists" in v:
                exists = k in doc
                if exists != v["$exists"]: return False
        elif val != v and str(val) != str(v):
            if isinstance(val, list) and v in val:
                continue
            return False
    return True

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.docs = []

    def create_index(self, *args, **kwargs):
        pass

    def insert_one(self, doc):
        d = dict(doc)
        if "_id" not in d:
            from bson import ObjectId
            d["_id"] = str(ObjectId())
        self.docs.append(d)
        class Res:
            inserted_id = d["_id"]
        return Res()

    def insert_many(self, docs):
        res = []
        for d in docs:
            r = self.insert_one(d)
            res.append(r.inserted_id)
        class ResMany:
            inserted_ids = res
        return ResMany()

    def find_one(self, query=None):
        query = query or {}
        for d in self.docs:
            if match_query(d, query):
                return dict(d)
        return None

    def find(self, query=None):
        query = query or {}
        matched = [dict(d) for d in self.docs if match_query(d, query)]
        return MockCursor(matched)

    def count_documents(self, query=None):
        query = query or {}
        return len([d for d in self.docs if match_query(d, query)])

    def distinct(self, field, query=None):
        query = query or {}
        vals = set()
        for d in self.docs:
            if match_query(d, query) and field in d:
                val = d[field]
                if isinstance(val, list):
                    for v in val: vals.add(v)
                else:
                    vals.add(val)
        return list(vals)

    def update_one(self, filter, update, upsert=False):
        fields_to_set = update.get("$set", {})
        add_to_set = update.get("$addToSet", {})
        for d in self.docs:
            if match_query(d, filter):
                d.update(fields_to_set)
                for k, v in add_to_set.items():
                    if k not in d or not isinstance(d[k], list):
                        d[k] = []
                    if v not in d[k]:
                        d[k].append(v)
                class Res:
                    matched_count = 1
                    modified_count = 1
                return Res()
        if upsert:
            new_doc = dict(filter)
            new_doc.update(fields_to_set)
            self.insert_one(new_doc)
            class ResUpsert:
                matched_count = 0
                modified_count = 1
            return ResUpsert()
        class ResNone:
            matched_count = 0
            modified_count = 0
        return ResNone()

    def update_many(self, filter, update):
        fields_to_set = update.get("$set", {})
        count = 0
        for d in self.docs:
            if match_query(d, filter):
                d.update(fields_to_set)
                count += 1
        class ResMany:
            modified_count = count
        return ResMany()

    def delete_one(self, filter):
        for i, d in enumerate(self.docs):
            if match_query(d, filter):
                self.docs.pop(i)
                class Res:
                    deleted_count = 1
                return Res()
        class Res0:
            deleted_count = 0
        return Res0()

    def delete_many(self, filter):
        to_keep = []
        deleted = 0
        for d in self.docs:
            if match_query(d, filter):
                deleted += 1
            else:
                to_keep.append(d)
        self.docs = to_keep
        class ResMany:
            deleted_count = deleted
        return ResMany()

class MockDatabase:
    def __init__(self):
        self.collections = {}

    def __getattr__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

    def __getitem__(self, name):
        return getattr(self, name)

# Check MongoDB connectivity; fallback to MockDatabase if offline
try:
    mongo_uri = app.config.get("MONGO_URI", "mongodb://localhost:27017/student_rank_card_db")
    test_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
    test_client.admin.command('ping')
    print("[DB INFO] Connected to active MongoDB service.")
except Exception as ping_err:
    print(f"[DB INFO] Local MongoDB daemon offline ({ping_err}). Initializing pure-Python in-memory Mongo mock...")
    mock_db = MockDatabase()
    db_wrapper.client = mock_db
    db_wrapper.db = mock_db
    app.db = mock_db
    from app import seed_database
    seed_database(app)




def run_tests():
    print("=" * 80)
    print("STARTING COMPREHENSIVE ONLINE EXAMINATION BACKEND VERIFICATION TESTS")
    print("=" * 80)

    client = app.test_client()
    db = db_wrapper.db

    passed_count = 0
    failed_count = 0

    def assert_true(condition, test_name, error_msg=""):
        nonlocal passed_count, failed_count
        if condition:
            print(f"[PASS] {test_name}")
            passed_count += 1
            return True
        else:
            print(f"[FAIL] {test_name} - {error_msg}")
            failed_count += 1
            return False

    # Helper function for authenticated requests
    def request(path, method="GET", body=None, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(body) if body is not None else None
        
        res = client.open(path, method=method, headers=headers, data=data)
        try:
            res_json = json.loads(res.data.decode("utf-8"))
        except Exception:
            res_json = {"raw": res.data.decode("utf-8")}
        return res.status_code, res_json

    # ---------------------------------------------------------
    # 1. AUTHENTICATION & TOKEN SETUP
    # ---------------------------------------------------------
    print("\n--- 1. Authentication & Authorization Setup ---")

    # Login Admin
    status, res = request("/api/auth/login", "POST", {"userId": "admin", "password": "Admin@123"})
    assert_true(status == 200 and res.get("success"), "Super Admin Login", res.get("message"))
    admin_token = res["data"]["token"]

    # Setup Class & Subject
    status, cls_res = request("/api/classes", "GET", token=admin_token)
    class_id = None
    for cls in cls_res.get("data", []):
        if cls.get("className") == "Class 10A":
            class_id = cls["_id"]
            break
    if not class_id:
        status, res = request("/api/admin/create-class", "POST", {"className": "Class 10A", "section": "A"}, token=admin_token)
        class_id = res.get("data", {}).get("_id")

    status, sub_res = request("/api/subjects", "GET", token=admin_token)
    sub_id = None
    for s in sub_res.get("data", []):
        if s.get("subjectName") == "Maths 10":
            sub_id = s["_id"]
            break
    if not sub_id:
        status, res = request("/api/admin/create-subject", "POST", {"subjectName": "Maths 10"}, token=admin_token)
        sub_id = res.get("data", {}).get("_id")

    # Create Teachers
    request("/api/admin/create-teacher", "POST", {
        "userId": "teacher_assigned", "password": "Password@123", "name": "Teacher Assigned", "department": "Maths", "teacherId": "teacher_assigned"
    }, token=admin_token)
    request("/api/admin/assign-teacher", "POST", {"teacherId": "teacher_assigned", "classId": class_id}, token=admin_token)

    request("/api/admin/create-teacher", "POST", {
        "userId": "teacher_unassigned", "password": "Password@123", "name": "Teacher Unassigned", "department": "Science", "teacherId": "teacher_unassigned"
    }, token=admin_token)

    # Create Students
    request("/api/admin/create-student", "POST", {
        "userId": "student_1", "password": "Password@123", "name": "Student One", "classId": class_id, "rollNumber": "101", "studentId": "student_1"
    }, token=admin_token)
    request("/api/admin/create-student", "POST", {
        "userId": "student_2", "password": "Password@123", "name": "Student Two", "classId": class_id, "rollNumber": "102", "studentId": "student_2"
    }, token=admin_token)

    # Login Teacher Assigned
    status, res = request("/api/auth/login", "POST", {"userId": "teacher_assigned", "password": "Password@123"})
    teacher_assigned_token = res["data"]["token"]

    # Login Teacher Unassigned
    status, res = request("/api/auth/login", "POST", {"userId": "teacher_unassigned", "password": "Password@123"})
    teacher_unassigned_token = res["data"]["token"]

    # Login Student 1 & 2
    status, res = request("/api/auth/login", "POST", {"userId": "student_1", "password": "Password@123"})
    student_1_token = res["data"]["token"]

    status, res = request("/api/auth/login", "POST", {"userId": "student_2", "password": "Password@123"})
    student_2_token = res["data"]["token"]

    # Verify Role Restrictions (RBAC)
    status, res = request("/api/admin/exams", "GET", token=student_1_token)
    assert_true(status == 403, "RBAC: Student forbidden from Super Admin API")

    status, res = request("/api/teacher/exams", "GET", token=student_1_token)
    assert_true(status == 403, "RBAC: Student forbidden from Teacher API")

    status, res = request("/api/admin/exams", "GET", token=teacher_assigned_token)
    assert_true(status == 403, "RBAC: Teacher forbidden from Super Admin API")

    status, res = request("/api/admin/exams", "GET", token="invalid_jwt_token_12345")
    assert_true(status == 401, "Auth: Invalid JWT returns 401 Unauthorized")

    status, res = request("/api/admin/exams", "GET")
    assert_true(status == 401, "Auth: Missing JWT returns 401 Unauthorized")

    # ---------------------------------------------------------
    # 2. SUPER ADMIN APIS (CREATE, GET, UPDATE, DELETE, PUBLISH, CLOSE, PUBLISH RESULTS)
    # ---------------------------------------------------------
    print("\n--- 2. Super Admin APIs Verification ---")

    ts = int(time.time())
    now_dt = datetime.now(timezone.utc)
    start_dt_str = (now_dt - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    end_dt_str = (now_dt + timedelta(hours=2)).isoformat().replace("+00:00", "Z")

    exam_id_1 = f"EXM_TEST_1_{ts}"
    create_payload = {
        "examId": exam_id_1,
        "title": f"Mathematics Unit Test {ts}",
        "subjectId": sub_id,
        "classIds": [class_id],
        "academicYear": "2026-2027",
        "duration": 60,
        "passingMarks": 10,
        "startDateTime": start_dt_str,
        "endDateTime": end_dt_str,
        "instructions": "Answer all objective questions.",
        "questions": [
            {
                "questionId": "Q001",
                "question": "What is 15 x 5?",
                "type": "MCQ",
                "options": ["55", "65", "75", "85"],
                "correctAnswer": "75",
                "marks": 5,
                "negativeMarks": 1,
                "explanation": "15 times 5 is 75."
            },
            {
                "questionId": "Q002",
                "question": "Is 17 a prime number?",
                "type": "TRUE_FALSE",
                "options": ["True", "False"],
                "correctAnswer": "True",
                "marks": 5,
                "negativeMarks": 1,
                "explanation": "17 is a prime number."
            },
            {
                "questionId": "Q003",
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

    # Test Validation: startDateTime >= endDateTime
    bad_dates_payload = create_payload.copy()
    bad_dates_payload["examId"] = f"EXM_BAD_{ts}"
    bad_dates_payload["startDateTime"] = end_dt_str
    bad_dates_payload["endDateTime"] = start_dt_str
    status, res = request("/api/admin/exams", "POST", bad_dates_payload, token=admin_token)
    assert_true(status == 400, "Validation: Reject startDateTime >= endDateTime")

    # Test Validation: MCQ with < 2 options
    bad_mcq_payload = create_payload.copy()
    bad_mcq_payload["examId"] = f"EXM_BAD_MCQ_{ts}"
    bad_mcq_payload["questions"] = [{
        "question": "What is 2+2?", "type": "MCQ", "options": ["4"], "correctAnswer": "4", "marks": 5
    }]
    status, res = request("/api/admin/exams", "POST", bad_mcq_payload, token=admin_token)
    assert_true(status == 400, "Validation: Reject MCQ with less than 2 options")

    # Create Valid Exam 1
    status, res = request("/api/admin/exams", "POST", create_payload, token=admin_token)
    assert_true(status == 201 and res.get("success"), "Super Admin: Create Exam")
    created_exam = res.get("data", {})
    assert_true(created_exam.get("totalMarks") == 20, "Super Admin: Total marks calculated (5+5+10=20)")
    assert_true(created_exam.get("status") == "DRAFT", "Super Admin: Initial exam status is DRAFT")

    # Verify questions in database
    q_docs = list(db.exam_questions.find({"examId": exam_id_1}))
    assert_true(len(q_docs) == 3, "Database: Questions saved in exam_questions collection")

    # Get Exams with filters
    status, res = request(f"/api/admin/exams?classId={class_id}&subjectId={sub_id}&status=DRAFT", "GET", token=admin_token)
    assert_true(status == 200 and len(res.get("data", [])) >= 1, "Super Admin: Get Exams with filters")

    # Update Exam in DRAFT status (including updating questions)
    update_payload = {
        "instructions": "Updated instructions for testing.",
        "questions": [
            {
                "questionId": "Q001",
                "question": "What is 15 x 5?",
                "type": "MCQ",
                "options": ["55", "65", "75", "85"],
                "correctAnswer": "75",
                "marks": 10,
                "negativeMarks": 1
            },
            {
                "questionId": "Q002",
                "question": "Is 17 a prime number?",
                "type": "TRUE_FALSE",
                "options": ["True", "False"],
                "correctAnswer": "True",
                "marks": 10,
                "negativeMarks": 1
            }
        ]
    }
    status, res = request(f"/api/admin/exams/{exam_id_1}", "PUT", update_payload, token=admin_token)
    assert_true(status == 200 and res.get("success"), "Super Admin: Update DRAFT exam with questions")
    assert_true(res.get("data", {}).get("totalMarks") == 20, "Super Admin: Updated totalMarks (10+10=20)")

    # Create temporary exam for Delete test
    temp_exam_id = f"EXM_TEMP_{ts}"
    temp_payload = create_payload.copy()
    temp_payload["examId"] = temp_exam_id
    temp_payload["title"] = f"Temp Exam {ts}"
    request("/api/admin/exams", "POST", temp_payload, token=admin_token)

    status, res = request(f"/api/admin/exams/{temp_exam_id}", "DELETE", token=admin_token)
    assert_true(status == 200 and res.get("success"), "Super Admin: Delete DRAFT exam with zero attempts")

    # Publish Exam 1
    status, res = request(f"/api/admin/exams/{exam_id_1}/publish", "POST", token=admin_token)
    assert_true(status == 200 and res.get("success"), "Super Admin: Publish Exam")

    # Try updating published exam (should fail)
    status, res = request(f"/api/admin/exams/{exam_id_1}", "PUT", {"instructions": "Fail edit"}, token=admin_token)
    assert_true(status == 400, "Super Admin: Reject updating PUBLISHED exam")

    # Try deleting published exam (should fail)
    status, res = request(f"/api/admin/exams/{exam_id_1}", "DELETE", token=admin_token)
    assert_true(status == 400, "Super Admin: Reject deleting PUBLISHED exam")

    # ---------------------------------------------------------
    # 3. TEACHER APIS & STUDENT WORKFLOW
    # ---------------------------------------------------------
    print("\n--- 3. Teacher & Student APIs Verification ---")

    # Teacher Assigned Exams
    status, res = request("/api/teacher/exams", "GET", token=teacher_assigned_token)
    assert_true(status == 200 and any(e["examId"] == exam_id_1 for e in res.get("data", [])), "Teacher: View Assigned Exams")

    status, res = request("/api/teacher/exams", "GET", token=teacher_unassigned_token)
    assert_true(status == 200 and len(res.get("data", [])) == 0, "Teacher: Unassigned teacher sees 0 exams")

    # Student 1: Get My Exams
    status, res = request("/api/student/exams", "GET", token=student_1_token)
    assert_true(status == 200, "Student 1: My Exams")
    st_exams = res.get("data", [])
    matching_st_exam = next((e for e in st_exams if e["examId"] == exam_id_1), None)
    assert_true(matching_st_exam is not None and matching_st_exam.get("status") == "Active", "Student 1: Exam status is Active")

    # Student 1: Start Exam
    status, res = request(f"/api/student/exams/{exam_id_1}/start", "POST", token=student_1_token)
    assert_true(status == 201 and res.get("success"), "Student 1: Start Exam")
    attempt_1 = res.get("data", {})
    attempt_id_1 = attempt_1.get("attemptId")

    # Resume exam attempt (should return existing in progress attempt)
    status, res = request(f"/api/student/exams/{exam_id_1}/start", "POST", token=student_1_token)
    assert_true(status == 200 and res.get("data", {}).get("attemptId") == attempt_id_1, "Student 1: Resume active attempt")

    # Student 1: Get Questions (sensitive fields stripped)
    status, res = request(f"/api/student/exams/{exam_id_1}", "GET", token=student_1_token)
    assert_true(status == 200, "Student 1: Get Questions")
    questions_list = res.get("data", [])
    assert_true(len(questions_list) == 2, "Student 1: Returns 2 questions")
    first_q = questions_list[0]
    assert_true("correctAnswer" not in first_q and "explanation" not in first_q and "marks" not in first_q, "Student 1: Sensitive fields stripped before submission")

    # Student 1: Save Answer Q001
    status, res = request(f"/api/student/exams/{exam_id_1}/save-answer", "POST", {
        "questionId": "Q001", "selectedAnswer": "75"
    }, token=student_1_token)
    assert_true(status == 200 and res.get("success"), "Student 1: Save Answer Q001 (Correct)")

    # Save Answer Q002 (Replace answer test: first set wrong, then update to correct)
    request(f"/api/student/exams/{exam_id_1}/save-answer", "POST", {"questionId": "Q002", "selectedAnswer": "False"}, token=student_1_token)
    status, res = request(f"/api/student/exams/{exam_id_1}/save-answer", "POST", {"questionId": "Q002", "selectedAnswer": "True"}, token=student_1_token)
    assert_true(status == 200 and res.get("success"), "Student 1: Replace Answer Q002 with True (Correct)")

    # Teacher Live Monitoring (during student attempt)
    status, res = request(f"/api/teacher/exams/{exam_id_1}/live", "GET", token=teacher_assigned_token)
    assert_true(status == 200, "Teacher: Live Monitoring")
    live_data = res.get("data", {})
    assert_true(live_data.get("studentsStarted") == 1 and live_data.get("activeCount") == 1, "Teacher: Live counts match DB (Started 1, Active 1)")

    # Student 1: Submit Exam
    status, res = request(f"/api/student/exams/{exam_id_1}/submit", "POST", token=student_1_token)
    assert_true(status == 200 and res.get("success"), "Student 1: Submit Exam")

    # Duplicate Submission check
    status, res = request(f"/api/student/exams/{exam_id_1}/submit", "POST", token=student_1_token)
    assert_true(status == 400, "Student 1: Reject duplicate submission")

    # Duplicate Start attempt check
    status, res = request(f"/api/student/exams/{exam_id_1}/start", "POST", token=student_1_token)
    assert_true(status == 400, "Student 1: Reject starting already submitted exam")

    # Teacher Live Monitoring (after submission)
    status, res = request(f"/api/teacher/exams/{exam_id_1}/live", "GET", token=teacher_assigned_token)
    live_data = res.get("data", {})
    assert_true(live_data.get("studentsSubmitted") == 1 and live_data.get("activeCount") == 0, "Teacher: Live counts match DB (Submitted 1, Active 0)")

    # Teacher Student Attempts
    status, res = request(f"/api/teacher/exams/{exam_id_1}/attempts", "GET", token=teacher_assigned_token)
    assert_true(status == 200 and len(res.get("data", [])) >= 1, "Teacher: View Student Attempts")
    att_info = res.get("data", [])[0]
    assert_true(att_info.get("status") == "SUBMITTED" and att_info.get("student", {}).get("name") == "Student One", "Teacher: Attempt info contains student details")

    # View Result Before Publishing (Should return null data with message)
    status, res = request(f"/api/student/exams/{exam_id_1}/result", "GET", token=student_1_token)
    assert_true(status == 200 and res.get("data") is None and "not been published" in res.get("message", ""), "Student 1: View Result before publication returns null data")

    # Teacher Publish Results
    status, res = request(f"/api/teacher/exams/{exam_id_1}/publish-results", "POST", token=teacher_assigned_token)
    assert_true(status == 200 and res.get("success"), "Teacher: Publish Results")

    # Unassigned Teacher Publish Results (Should return 403)
    status, res = request(f"/api/teacher/exams/{exam_id_1}/publish-results", "POST", token=teacher_unassigned_token)
    assert_true(status == 403, "Teacher: Unassigned teacher publish results returns 403")

    # View Result After Publishing
    status, res = request(f"/api/student/exams/{exam_id_1}/result", "GET", token=student_1_token)
    assert_true(status == 200 and res.get("data") is not None, "Student 1: View Result after publication")
    res_data = res.get("data", {})
    assert_true(res_data.get("score") == 20 and res_data.get("percentage") == 100.0 and res_data.get("grade") == "A+" and res_data.get("passed") is True, "Auto Evaluation: Perfect Score 20/20, 100%, Grade A+, Passed")

    # Check Student My Exams status after submission
    status, res = request("/api/student/exams", "GET", token=student_1_token)
    st_exams = res.get("data", [])
    matching_st_exam = next((e for e in st_exams if e["examId"] == exam_id_1), None)
    assert_true(matching_st_exam is not None and matching_st_exam.get("status") == "Completed", "Student 1: My Exams status is Completed after submission")

    # ---------------------------------------------------------
    # 4. EDGE CASE & ERROR HANDLING VERIFICATION
    # ---------------------------------------------------------
    print("\n--- 4. Edge Cases & Error Handling Verification ---")

    # Future Exam (Upcoming)
    future_exam_id = f"EXM_FUTURE_{ts}"
    future_start = (now_dt + timedelta(hours=10)).isoformat().replace("+00:00", "Z")
    future_end = (now_dt + timedelta(hours=12)).isoformat().replace("+00:00", "Z")
    future_payload = create_payload.copy()
    future_payload["examId"] = future_exam_id
    future_payload["title"] = f"Future Exam {ts}"
    future_payload["startDateTime"] = future_start
    future_payload["endDateTime"] = future_end
    request("/api/admin/exams", "POST", future_payload, token=admin_token)
    request(f"/api/admin/exams/{future_exam_id}/publish", "POST", token=admin_token)

    # Student tries to start future exam (should fail 400)
    status, res = request(f"/api/student/exams/{future_exam_id}/start", "POST", token=student_1_token)
    assert_true(status == 400, "Edge Case: Cannot start exam before startDateTime")

    # Past Exam (Missed / Closed)
    past_exam_id = f"EXM_PAST_{ts}"
    past_start = (now_dt - timedelta(hours=12)).isoformat().replace("+00:00", "Z")
    past_end = (now_dt - timedelta(hours=10)).isoformat().replace("+00:00", "Z")
    past_payload = create_payload.copy()
    past_payload["examId"] = past_exam_id
    past_payload["title"] = f"Past Exam {ts}"
    past_payload["startDateTime"] = past_start
    past_payload["endDateTime"] = past_end
    request("/api/admin/exams", "POST", past_payload, token=admin_token)
    request(f"/api/admin/exams/{past_exam_id}/publish", "POST", token=admin_token)

    # Student My Exams status for past exam (should show Missed)
    status, res = request("/api/student/exams", "GET", token=student_2_token)
    st_exams = res.get("data", [])
    past_st_exam = next((e for e in st_exams if e["examId"] == past_exam_id), None)
    assert_true(past_st_exam is not None and past_st_exam.get("status") == "Missed", "Student 2: Past unattempted exam status is Missed")

    # Student tries to start past exam (should fail 400)
    status, res = request(f"/api/student/exams/{past_exam_id}/start", "POST", token=student_2_token)
    assert_true(status == 400, "Edge Case: Cannot start exam after endDateTime")

    # Super Admin Close Exam with active attempt auto-submit
    auto_close_exam_id = f"EXM_AUTOCLOSE_{ts}"
    auto_close_payload = create_payload.copy()
    auto_close_payload["examId"] = auto_close_exam_id
    auto_close_payload["title"] = f"Auto Close Exam {ts}"
    request("/api/admin/exams", "POST", auto_close_payload, token=admin_token)
    request(f"/api/admin/exams/{auto_close_exam_id}/publish", "POST", token=admin_token)

    # Student 2 starts auto close exam
    request(f"/api/student/exams/{auto_close_exam_id}/start", "POST", token=student_2_token)

    # Admin closes exam
    status, res = request(f"/api/admin/exams/{auto_close_exam_id}/close", "POST", token=admin_token)
    assert_true(status == 200 and res.get("success"), "Super Admin: Close Exam auto-submits active attempts")

    # Check Student 2 attempt is now SUBMITTED
    att_2 = db.exam_attempts.find_one({"examId": auto_close_exam_id, "studentId": "student_2"})
    assert_true(att_2 is not None and att_2.get("status") == "SUBMITTED", "Database: Active attempt auto-submitted on exam close")

    # Non-existent Exam ID 404
    status, res = request("/api/admin/exams/EXM_NONEXISTENT_999", "GET", token=admin_token)
    assert_true(status == 200 and len(res.get("data", [])) == 0, "404/Empty filter handling for missing exam")

    # ---------------------------------------------------------
    # 5. PERFORMANCE & CONCURRENCY TESTING
    # ---------------------------------------------------------
    print("\n--- 5. Performance & Concurrency Testing ---")

    # Large Exam Creation (100 Questions)
    large_exam_id = f"EXM_LARGE_{ts}"
    large_questions = []
    for i in range(1, 101):
        large_questions.append({
            "questionId": f"Q{i:03d}",
            "question": f"Question number {i} text?",
            "type": "MCQ",
            "options": ["A", "B", "C", "D"],
            "correctAnswer": "A",
            "marks": 1
        })
    large_payload = {
        "examId": large_exam_id,
        "title": f"Large Performance Exam {ts}",
        "subjectId": sub_id,
        "classIds": [class_id],
        "academicYear": "2026-2027",
        "duration": 120,
        "passingMarks": 40,
        "startDateTime": start_dt_str,
        "endDateTime": end_dt_str,
        "questions": large_questions
    }

    t0 = time.time()
    status, res = request("/api/admin/exams", "POST", large_payload, token=admin_token)
    t1 = time.time()
    assert_true(status == 201 and res.get("data", {}).get("totalMarks") == 100, f"Performance: 100 questions exam created in {(t1-t0):.3f}s")

    request(f"/api/admin/exams/{large_exam_id}/publish", "POST", token=admin_token)

    # Concurrency test: Save answer concurrently
    request(f"/api/student/exams/{large_exam_id}/start", "POST", token=student_2_token)

    threads = []
    concurrency_errors = []

    def worker_save_answer(q_idx):
        try:
            st, r = request(f"/api/student/exams/{large_exam_id}/save-answer", "POST", {
                "questionId": f"Q{q_idx:03d}", "selectedAnswer": "A"
            }, token=student_2_token)
            if st != 200 or not r.get("success"):
                concurrency_errors.append(f"Save Q{q_idx} failed: {st}")
        except Exception as ex:
            concurrency_errors.append(str(ex))

    for i in range(1, 21):
        t = threading.Thread(target=worker_save_answer, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert_true(len(concurrency_errors) == 0, "Concurrency: 20 parallel answer saves executed cleanly")

    # ---------------------------------------------------------
    # 6. MONGODB COLLECTION INTEGRITY VERIFICATION
    # ---------------------------------------------------------
    print("\n--- 6. MongoDB Integrity Checks ---")

    exams_count = db.exams.count_documents({"isOnline": True})
    questions_count = db.exam_questions.count_documents({})
    attempts_count = db.exam_attempts.count_documents({})
    answers_count = db.student_answers.count_documents({})
    results_count = db.exam_results.count_documents({})

    print(f"Database Record Totals -> Exams: {exams_count}, Questions: {questions_count}, Attempts: {attempts_count}, Answers: {answers_count}, Results: {results_count}")

    # Check for orphaned questions
    existing_exam_ids = set(db.exams.distinct("examId", {"isOnline": True}))
    question_exam_ids = set(db.exam_questions.distinct("examId"))
    orphaned_questions = question_exam_ids - existing_exam_ids
    assert_true(len(orphaned_questions) == 0, "MongoDB Integrity: No orphaned questions found")

    # Check for orphaned attempts
    attempt_exam_ids = set(db.exam_attempts.distinct("examId"))
    orphaned_attempts = attempt_exam_ids - existing_exam_ids
    assert_true(len(orphaned_attempts) == 0, "MongoDB Integrity: No orphaned attempts found")

    # ---------------------------------------------------------
    # 7. FINAL ACCEPTANCE TEST SUMMARY
    # ---------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"VERIFICATION SUMMARY: PASSED={passed_count}, FAILED={failed_count}")
    print("=" * 80)

    return failed_count == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

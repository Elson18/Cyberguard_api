import time
import uuid
from datetime import datetime, timezone
from bson import ObjectId
from repositories.online_exam_repository import OnlineExamRepository
from utils.response import success_response, error_response
from utils.helpers import serialize_doc

def parse_iso_datetime(v: str) -> datetime:
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def compare_answers(selected, correct, question_type):
    if selected is None or correct is None or selected == "" or selected == []:
        return False
        
    if question_type == "MULTIPLE_SELECT":
        sel_list = []
        if isinstance(selected, list):
            sel_list = [str(x).strip() for x in selected if str(x).strip()]
        elif isinstance(selected, str):
            sel_list = [x.strip() for x in selected.split(",") if x.strip()]
            
        corr_list = []
        if isinstance(correct, list):
            corr_list = [str(x).strip() for x in correct if str(x).strip()]
        elif isinstance(correct, str):
            corr_list = [x.strip() for x in correct.split(",") if x.strip()]
            
        return sorted(sel_list) == sorted(corr_list)
        
    elif question_type == "TRUE_FALSE":
        sel_str = str(selected).strip().lower()
        corr_str = str(correct).strip().lower()
        return sel_str == corr_str
        
    else:
        sel_str = str(selected).strip().lower()
        corr_str = str(correct).strip().lower()
        return sel_str == corr_str

class OnlineExamService:
    @staticmethod
    def create_exam(admin_user_id, data):
        # Validate subjectId exists
        subject = OnlineExamRepository.get_subject_by_id(data["subjectId"])
        if not subject:
            return error_response("Subject ID not found.", 404)

        # Validate classIds exist
        for cid in data["classIds"]:
            cls_doc = OnlineExamRepository.get_class_by_id(cid)
            if not cls_doc:
                return error_response(f"Class ID '{cid}' not found.", 404)

        # Validate duplicate title for same class, subject, and academic year
        dup_exams = OnlineExamRepository.find_exams({
            "title": data["title"],
            "subjectId": data["subjectId"],
            "academicYear": data["academicYear"]
        })
        for de in dup_exams:
            overlap = set(de.get("classIds", [])).intersection(set(data["classIds"]))
            if overlap:
                return error_response("An exam with this title already exists for one of the specified classes, subject, and academic year.", 400)

        # Generate unique examId if not provided
        exam_id = data.get("examId")
        if not exam_id:
            exam_id = f"EXM{int(time.time())}"
        
        # Verify examId unique
        if OnlineExamRepository.get_exam_by_id(exam_id):
            return error_response(f"Exam ID '{exam_id}' already exists.", 400)

        now = datetime.now(timezone.utc)
        questions_input = data.pop("questions", [])

        exam_doc = {
            "examId": exam_id,
            "title": data["title"],
            "subjectId": data["subjectId"],
            "classIds": data["classIds"],
            "academicYear": data["academicYear"],
            "duration": data["duration"],
            "totalMarks": data["totalMarks"],
            "passingMarks": data["passingMarks"],
            "startDateTime": data["startDateTime"],
            "endDateTime": data["endDateTime"],
            "instructions": data.get("instructions", ""),
            "status": "DRAFT",
            "createdBy": admin_user_id,
            "createdAt": now,
            "updatedAt": now
        }

        # Build question docs
        question_docs = []
        for i, q in enumerate(questions_input):
            q_id = q.get("questionId") or f"Q{i+1:03d}"
            question_docs.append({
                "questionId": q_id,
                "examId": exam_id,
                "question": q["question"],
                "type": q["type"],
                "options": q.get("options"),
                "correctAnswer": q["correctAnswer"],
                "marks": q["marks"],
                "negativeMarks": q.get("negativeMarks", 0),
                "explanation": q.get("explanation", ""),
                "order": q.get("order") or (i + 1)
            })

        try:
            # Create exam
            OnlineExamRepository.create_exam(exam_doc)
            # Create questions
            OnlineExamRepository.bulk_create_questions(question_docs)
        except Exception as e:
            # Cleanup if fail
            OnlineExamRepository.delete_exam(exam_id)
            return error_response(f"Database error during creation: {str(e)}", 500)

        exam_doc["questions"] = question_docs
        return success_response(message="Online exam created successfully.", data=serialize_doc(exam_doc), status_code=201)

    @staticmethod
    def update_exam(admin_user_id, exam_id, data):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        if exam.get("status") != "DRAFT":
            return error_response("Exam details can only be modified while in DRAFT status.", 400)

        # Validate subjectId if changing
        if "subjectId" in data:
            subject = OnlineExamRepository.get_subject_by_id(data["subjectId"])
            if not subject:
                return error_response("Subject ID not found.", 404)

        # Validate classIds if changing
        if "classIds" in data:
            for cid in data["classIds"]:
                cls_doc = OnlineExamRepository.get_class_by_id(cid)
                if not cls_doc:
                    return error_response(f"Class ID '{cid}' not found.", 404)

        # Check duplicate title if title, subjectId, academicYear, or classIds changing
        title = data.get("title", exam["title"])
        sub_id = data.get("subjectId", exam["subjectId"])
        acad_yr = data.get("academicYear", exam["academicYear"])
        cls_ids = data.get("classIds", exam["classIds"])

        dup_exams = OnlineExamRepository.find_exams({
            "title": title,
            "subjectId": sub_id,
            "academicYear": acad_yr,
            "examId": {"$ne": exam_id}
        })
        for de in dup_exams:
            overlap = set(de.get("classIds", [])).intersection(set(cls_ids))
            if overlap:
                return error_response("An exam with this title already exists for one of the specified classes, subject, and academic year.", 400)

        now = datetime.now(timezone.utc)
        allowed_keys = ["title", "subjectId", "classIds", "academicYear", "duration", "passingMarks", "startDateTime", "endDateTime", "instructions", "totalMarks"]
        fields_to_set = {k: v for k, v in data.items() if k in allowed_keys and v is not None}
        fields_to_set["updatedAt"] = now

        # Update questions if provided
        if "questions" in data and data["questions"] is not None:
            questions_input = data["questions"]
            question_docs = []
            for i, q in enumerate(questions_input):
                q_id = q.get("questionId") or f"Q{i+1:03d}"
                question_docs.append({
                    "questionId": q_id,
                    "examId": exam_id,
                    "question": q["question"],
                    "type": q["type"],
                    "options": q.get("options"),
                    "correctAnswer": q["correctAnswer"],
                    "marks": q["marks"],
                    "negativeMarks": q.get("negativeMarks", 0),
                    "explanation": q.get("explanation", ""),
                    "order": q.get("order") or (i + 1)
                })
            fields_to_set["totalMarks"] = sum(q["marks"] for q in question_docs)
            OnlineExamRepository.delete_questions_by_exam_id(exam_id)
            OnlineExamRepository.bulk_create_questions(question_docs)

        updated = OnlineExamRepository.update_exam(exam_id, fields_to_set)
        return success_response(message="Exam updated successfully.", data=serialize_doc(updated))

    @staticmethod
    def delete_exam(admin_user_id, exam_id):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        if exam.get("status") != "DRAFT":
            return error_response("Only DRAFT exams with no attempts can be deleted.", 400)

        # Check if any student started
        attempts_count = len(OnlineExamRepository.get_attempts_by_exam_id(exam_id))
        if attempts_count > 0:
            return error_response("Cannot delete exam because one or more students have already started or attempted it.", 400)

        OnlineExamRepository.delete_exam(exam_id)
        return success_response(message="Exam deleted successfully.")


    @staticmethod
    def publish_exam(admin_user_id, exam_id):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        if exam.get("status") == "PUBLISHED":
            return success_response(message="Exam is already published.")

        # Update status
        now = datetime.now(timezone.utc)
        OnlineExamRepository.update_exam(exam_id, {"status": "PUBLISHED", "updatedAt": now})

        # Notify students of the assigned classes
        students = OnlineExamRepository.get_students_by_classIds(exam["classIds"])
        for student in students:
            # Publish notification
            OnlineExamRepository.create_notification({
                "userId": student["userId"],
                "title": "New Exam Published",
                "message": f"A new online exam '{exam['title']}' has been published.",
                "type": "EXAM_PUBLISHED",
                "isRead": False,
                "createdAt": now
            })
            # Reminder notification
            OnlineExamRepository.create_notification({
                "userId": student["userId"],
                "title": "Exam Reminder",
                "message": f"Online exam '{exam['title']}' starts at {exam['startDateTime']}.",
                "type": "EXAM_REMINDER",
                "isRead": False,
                "createdAt": now
            })

        return success_response(message="Exam published successfully and notifications dispatched.")

    @staticmethod
    def close_exam(admin_user_id, exam_id):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        now = datetime.now(timezone.utc)
        OnlineExamRepository.update_exam(exam_id, {"status": "CLOSED", "updatedAt": now})

        # End all IN_PROGRESS attempts
        attempts = OnlineExamRepository.get_attempts_by_exam_id(exam_id)
        active_attempts = [a for a in attempts if a.get("status") == "IN_PROGRESS"]

        for attempt in active_attempts:
            # Evaluate and submit the active attempt automatically
            student_id = attempt["studentId"]
            
            # Fetch all questions
            questions = OnlineExamRepository.get_questions_by_exam_id(exam_id)
            # Fetch student answers
            student_answers = {sa["questionId"]: sa for sa in OnlineExamRepository.get_answers_by_attempt(attempt["attemptId"])}

            correct_count = 0
            wrong_count = 0
            score = 0

            for q in questions:
                q_id = q["questionId"]
                ans_doc = student_answers.get(q_id)
                selected_ans = ans_doc.get("selectedAnswer") if ans_doc else None

                if selected_ans is not None and selected_ans != "" and selected_ans != []:
                    is_correct = compare_answers(selected_ans, q["correctAnswer"], q["type"])
                    if is_correct:
                        correct_count += 1
                        marks_awarded = q["marks"]
                    else:
                        wrong_count += 1
                        marks_awarded = -q.get("negativeMarks", 0)
                else:
                    is_correct = False
                    wrong_count += 1
                    marks_awarded = 0


                score += marks_awarded

                # Update individual answer
                OnlineExamRepository.save_student_answer({
                    "attemptId": attempt["attemptId"],
                    "studentId": student_id,
                    "questionId": q_id,
                    "selectedAnswer": selected_ans,
                    "isCorrect": is_correct,
                    "marksAwarded": marks_awarded
                })

            # Calculate metrics
            score = max(0, score) # Capped at 0
            total_marks = exam["totalMarks"]
            percentage = (score / total_marks) * 100 if total_marks > 0 else 0
            passed = score >= exam["passingMarks"]

            # Determine grade
            if percentage >= 90.0:
                grade = "A+"
            elif percentage >= 80.0:
                grade = "A"
            elif percentage >= 70.0:
                grade = "B"
            elif percentage >= 60.0:
                grade = "C"
            elif percentage >= 50.0:
                grade = "D"
            elif percentage >= 40.0:
                grade = "E"
            else:
                grade = "F"

            # Create/save final result
            OnlineExamRepository.save_result({
                "examId": exam_id,
                "studentId": student_id,
                "totalQuestions": len(questions),
                "correctAnswers": correct_count,
                "wrongAnswers": wrong_count,
                "score": score,
                "percentage": round(percentage, 2),
                "grade": grade,
                "passed": passed,
                "published": False,
                "submittedAt": now
            })

            # Mark attempt as SUBMITTED/CLOSED
            started_at = attempt.get("startedAt")
            if started_at:
                if isinstance(started_at, str):
                    started_at = parse_iso_datetime(started_at)
                elif started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                time_taken = int((now - started_at).total_seconds())
            else:
                time_taken = 0
            OnlineExamRepository.update_attempt(attempt["attemptId"], {
                "status": "SUBMITTED",
                "submittedAt": now,
                "timeTaken": time_taken
            })

        return success_response(message="Exam closed successfully and active attempts auto-submitted.")

    @staticmethod
    def publish_results(admin_user_id, exam_id):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        now = datetime.now(timezone.utc)
        OnlineExamRepository.publish_results(exam_id)

        # Notify students who attempted the exam
        attempts = OnlineExamRepository.get_attempts_by_exam_id(exam_id)
        for attempt in attempts:
            student = OnlineExamRepository.get_student_by_studentId(attempt["studentId"])
            if student:
                OnlineExamRepository.create_notification({
                    "userId": student["userId"],
                    "title": "Exam Results Published",
                    "message": f"Results for the online exam '{exam['title']}' have been published.",
                    "type": "EXAM_RESULTS_PUBLISHED",
                    "isRead": False,
                    "createdAt": now
                })

        return success_response(message="Exam results published successfully and notifications dispatched.")

    @staticmethod
    def get_exams_admin(filters):
        query = {}
        if filters.get("classId"):
            query["classIds"] = filters["classId"]
        if filters.get("subjectId"):
            query["subjectId"] = filters["subjectId"]
        if filters.get("academicYear"):
            query["academicYear"] = filters["academicYear"]
        if filters.get("status"):
            query["status"] = filters["status"]

        exams = OnlineExamRepository.find_exams(query)
        return success_response(data=serialize_doc(exams))

    @staticmethod
    def get_exam_by_id_admin(exam_id):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return success_response(data=[])
        questions = OnlineExamRepository.get_questions_by_exam_id(exam_id)
        exam_doc = serialize_doc(exam)
        exam_doc["questions"] = serialize_doc(questions)
        return success_response(data=exam_doc)

    @staticmethod
    def get_exams_teacher(teacher_user_id):
        teacher = OnlineExamRepository.get_teacher_by_userId(teacher_user_id)
        if not teacher:
            return error_response("Teacher profile not found.", 404)

        assigned_classes = teacher.get("assignedClasses", [])
        if not assigned_classes:
            return success_response(data=[])

        exams = OnlineExamRepository.find_exams({
            "classIds": {"$in": assigned_classes}
        })
        return success_response(data=serialize_doc(exams))

    @staticmethod
    def get_live_monitoring(teacher_user_id, exam_id):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        teacher = OnlineExamRepository.get_teacher_by_userId(teacher_user_id)
        if not teacher:
            return error_response("Teacher profile not found.", 404)

        # Validate access
        overlap = set(exam["classIds"]).intersection(set(teacher.get("assignedClasses", [])))
        if not overlap:
            return error_response("Access denied. You do not teach any class assigned to this exam.", 403)

        # Total students in classes
        students = OnlineExamRepository.get_students_by_classIds(exam["classIds"])
        total_student_ids = {s["studentId"] for s in students}

        attempts = OnlineExamRepository.get_attempts_by_exam_id(exam_id)
        started_student_ids = {a["studentId"] for a in attempts}
        submitted_student_ids = {a["studentId"] for a in attempts if a.get("status") == "SUBMITTED"}

        students_started = len(started_student_ids)
        students_submitted = len(submitted_student_ids)
        students_pending = len(total_student_ids - started_student_ids)
        active_count = len(started_student_ids - submitted_student_ids)

        return success_response(data={
            "studentsStarted": students_started,
            "studentsSubmitted": students_submitted,
            "studentsPending": students_pending,
            "activeCount": active_count
        })

    @staticmethod
    def get_attempts(teacher_user_id, exam_id):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        teacher = OnlineExamRepository.get_teacher_by_userId(teacher_user_id)
        if not teacher:
            return error_response("Teacher profile not found.", 404)

        overlap = set(exam["classIds"]).intersection(set(teacher.get("assignedClasses", [])))
        if not overlap:
            return error_response("Access denied. You do not teach any class assigned to this exam.", 403)

        attempts = OnlineExamRepository.get_attempts_by_exam_id(exam_id)
        attempts_list = []
        for att in attempts:
            student = OnlineExamRepository.get_student_by_studentId(att["studentId"])
            student_info = {
                "studentId": att["studentId"],
                "name": student.get("name") if student else "N/A",
                "rollNumber": student.get("rollNumber") if student else "N/A",
                "classId": student.get("classId") if student else "N/A"
            }
            att_doc = serialize_doc(att)
            att_doc["student"] = student_info
            attempts_list.append(att_doc)

        return success_response(data=attempts_list)

    @staticmethod
    def publish_results_teacher(teacher_user_id, exam_id):
        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        teacher = OnlineExamRepository.get_teacher_by_userId(teacher_user_id)
        if not teacher:
            return error_response("Teacher profile not found.", 404)

        overlap = set(exam["classIds"]).intersection(set(teacher.get("assignedClasses", [])))
        if not overlap:
            return error_response("Access denied. You do not teach any class assigned to this exam.", 403)

        return OnlineExamService.publish_results(teacher_user_id, exam_id)

    @staticmethod
    def get_exams_student(student_user_id, filters):
        student = OnlineExamRepository.get_student_by_userId(student_user_id)
        if not student:
            return error_response("Student profile not found.", 404)

        class_id = student["classId"]
        query = {
            "status": "PUBLISHED",
            "classIds": class_id
        }

        # Apply active academic year query parameter filter
        academic_year = filters.get("academicYear")
        if academic_year:
            query["academicYear"] = academic_year

        raw_exams = OnlineExamRepository.find_exams(query)
        now = datetime.now(timezone.utc)

        result_exams = []
        for exam in raw_exams:
            exam_doc = serialize_doc(exam)
            attempt = OnlineExamRepository.get_attempt_by_student_and_exam(student["studentId"], exam["examId"])
            
            if attempt and attempt.get("status") == "SUBMITTED":
                student_status = "Completed"
            elif attempt and attempt.get("status") == "IN_PROGRESS":
                student_status = "Active"
            else:
                start_dt = parse_iso_datetime(exam["startDateTime"])
                end_dt = parse_iso_datetime(exam["endDateTime"])
                if now < start_dt:
                    student_status = "Upcoming"
                elif now > end_dt:
                    student_status = "Missed"
                else:
                    student_status = "Active"
            
            exam_doc["status"] = student_status
            result_exams.append(exam_doc)

        return success_response(data=result_exams)


    @staticmethod
    def start_exam(student_user_id, exam_id):
        student = OnlineExamRepository.get_student_by_userId(student_user_id)
        if not student:
            return error_response("Student profile not found.", 404)

        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        # Check published
        if exam["status"] != "PUBLISHED":
            return error_response("This exam is not open for attempts.", 400)

        # Check assigned class
        if student["classId"] not in exam["classIds"]:
            return error_response("Access denied. This exam is not assigned to your class.", 403)

        # Check current time window
        now = datetime.now(timezone.utc)
        start_time = parse_iso_datetime(exam["startDateTime"])
        end_time = parse_iso_datetime(exam["endDateTime"])
        
        if now < start_time:
            return error_response("Exam attempt period has not started yet.", 400)
        if now > end_time:
            return error_response("Exam attempt period has closed.", 400)

        # Check previous attempt
        attempt = OnlineExamRepository.get_attempt_by_student_and_exam(student["studentId"], exam_id)
        if attempt:
            if attempt.get("status") == "SUBMITTED":
                return error_response("You have already submitted an attempt for this exam.", 400)
            else:
                # Return existing in progress attempt details
                return success_response(message="Resuming exam attempt.", data=serialize_doc(attempt))

        # Create attempt
        attempt_id = f"ATT{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}"
        attempt_doc = {
            "attemptId": attempt_id,
            "examId": exam_id,
            "studentId": student["studentId"],
            "startedAt": now,
            "submittedAt": None,
            "status": "IN_PROGRESS",
            "timeTaken": 0
        }
        OnlineExamRepository.create_attempt(attempt_doc)
        return success_response(message="Exam attempt started successfully.", data=serialize_doc(attempt_doc), status_code=201)

    @staticmethod
    def get_exam_questions(student_user_id, exam_id):
        student = OnlineExamRepository.get_student_by_userId(student_user_id)
        if not student:
            return error_response("Student profile not found.", 404)

        # Check attempt
        attempt = OnlineExamRepository.get_attempt_by_student_and_exam(student["studentId"], exam_id)
        if not attempt or attempt.get("status") != "IN_PROGRESS":
            return error_response("Access denied. You must start the exam to view questions.", 403)

        questions = OnlineExamRepository.get_questions_by_exam_id(exam_id)
        serialized_questions = []
        for q in questions:
            q_doc = serialize_doc(q)
            # Remove sensitive fields
            q_doc.pop("correctAnswer", None)
            q_doc.pop("explanation", None)
            q_doc.pop("marks", None)
            serialized_questions.append(q_doc)

        return success_response(data=serialized_questions)

    @staticmethod
    def save_answer(student_user_id, exam_id, data):
        student = OnlineExamRepository.get_student_by_userId(student_user_id)
        if not student:
            return error_response("Student profile not found.", 404)

        attempt = OnlineExamRepository.get_attempt_by_student_and_exam(student["studentId"], exam_id)
        if not attempt or attempt.get("status") != "IN_PROGRESS":
            return error_response("No active in-progress attempt found for this exam.", 400)

        # Validate question exists
        questions = OnlineExamRepository.get_questions_by_exam_id(exam_id)
        valid_q_ids = {q["questionId"] for q in questions}
        if data["questionId"] not in valid_q_ids:
            return error_response(f"Question ID '{data['questionId']}' does not belong to this exam.", 400)

        # Save/update
        answer_doc = {
            "attemptId": attempt["attemptId"],
            "studentId": student["studentId"],
            "questionId": data["questionId"],
            "selectedAnswer": data["selectedAnswer"],
            "isCorrect": None,
            "marksAwarded": 0
        }
        OnlineExamRepository.save_student_answer(answer_doc)
        return success_response(message="Answer saved successfully.")

    @staticmethod
    def submit_exam(student_user_id, exam_id):
        student = OnlineExamRepository.get_student_by_userId(student_user_id)
        if not student:
            return error_response("Student profile not found.", 404)

        attempt = OnlineExamRepository.get_attempt_by_student_and_exam(student["studentId"], exam_id)
        if not attempt or attempt.get("status") != "IN_PROGRESS":
            return error_response("No active in-progress attempt found to submit.", 400)

        exam = OnlineExamRepository.get_exam_by_id(exam_id)
        if not exam:
            return error_response("Exam not found.", 404)

        now = datetime.now(timezone.utc)
        questions = OnlineExamRepository.get_questions_by_exam_id(exam_id)
        student_answers = {sa["questionId"]: sa for sa in OnlineExamRepository.get_answers_by_attempt(attempt["attemptId"])}

        correct_count = 0
        wrong_count = 0
        score = 0

        for q in questions:
            q_id = q["questionId"]
            ans_doc = student_answers.get(q_id)
            selected_ans = ans_doc["selectedAnswer"] if ans_doc else None

            if selected_ans is not None and selected_ans != "" and selected_ans != []:
                is_correct = compare_answers(selected_ans, q["correctAnswer"], q["type"])
                if is_correct:
                    correct_count += 1
                    marks_awarded = q["marks"]
                else:
                    wrong_count += 1
                    marks_awarded = -q.get("negativeMarks", 0)
            else:
                is_correct = False
                wrong_count += 1
                marks_awarded = 0


            score += marks_awarded

            # Save evaluated answer
            OnlineExamRepository.save_student_answer({
                "attemptId": attempt["attemptId"],
                "studentId": student["studentId"],
                "questionId": q_id,
                "selectedAnswer": selected_ans,
                "isCorrect": is_correct,
                "marksAwarded": marks_awarded
            })

        score = max(0, score) # Cap at 0
        total_marks = exam["totalMarks"]
        percentage = (score / total_marks) * 100 if total_marks > 0 else 0
        passed = score >= exam["passingMarks"]

        # Determine grade
        if percentage >= 90.0:
            grade = "A+"
        elif percentage >= 80.0:
            grade = "A"
        elif percentage >= 70.0:
            grade = "B"
        elif percentage >= 60.0:
            grade = "C"
        elif percentage >= 50.0:
            grade = "D"
        elif percentage >= 40.0:
            grade = "E"
        else:
            grade = "F"

        # Create Result record
        OnlineExamRepository.save_result({
            "examId": exam_id,
            "studentId": student["studentId"],
            "totalQuestions": len(questions),
            "correctAnswers": correct_count,
            "wrongAnswers": wrong_count,
            "score": score,
            "percentage": round(percentage, 2),
            "grade": grade,
            "passed": passed,
            "published": False,
            "submittedAt": now
        })

        # Lock attempt
        time_taken = int((now - attempt["startedAt"].replace(tzinfo=timezone.utc)).total_seconds()) if attempt.get("startedAt") else 0
        OnlineExamRepository.update_attempt(attempt["attemptId"], {
            "status": "SUBMITTED",
            "submittedAt": now,
            "timeTaken": time_taken
        })

        # Dispatch Notifications
        # Student Notification
        OnlineExamRepository.create_notification({
            "userId": student["userId"],
            "title": "Exam Attempt Submitted",
            "message": f"Your attempt for the online exam '{exam['title']}' has been submitted.",
            "type": "EXAM_SUBMISSION",
            "isRead": False,
            "createdAt": now
        })

        # Teacher Notifications
        # Find teachers assigned to student's class
        teachers = list(OnlineExamRepository.get_db().teachers.find({"assignedClasses": student["classId"]}))
        for t in teachers:
            if t.get("userId"):
                OnlineExamRepository.create_notification({
                    "userId": t["userId"],
                    "title": "Exam Attempt Submitted",
                    "message": f"Student '{student['name']}' has submitted the online exam '{exam['title']}'.",
                    "type": "EXAM_SUBMISSION",
                    "isRead": False,
                    "createdAt": now
                })

        return success_response(message="Exam submitted and auto-evaluated successfully.")

    @staticmethod
    def view_result(student_user_id, exam_id):
        student = OnlineExamRepository.get_student_by_userId(student_user_id)
        if not student:
            return error_response("Student profile not found.", 404)

        result = OnlineExamRepository.get_result(exam_id, student["studentId"])
        if not result:
            return error_response("No result record found for this exam attempt.", 404)

        if not result.get("published", False):
            return success_response(message="Results have not been published yet.", data=None)

        # Retrieve questions
        questions = OnlineExamRepository.get_questions_by_exam_id(exam_id)
        # Retrieve answers
        attempt = OnlineExamRepository.get_attempt_by_student_and_exam(student["studentId"], exam_id)
        student_answers = {sa["questionId"]: sa for sa in OnlineExamRepository.get_answers_by_attempt(attempt["attemptId"])} if attempt else {}

        # Build review list
        review_list = []
        for q in questions:
            ans_doc = student_answers.get(q["questionId"])
            review_list.append({
                "questionId": q["questionId"],
                "question": q["question"],
                "type": q["type"],
                "options": q.get("options"),
                "order": q.get("order"),
                "correctAnswer": q["correctAnswer"],
                "studentAnswer": ans_doc.get("selectedAnswer") if ans_doc else None,
                "explanation": q.get("explanation", ""),
                "marks": q["marks"],
                "isCorrect": ans_doc.get("isCorrect") if ans_doc else False,
                "marksAwarded": ans_doc.get("marksAwarded") if ans_doc else 0
            })

        res_data = {
            "totalQuestions": result["totalQuestions"],
            "correctAnswers": result["correctAnswers"],
            "wrongAnswers": result["wrongAnswers"],
            "score": result["score"],
            "percentage": result["percentage"],
            "grade": result["grade"],
            "passed": result["passed"],
            "review": review_list
        }

        return success_response(data=res_data)

import time
from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import db_wrapper
from services.audit_service import AuditService
from utils.response import success_response, error_response
from utils.helpers import serialize_doc

class ExamService:
    @staticmethod
    def create_exam(teacher_id, exam_data: dict, role="TEACHER"):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam_id = exam_data.get("examId")
        if not exam_id:
            exam_id = f"EXM{int(time.time())}"
            
        # 1. Unique ID check
        if db.exams.find_one({"examId": exam_id}):
            return error_response(f"Exam ID '{exam_id}' already exists.", 400)
            
        class_id = exam_data.get("classId")
        
        # 2. Duplicate Check: same class, term, academic year
        dup = db.exams.find_one({
            "classId": class_id,
            "term": exam_data.get("term"),
            "academicYear": exam_data.get("academicYear")
        })
        if dup:
            return error_response("An exam for this class, term, and academic year already exists.", 400)
            
        # Verify class exists
        class_filter = {"_id": class_id}
        try:
            class_filter = {"_id": ObjectId(class_id)}
        except Exception:
            pass
        if not db.classes.find_one(class_filter):
            return error_response("Class ID not found.", 404)
            
        now = datetime.now(timezone.utc)
        exam_doc = {
            "examId": exam_id,
            "examName": exam_data.get("examName"),
            "classId": class_id,
            "academicYear": exam_data.get("academicYear"),
            "term": exam_data.get("term"),
            "maxMarks": exam_data.get("maxMarks", 100),
            "passMarks": exam_data.get("passMarks", 35),
            "startDate": exam_data.get("startDate"),
            "endDate": exam_data.get("endDate"),
            "status": "DRAFT",
            "createdBy": teacher_id,
            "createdAt": now,
            "updatedAt": now
        }
        
        db.exams.insert_one(exam_doc)
        
        # Log action
        AuditService.log_action("CREATE_EXAM", teacher_id, role, {"examId": exam_id, "classId": class_id})
        
        return success_response(message="Exam created successfully.", data=serialize_doc(exam_doc), status_code=201)

    @staticmethod
    def update_exam(teacher_id, is_admin, exam_id, update_data: dict, role="TEACHER"):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        # Security check: Teachers can only edit their own exams
        if not is_admin and exam.get("createdBy") != teacher_id:
            return error_response("Access denied. You do not own this exam.", 403)
            
        # Check status: updates only permitted in DRAFT mode
        if exam.get("status") != "DRAFT":
            return error_response("Exam cannot be modified unless it is in DRAFT status.", 400)
            
        # Update validation if classId is changing
        class_id = update_data.get("classId")
        if class_id:
            class_filter = {"_id": class_id}
            try:
                class_filter = {"_id": ObjectId(class_id)}
            except Exception:
                pass
            if not db.classes.find_one(class_filter):
                return error_response("Class ID not found.", 404)
                
        now = datetime.now(timezone.utc)
        allowed_keys = ["examName", "classId", "academicYear", "term", "maxMarks", "passMarks", "startDate", "endDate"]
        fields_to_set = {k: v for k, v in update_data.items() if k in allowed_keys and v is not None}
        fields_to_set["updatedAt"] = now
        
        db.exams.update_one({"examId": exam_id}, {"$set": fields_to_set})
        updated_exam = db.exams.find_one({"examId": exam_id})
        
        # Log action
        AuditService.log_action("UPDATE_EXAM", teacher_id, role, {"examId": exam_id})
        
        return success_response(message="Exam updated successfully.", data=serialize_doc(updated_exam))

    @staticmethod
    def delete_exam(teacher_id, is_admin, exam_id, role="TEACHER"):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        # Delete constraints:
        # Teachers can delete ONLY if DRAFT and NO marks entered.
        # Super admin can delete at any time.
        if not is_admin:
            if exam.get("status") != "DRAFT":
                return error_response("Teachers can only delete exams in DRAFT status.", 400)
            # Check if any marks entered
            marks_count = db.marks.count_documents({"examId": exam_id})
            if marks_count > 0:
                return error_response("Teachers cannot delete an exam if marks have already been entered.", 400)
        else:
            # If admin is deleting, verify they have permission to delete
            if role != "SUPER_ADMIN":
                return error_response("Access denied.", 403)
                
        db.exams.delete_one({"examId": exam_id})
        
        # Clean up related marks and report cards
        db.marks.delete_many({"examId": exam_id})
        db.report_cards.delete_many({"examId": exam_id})
        
        # Log action
        AuditService.log_action("DELETE_EXAM", teacher_id, role, {"examId": exam_id})
        
        return success_response(message="Exam and its associated marks/report cards deleted successfully.")

    @staticmethod
    def get_exam(teacher_id, is_admin, exam_id):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        # Security check
        if not is_admin and exam.get("createdBy") != teacher_id:
            return error_response("Access denied. You do not own this exam.", 403)
            
        return success_response(data=serialize_doc(exam))

    @staticmethod
    def get_exams(teacher_id, is_admin, filters: dict):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        query = {}
        # Apply role filter
        if not is_admin:
            query["createdBy"] = teacher_id
            
        # Apply query parameter filters
        if filters.get("academicYear"):
            query["academicYear"] = filters["academicYear"]
        if filters.get("classId"):
            query["classId"] = filters["classId"]
        if filters.get("status"):
            query["status"] = filters["status"]
            
        exams = list(db.exams.find(query))
        return success_response(data=serialize_doc(exams))

    @staticmethod
    def bulk_save_marks(teacher_id, exam_id, students_marks: list, role="TEACHER"):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        # Security check
        if exam.get("createdBy") != teacher_id:
            return error_response("Access denied. You do not own this exam.", 403)
            
        # Status check
        if exam.get("status") != "DRAFT":
            return error_response("Marks can only be saved when the exam is in DRAFT status.", 400)
            
        class_id = exam["classId"]
        max_marks = exam["maxMarks"]
        
        # Verify all students and subjects
        for student_block in students_marks:
            student_id = student_block.get("studentId")
            
            # Verify student exists in the class
            student = db.students.find_one({"studentId": student_id})
            if not student:
                return error_response(f"Student with ID '{student_id}' not found.", 404)
            if student.get("classId") != class_id:
                return error_response(f"Student '{student_id}' does not belong to the class assigned to this exam.", 400)
                
            for sub_block in student_block.get("subjects", []):
                subject_id = sub_block.get("subjectId")
                marks_val = sub_block.get("marks")
                
                # Check marks limits
                if marks_val > max_marks:
                    return error_response(f"Marks scored ({marks_val}) cannot exceed the exam maximum ({max_marks}) for student '{student_id}'.", 400)
                    
                # Verify subject exists
                sub_filter = {"_id": subject_id}
                try:
                    sub_filter = {"_id": ObjectId(subject_id)}
                except Exception:
                    pass
                subject = db.subjects.find_one(sub_filter)
                if not subject:
                    subject = db.subjects.find_one({"subjectName": subject_id})
                    if not subject:
                        return error_response(f"Subject '{subject_id}' not found.", 404)
                        
        # Save marks
        now = datetime.now(timezone.utc)
        for student_block in students_marks:
            student_id = student_block.get("studentId")
            for sub_block in student_block.get("subjects", []):
                subject_id = sub_block.get("subjectId")
                
                # Normalize subject ID string
                sub_filter = {"_id": subject_id}
                try:
                    sub_filter = {"_id": ObjectId(subject_id)}
                except Exception:
                    pass
                subject = db.subjects.find_one(sub_filter)
                if not subject:
                    subject = db.subjects.find_one({"subjectName": subject_id})
                norm_subject_id = str(subject["_id"])
                
                filter_query = {
                    "studentId": student_id,
                    "classId": class_id,
                    "subjectId": norm_subject_id,
                    "examId": exam_id
                }
                
                update_fields = {
                    "teacherId": teacher_id,
                    "exam": exam["examName"],
                    "academicYear": exam["academicYear"],
                    "marks": sub_block.get("marks"),
                    "updatedAt": now
                }
                
                # Check for insertion to include createdAt
                existing = db.marks.find_one(filter_query)
                if not existing:
                    # Backward compatibility fallback compound check
                    compat_existing = db.marks.find_one({
                        "studentId": student_id,
                        "classId": class_id,
                        "subjectId": norm_subject_id,
                        "exam": exam["examName"],
                        "academicYear": exam["academicYear"]
                    })
                    if compat_existing:
                        db.marks.update_one({"_id": compat_existing["_id"]}, {"$set": {"examId": exam_id}})
                        filter_query = {"_id": compat_existing["_id"]}
                    else:
                        update_fields["createdAt"] = now
                        
                db.marks.update_one(filter_query, {"$set": update_fields}, upsert=True)
                
        # Log action
        AuditService.log_action("BULK_SAVE_MARKS", teacher_id, role, {"examId": exam_id})
        
        return success_response(message="Marks saved successfully.")

    @staticmethod
    def update_student_marks(teacher_id, is_admin, exam_id, student_id, subjects_marks: list, role="TEACHER"):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        # Security check: Teacher owns the exam (or Admin)
        if not is_admin and exam.get("createdBy") != teacher_id:
            return error_response("Access denied. You do not own this exam.", 403)
            
        # Status check
        if exam.get("status") != "DRAFT":
            return error_response("Marks can only be modified when the exam is in DRAFT status.", 400)
            
        class_id = exam["classId"]
        max_marks = exam["maxMarks"]
        
        # Verify student exists in this class
        student = db.students.find_one({"studentId": student_id})
        if not student:
            return error_response("Student not found.", 404)
        if student.get("classId") != class_id:
            return error_response("Student does not belong to the class assigned to this exam.", 400)
            
        # Verify subject IDs and marks limits
        for sub_block in subjects_marks:
            subject_id = sub_block.get("subjectId")
            marks_val = sub_block.get("marks")
            
            if marks_val > max_marks:
                return error_response(f"Marks scored ({marks_val}) cannot exceed the exam maximum ({max_marks}).", 400)
                
            sub_filter = {"_id": subject_id}
            try:
                sub_filter = {"_id": ObjectId(subject_id)}
            except Exception:
                pass
            subject = db.subjects.find_one(sub_filter)
            if not subject:
                subject = db.subjects.find_one({"subjectName": subject_id})
                if not subject:
                    return error_response(f"Subject '{subject_id}' not found.", 404)
                    
        # Perform updates
        now = datetime.now(timezone.utc)
        for sub_block in subjects_marks:
            subject_id = sub_block.get("subjectId")
            
            sub_filter = {"_id": subject_id}
            try:
                sub_filter = {"_id": ObjectId(subject_id)}
            except Exception:
                pass
            subject = db.subjects.find_one(sub_filter)
            if not subject:
                subject = db.subjects.find_one({"subjectName": subject_id})
            norm_subject_id = str(subject["_id"])
            
            filter_query = {
                "studentId": student_id,
                "classId": class_id,
                "subjectId": norm_subject_id,
                "examId": exam_id
            }
            
            update_fields = {
                "teacherId": exam.get("createdBy"),
                "exam": exam["examName"],
                "academicYear": exam["academicYear"],
                "marks": sub_block.get("marks"),
                "updatedAt": now
            }
            
            existing = db.marks.find_one(filter_query)
            if not existing:
                update_fields["createdAt"] = now
                
            db.marks.update_one(filter_query, {"$set": update_fields}, upsert=True)
            
        # Log action
        AuditService.log_action("UPDATE_STUDENT_MARKS", teacher_id, role, {"examId": exam_id, "studentId": student_id})
        
        return success_response(message="Student marks updated successfully.")

    @staticmethod
    def get_marksheet(teacher_id, exam_id):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        # Security check
        if exam.get("createdBy") != teacher_id:
            return error_response("Access denied. You do not own this exam.", 403)
            
        class_id = exam["classId"]
        
        # Get all subjects
        subjects = list(db.subjects.find({}))
        
        # Get all students enrolled in the class
        students = list(db.students.find({"classId": class_id}))
        
        # Get existing marks
        existing_marks = list(db.marks.find({"examId": exam_id}))
        
        data = {
            "exam": exam,
            "subjects": subjects,
            "students": students,
            "existingMarks": existing_marks
        }
        
        return success_response(message="Marksheet sheet retrieved successfully.", data=serialize_doc(data))

    @staticmethod
    def publish_exam(teacher_id, exam_id, role="TEACHER"):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        # Security check
        if exam.get("createdBy") != teacher_id:
            return error_response("Access denied. You do not own this exam.", 403)
            
        # Status check
        if exam.get("status") != "DRAFT":
            return error_response("Exam must be in DRAFT status to publish.", 400)
            
        class_id = exam["classId"]
        max_marks = exam["maxMarks"]
        pass_marks = exam["passMarks"]
        
        subjects = list(db.subjects.find({}))
        num_subjects = len(subjects)
        if num_subjects == 0:
            num_subjects = 1
            
        students = list(db.students.find({"classId": class_id}))
        if not students:
            return error_response("Cannot publish exam. No students exist in the class.", 400)
            
        student_results = []
        
        for student in students:
            student_id = student["studentId"]
            
            # Fetch all marks for this student and examId
            marks_list = list(db.marks.find({
                "studentId": student_id,
                "classId": class_id,
                "examId": exam_id
            }))
            
            marks_map = {str(mark["subjectId"]): mark["marks"] for mark in marks_list}
            
            total_marks = 0.0
            passed = True
            subject_marks_detail = []
            
            for subject in subjects:
                sub_id = str(subject["_id"])
                mark_val = marks_map.get(sub_id, 0.0)
                total_marks += mark_val
                
                # Check passMarks per subject
                if mark_val < pass_marks:
                    passed = False
                    
                subject_marks_detail.append({
                    "subjectId": sub_id,
                    "subjectName": subject["subjectName"],
                    "marks": mark_val,
                    "teacherId": next((mark.get("teacherId") for mark in marks_list if str(mark.get("subjectId")) == sub_id), None)
                })
                
            if not subjects:
                passed = False
                
            # Calculate overall percentage
            percentage = (total_marks / (num_subjects * max_marks)) * 100
            if percentage < 40.0:
                passed = False
                
            # Determine grade based on percentage
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
                
            student_results.append({
                "examId": exam_id,
                "studentId": student_id,
                "name": student["name"],
                "classId": class_id,
                "totalMarks": total_marks,
                "percentage": round(percentage, 2),
                "grade": grade,
                "passed": passed,
                "subjectMarks": subject_marks_detail
            })
            
        # Dense Ranking Calculations
        student_results.sort(key=lambda x: x["totalMarks"], reverse=True)
        
        current_rank = 1
        for idx, res in enumerate(student_results):
            if idx > 0 and res["totalMarks"] < student_results[idx - 1]["totalMarks"]:
                current_rank += 1
            res["rank"] = current_rank
            
        # Save report cards
        now = datetime.now(timezone.utc)
        for res in student_results:
            report_doc = {
                "examId": res["examId"],
                "studentId": res["studentId"],
                "name": res["name"],
                "classId": res["classId"],
                "totalMarks": res["totalMarks"],
                "percentage": res["percentage"],
                "grade": res["grade"],
                "passed": res["passed"],
                "rank": res["rank"],
                "subjectMarks": res["subjectMarks"],
                "publishedAt": now,
                # Compatibility fields
                "exam": exam["examName"],
                "academicYear": exam["academicYear"]
            }
            
            db.report_cards.update_one(
                {
                    "studentId": res["studentId"],
                    "classId": res["classId"],
                    "examId": exam_id
                },
                {"$set": report_doc},
                upsert=True
            )
            
        # Update Exam status to LOCKED
        db.exams.update_one({"examId": exam_id}, {"$set": {"status": "LOCKED", "updatedAt": now}})
        
        # Log action
        AuditService.log_action("PUBLISH_EXAM", teacher_id, role, {"examId": exam_id})
        
        return success_response(message="Exam published and locked successfully.")

    @staticmethod
    def unlock_exam(exam_id, admin_id):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        now = datetime.now(timezone.utc)
        db.exams.update_one({"examId": exam_id}, {"$set": {"status": "DRAFT", "updatedAt": now}})
        
        # Log action
        AuditService.log_action("UNLOCK_EXAM", admin_id, "SUPER_ADMIN", {"examId": exam_id})
        
        return success_response(message="Exam unlocked and status reset to DRAFT successfully.")

    @staticmethod
    def get_statistics(teacher_id, is_admin, exam_id):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        exam = db.exams.find_one({"examId": exam_id})
        if not exam:
            return error_response("Exam not found.", 404)
            
        # Security check
        if not is_admin and exam.get("createdBy") != teacher_id:
            return error_response("Access denied. You do not own this exam.", 403)
            
        # Fetch report cards for stats
        reports = list(db.report_cards.find({"examId": exam_id}))
        if not reports:
            return error_response("No statistics available. Please publish the exam first.", 400)
            
        total_students = len(reports)
        total_marks_list = [r["totalMarks"] for r in reports]
        
        highest_mark = max(total_marks_list) if total_marks_list else 0.0
        lowest_mark = min(total_marks_list) if total_marks_list else 0.0
        average_mark = sum(total_marks_list) / total_students if total_students > 0 else 0.0
        
        passed_count = sum(1 for r in reports if r["passed"])
        failed_count = total_students - passed_count
        
        pass_pct = (passed_count / total_students) * 100 if total_students > 0 else 0.0
        fail_pct = (failed_count / total_students) * 100 if total_students > 0 else 0.0
        
        # Grade Distribution
        grade_dist = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
        for r in reports:
            g = r.get("grade")
            if g in grade_dist:
                grade_dist[g] += 1
                
        # Top 10 Students (Phase 3 update)
        top_students = []
        sorted_reports = sorted(reports, key=lambda x: x["rank"])
        for r in sorted_reports[:10]:
            student = db.students.find_one({"studentId": r["studentId"]})
            top_students.append({
                "studentId": r["studentId"],
                "name": student.get("name") if student else r.get("name", "Unknown"),
                "totalMarks": r["totalMarks"],
                "rank": r["rank"]
            })
            
        # Subject-wise Average
        subjects = list(db.subjects.find({}))
        subject_averages = []
        for subject in subjects:
            sub_id = str(subject["_id"])
            sub_marks = list(db.marks.find({"examId": exam_id, "subjectId": sub_id}))
            if sub_marks:
                sub_avg = sum(m["marks"] for m in sub_marks) / len(sub_marks)
            else:
                sub_avg = 0.0
                
            subject_averages.append({
                "subjectId": sub_id,
                "subjectName": subject["subjectName"],
                "average": round(sub_avg, 2)
            })
            
        stats_data = {
            "highestMark": highest_mark,
            "lowestMark": lowest_mark,
            "average": round(average_mark, 2),
            "passPercentage": round(pass_pct, 2),
            "failPercentage": round(fail_pct, 2),
            "gradeDistribution": grade_dist,
            "topStudents": top_students,
            "subjectWiseAverage": subject_averages
        }
        
        return success_response(message="Statistics retrieved successfully.", data=serialize_doc(stats_data))

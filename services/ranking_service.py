from datetime import datetime, timezone
from database.mongodb import db_wrapper

class RankingService:
    @staticmethod
    def calculate_and_save_rankings(class_id, exam, academic_year):
        """
        Calculates and stores report cards and rankings for all students
        in a class for a given exam and academic year.
        """
        db = db_wrapper.db
        if db is None:
            return False
            
        # 1. Fetch all subjects
        subjects = list(db.subjects.find({}))
        subject_ids = [str(sub["_id"]) for sub in subjects]
        num_subjects = len(subjects)
        if num_subjects == 0:
            num_subjects = 1  # Avoid division by zero if no subjects defined
            
        # 2. Fetch all students in the class
        students = list(db.students.find({"classId": class_id}))
        if not students:
            return False
            
        student_results = []
        
        # 3. For each student, compute total marks, percentage, grades, pass/fail
        for student in students:
            student_id = student["studentId"]
            
            # Fetch all marks for this student for this exam and academic year
            marks_list = list(db.marks.find({
                "studentId": student_id,
                "classId": class_id,
                "exam": exam,
                "academicYear": academic_year
            }))
            
            # Map of subjectId to marks values
            marks_map = {str(mark["subjectId"]): mark["marks"] for mark in marks_list}
            
            total_marks = 0.0
            passed = True
            subject_marks_detail = []
            
            for subject in subjects:
                sub_id = str(subject["_id"])
                # If a mark is missing, count as 0.0 (and therefore failed this subject)
                mark_val = marks_map.get(sub_id, 0.0)
                total_marks += mark_val
                
                if mark_val < 40.0:
                    passed = False
                    
                # Find teacher who graded this subject, if available
                graded_by = next((mark.get("teacherId") for mark in marks_list if str(mark.get("subjectId")) == sub_id), None)
                
                subject_marks_detail.append({
                    "subjectId": sub_id,
                    "subjectName": subject["subjectName"],
                    "marks": mark_val,
                    "teacherId": graded_by
                })
                
            # If no subjects exist, student hasn't passed anything
            if not subjects:
                passed = False
                
            percentage = (total_marks / (num_subjects * 100)) * 100
            
            # Overall percentage must also be >= 40% to pass
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
                "studentId": student_id,
                "name": student["name"],
                "classId": class_id,
                "exam": exam,
                "academicYear": academic_year,
                "totalMarks": total_marks,
                "percentage": round(percentage, 2),
                "grade": grade,
                "passed": passed,
                "subjectMarks": subject_marks_detail
            })
            
        # 4. Sort students by totalMarks descending to compute rankings (handling ties)
        student_results.sort(key=lambda x: x["totalMarks"], reverse=True)
        
        current_rank = 1
        for idx, res in enumerate(student_results):
            if idx > 0 and res["totalMarks"] < student_results[idx - 1]["totalMarks"]:
                current_rank = idx + 1
            res["rank"] = current_rank
            res["publishedAt"] = datetime.now(timezone.utc)
            
        # 5. Save/Update report cards in the database
        for res in student_results:
            db.report_cards.update_one(
                {
                    "studentId": res["studentId"],
                    "classId": res["classId"],
                    "exam": res["exam"],
                    "academicYear": res["academicYear"]
                },
                {"$set": res},
                upsert=True
            )
            
        return True
        
    @staticmethod
    def is_published(class_id, exam, academic_year):
        """Check if marks are published for this class, exam, and academic year."""
        db = db_wrapper.db
        if db is None:
            return False
        count = db.report_cards.count_documents({
            "classId": class_id,
            "exam": exam,
            "academicYear": academic_year
        })
        return count > 0

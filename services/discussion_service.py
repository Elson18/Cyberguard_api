from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import db_wrapper
from utils.response import success_response, error_response
from utils.helpers import serialize_doc

class DiscussionService:
    @staticmethod
    def create_discussion(student_user_id, data):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        # 1. Fetch Student profile
        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)

        student_id = student.get("studentId")
        student_name = student.get("name")
        class_id = student.get("classId")

        # 2. Resolve class teacher from class
        class_filter = {"_id": class_id}
        try:
            class_filter = {"_id": ObjectId(class_id)}
        except Exception:
            pass
        cls = db.classes.find_one(class_filter)
        class_teacher_id = cls.get("classTeacher") if cls else None

        # 3. Generate sequential discussion ID
        highest = 0
        for disc in db.discussions.find({}, {"discussionId": 1}):
            disc_id = disc.get("discussionId", "")
            if disc_id.startswith("DISC"):
                try:
                    num = int(disc_id[4:])
                    if num > highest:
                        highest = num
                except ValueError:
                    pass
        discussion_id = f"DISC{highest + 1:03d}"

        # 4. Create discussion document
        now = datetime.now(timezone.utc)
        discussion_doc = {
            "discussionId": discussion_id,
            "studentId": student_id,
            "studentName": student_name,
            "classId": class_id,
            "teacherId": class_teacher_id,
            "title": data["title"],
            "category": data["category"].upper(),
            "priority": data["priority"].upper(),
            "status": "OPEN",
            "createdAt": now,
            "updatedAt": now,
            "lastMessageAt": now,
            "lastMessageBy": "student"
        }
        db.discussions.insert_one(discussion_doc)

        # 5. Create initial message
        message_doc = {
            "discussionId": discussion_id,
            "senderId": student_id,
            "senderRole": "STUDENT",
            "message": data["message"],
            "attachments": [],
            "createdAt": now,
            "isEdited": False,
            "editedAt": None
        }
        db.discussion_messages.insert_one(message_doc)

        # 6. Create notification records for all teachers assigned to this class
        # (and class teacher if not already in that list)
        teacher_user_ids = set()
        for t in db.teachers.find({"assignedClasses": class_id}):
            if t.get("userId"):
                teacher_user_ids.add(t["userId"])
        if class_teacher_id:
            ct = db.teachers.find_one({"teacherId": class_teacher_id})
            if ct and ct.get("userId"):
                teacher_user_ids.add(ct["userId"])

        for t_uid in teacher_user_ids:
            db.notifications.insert_one({
                "userId": t_uid,
                "title": "New Discussion",
                "message": "A student has created a new discussion.",
                "type": "DISCUSSION",
                "isRead": False,
                "createdAt": now
            })

        return success_response(
            message="Discussion created successfully.",
            data={},
            status_code=201
        )

    @staticmethod
    def get_student_discussions(student_user_id, status_filter=None, priority_filter=None):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)

        query = {"studentId": student["studentId"]}
        if status_filter:
            query["status"] = status_filter.upper()
        if priority_filter:
            query["priority"] = priority_filter.upper()

        discussions = list(db.discussions.find(query).sort("createdAt", -1))
        return success_response(data=serialize_doc(discussions))

    @staticmethod
    def get_discussion_details(user_id, role, discussion_id):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        discussion = db.discussions.find_one({"discussionId": discussion_id})
        if not discussion:
            return error_response("Discussion not found.", 404)

        # Enforce role-based access
        if role == "STUDENT":
            student = db.students.find_one({"userId": user_id})
            if not student or student.get("studentId") != discussion.get("studentId"):
                return error_response("Access denied. You do not own this discussion.", 403)
        elif role == "TEACHER":
            teacher = db.teachers.find_one({"userId": user_id})
            if not teacher or discussion.get("classId") not in teacher.get("assignedClasses", []):
                return error_response("Access denied. You are not assigned to this class.", 403)

        messages = list(db.discussion_messages.find({"discussionId": discussion_id}).sort("createdAt", 1))

        return success_response(data={
            "discussion": serialize_doc(discussion),
            "messages": serialize_doc(messages)
        })

    @staticmethod
    def send_student_reply(student_user_id, discussion_id, message):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)

        discussion = db.discussions.find_one({"discussionId": discussion_id})
        if not discussion:
            return error_response("Discussion not found.", 404)

        if discussion.get("studentId") != student.get("studentId"):
            return error_response("Access denied. You do not own this discussion.", 403)

        if discussion.get("status") == "CLOSED":
            return error_response("Cannot reply to a closed discussion.", 400)

        now = datetime.now(timezone.utc)
        message_doc = {
            "discussionId": discussion_id,
            "senderId": student.get("studentId"),
            "senderRole": "STUDENT",
            "message": message,
            "attachments": [],
            "createdAt": now,
            "isEdited": False,
            "editedAt": None
        }
        db.discussion_messages.insert_one(message_doc)

        db.discussions.update_one(
            {"discussionId": discussion_id},
            {"$set": {
                "updatedAt": now,
                "lastMessageAt": now,
                "lastMessageBy": "student"
            }}
        )

        # Notify teachers of class
        teacher_user_ids = set()
        for t in db.teachers.find({"assignedClasses": discussion.get("classId")}):
            if t.get("userId"):
                teacher_user_ids.add(t["userId"])
        if discussion.get("teacherId"):
            ct = db.teachers.find_one({"teacherId": discussion.get("teacherId")})
            if ct and ct.get("userId"):
                teacher_user_ids.add(ct["userId"])

        for t_uid in teacher_user_ids:
            db.notifications.insert_one({
                "userId": t_uid,
                "title": "New Reply",
                "message": f"Student {student.get('name')} has replied to the discussion.",
                "type": "DISCUSSION",
                "isRead": False,
                "createdAt": now
            })

        return success_response(message="Reply sent successfully.", data={})

    @staticmethod
    def delete_student_discussion(student_user_id, discussion_id):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)

        discussion = db.discussions.find_one({"discussionId": discussion_id})
        if not discussion:
            return error_response("Discussion not found.", 404)

        if discussion.get("studentId") != student.get("studentId"):
            return error_response("Access denied. You do not own this discussion.", 403)

        if discussion.get("status") != "OPEN":
            return error_response("Cannot delete discussion. Status is not OPEN.", 400)

        # Check if there are teacher replies
        teacher_reply_count = db.discussion_messages.count_documents({
            "discussionId": discussion_id,
            "senderRole": {"$in": ["TEACHER", "SUPER_ADMIN"]}
        })
        if teacher_reply_count > 0:
            return error_response("Cannot delete discussion. It has teacher replies.", 400)

        # Delete discussion and messages
        db.discussions.delete_one({"discussionId": discussion_id})
        db.discussion_messages.delete_many({"discussionId": discussion_id})

        return success_response(message="Discussion deleted successfully.", data={})

    @staticmethod
    def get_teacher_discussions(teacher_user_id, class_id_filter=None, status_filter=None, category_filter=None, priority_filter=None):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        teacher = db.teachers.find_one({"userId": teacher_user_id})
        if not teacher:
            return error_response("Teacher profile not found.", 404)

        assigned_classes = teacher.get("assignedClasses", [])
        if not assigned_classes:
            return success_response(data=[])

        query = {"classId": {"$in": assigned_classes}}
        if class_id_filter:
            if class_id_filter not in assigned_classes:
                return success_response(data=[])
            query["classId"] = class_id_filter

        if status_filter:
            query["status"] = status_filter.upper()
        if category_filter:
            query["category"] = category_filter.upper()
        if priority_filter:
            query["priority"] = priority_filter.upper()

        discussions = list(db.discussions.find(query).sort("createdAt", -1))
        return success_response(data=serialize_doc(discussions))

    @staticmethod
    def send_teacher_reply(teacher_user_id, discussion_id, message):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        teacher = db.teachers.find_one({"userId": teacher_user_id})
        if not teacher:
            return error_response("Teacher profile not found.", 404)

        discussion = db.discussions.find_one({"discussionId": discussion_id})
        if not discussion:
            return error_response("Discussion not found.", 404)

        if discussion.get("classId") not in teacher.get("assignedClasses", []):
            return error_response("Access denied. You are not assigned to the class of this discussion.", 403)

        if discussion.get("status") == "CLOSED":
            return error_response("Cannot reply to a closed discussion.", 400)

        now = datetime.now(timezone.utc)
        message_doc = {
            "discussionId": discussion_id,
            "senderId": teacher.get("teacherId"),
            "senderRole": "TEACHER",
            "message": message,
            "attachments": [],
            "createdAt": now,
            "isEdited": False,
            "editedAt": None
        }
        db.discussion_messages.insert_one(message_doc)

        update_fields = {
            "updatedAt": now,
            "lastMessageAt": now,
            "lastMessageBy": "teacher"
        }
        if discussion.get("status") == "OPEN":
            update_fields["status"] = "IN_PROGRESS"

        db.discussions.update_one({"discussionId": discussion_id}, {"$set": update_fields})

        # Notify student
        student = db.students.find_one({"studentId": discussion.get("studentId")})
        if student and student.get("userId"):
            db.notifications.insert_one({
                "userId": student.get("userId"),
                "title": "New Reply",
                "message": "A teacher has replied to your discussion.",
                "type": "DISCUSSION",
                "isRead": False,
                "createdAt": now
            })

        return success_response(message="Reply sent successfully.", data={})

    @staticmethod
    def change_discussion_status(user_id, role, discussion_id, new_status):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        discussion = db.discussions.find_one({"discussionId": discussion_id})
        if not discussion:
            return error_response("Discussion not found.", 404)

        # Authorize and enforce rules
        if role == "TEACHER":
            teacher = db.teachers.find_one({"userId": user_id})
            if not teacher or discussion.get("classId") not in teacher.get("assignedClasses", []):
                return error_response("Access denied. You are not assigned to the class of this discussion.", 403)
            if new_status == "CLOSED":
                return error_response("Teachers are not authorized to close discussions.", 403)
        elif role != "SUPER_ADMIN":
            return error_response("Unauthorized access.", 403)

        now = datetime.now(timezone.utc)
        db.discussions.update_one(
            {"discussionId": discussion_id},
            {"$set": {"status": new_status, "updatedAt": now}}
        )

        # Notify student
        student = db.students.find_one({"studentId": discussion.get("studentId")})
        if student and student.get("userId"):
            msg_map = {
                "RESOLVED": "Your discussion has been marked as resolved.",
                "CLOSED": "Your discussion has been closed."
            }
            title_map = {
                "RESOLVED": "Discussion Resolved",
                "CLOSED": "Discussion Closed"
            }
            db.notifications.insert_one({
                "userId": student.get("userId"),
                "title": title_map.get(new_status, "Discussion Status Updated"),
                "message": msg_map.get(new_status, f"Your discussion status has been updated to {new_status}."),
                "type": "DISCUSSION",
                "isRead": False,
                "createdAt": now
            })

        return success_response(message="Status updated successfully.", data={})

    @staticmethod
    def get_all_discussions(school=None, class_id=None, teacher_id=None, student_id=None, status=None, category=None, priority=None):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        query = {}
        # Apply filters
        if school:
            query["school"] = school
        if class_id:
            query["classId"] = class_id
        if teacher_id:
            query["teacherId"] = teacher_id
        if student_id:
            query["studentId"] = student_id
        if status:
            query["status"] = status.upper()
        if category:
            query["category"] = category.upper()
        if priority:
            query["priority"] = priority.upper()

        discussions = list(db.discussions.find(query).sort("createdAt", -1))
        return success_response(data=serialize_doc(discussions))

    @staticmethod
    def send_admin_reply(admin_user_id, discussion_id, message):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        discussion = db.discussions.find_one({"discussionId": discussion_id})
        if not discussion:
            return error_response("Discussion not found.", 404)

        now = datetime.now(timezone.utc)
        message_doc = {
            "discussionId": discussion_id,
            "senderId": admin_user_id,
            "senderRole": "SUPER_ADMIN",
            "message": message,
            "attachments": [],
            "createdAt": now,
            "isEdited": False,
            "editedAt": None
        }
        db.discussion_messages.insert_one(message_doc)

        update_fields = {
            "updatedAt": now,
            "lastMessageAt": now,
            "lastMessageBy": "admin"
        }
        if discussion.get("status") == "OPEN":
            update_fields["status"] = "IN_PROGRESS"

        db.discussions.update_one({"discussionId": discussion_id}, {"$set": update_fields})

        # Notify student
        student = db.students.find_one({"studentId": discussion.get("studentId")})
        if student and student.get("userId"):
            db.notifications.insert_one({
                "userId": student.get("userId"),
                "title": "New Reply",
                "message": "An administrator has replied to your discussion.",
                "type": "DISCUSSION",
                "isRead": False,
                "createdAt": now
            })

        return success_response(message="Reply sent successfully.", data={})

    @staticmethod
    def delete_admin_discussion(discussion_id):
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        discussion = db.discussions.find_one({"discussionId": discussion_id})
        if not discussion:
            return error_response("Discussion not found.", 404)

        db.discussions.delete_one({"discussionId": discussion_id})
        db.discussion_messages.delete_many({"discussionId": discussion_id})

        return success_response(message="Discussion deleted successfully.", data={})

    @staticmethod
    def get_statistics():
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)

        total = db.discussions.count_documents({})
        open_cnt = db.discussions.count_documents({"status": "OPEN"})
        in_progress_cnt = db.discussions.count_documents({"status": "IN_PROGRESS"})
        resolved_cnt = db.discussions.count_documents({"status": "RESOLVED"})
        closed_cnt = db.discussions.count_documents({"status": "CLOSED"})
        high_priority_cnt = db.discussions.count_documents({"priority": "HIGH"})

        stats = {
            "totalDiscussions": total,
            "open": open_cnt,
            "inProgress": in_progress_cnt,
            "resolved": resolved_cnt,
            "closed": closed_cnt,
            "highPriority": high_priority_cnt
        }
        return success_response(message="Discussion statistics retrieved successfully.", data=stats)

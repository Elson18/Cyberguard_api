from datetime import datetime, timezone, timedelta
from bson import ObjectId
from database.mongodb import db_wrapper
from utils.helpers import serialize_doc
from utils.response import success_response, error_response

class FeesService:
    @staticmethod
    def update_overdue_fees():
        """Automatically checks due dates and marks unpaid/partially paid fees as OVERDUE."""
        db = db_wrapper.db
        if db is None:
            return
        now = datetime.now(timezone.utc)
        current_date_str = now.strftime("%Y-%m-%d")
        
        # Find all fee structures where due date is in the past
        overdue_structures = list(db.fee_structures.find({"dueDate": {"$lt": current_date_str}}))
        for struct in overdue_structures:
            fee_struct_id = struct.get("feeStructureId")
            title = struct.get("title")
            
            # Find student fees for this structure that are pending but not already OVERDUE
            pending_fees = list(db.student_fees.find({
                "feeStructureId": fee_struct_id,
                "pendingAmount": {"$gt": 0},
                "status": {"$ne": "OVERDUE"}
            }))
            
            for fee in pending_fees:
                db.student_fees.update_one(
                    {"_id": fee["_id"]},
                    {"$set": {"status": "OVERDUE", "updatedAt": now}}
                )
                
                # Create notification record
                db.fee_notifications.insert_one({
                    "studentId": fee.get("studentId"),
                    "title": "Fee Overdue",
                    "message": f"Your fee payment for '{title}' is overdue. Pending amount: {fee.get('pendingAmount')}.",
                    "isRead": False,
                    "type": "FEE_OVERDUE",
                    "createdAt": now
                })

    @staticmethod
    def create_fee_structure(title, academic_year, class_ids, fee_items, due_date, created_by):
        """Creates a fee structure, assigns it to all students in specified classes, and creates notifications."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # Check duplicate fee structures by title and academicYear
        if db.fee_structures.find_one({"title": title, "academicYear": academic_year}):
            return error_response("Fee structure with this title and academic year already exists.", 400)
            
        # Validate class IDs
        for cid in class_ids:
            class_filter = {"_id": cid}
            try:
                class_filter = {"_id": ObjectId(cid)}
            except Exception:
                pass
            if not db.classes.find_one(class_filter):
                return error_response(f"Class ID '{cid}' not found.", 404)
                
        # Generate unique feeStructureId
        count = db.fee_structures.count_documents({})
        fee_struct_id = f"FEE{count + 1:03d}"
        while db.fee_structures.find_one({"feeStructureId": fee_struct_id}):
            count += 1
            fee_struct_id = f"FEE{count + 1:03d}"
            
        total_amount = sum(item["amount"] for item in fee_items)
        now = datetime.now(timezone.utc)
        
        # Save fee structure
        struct_doc = {
            "feeStructureId": fee_struct_id,
            "title": title,
            "academicYear": academic_year,
            "classIds": class_ids,
            "feeItems": fee_items,
            "totalAmount": total_amount,
            "dueDate": due_date,
            "status": "ACTIVE",
            "createdBy": created_by,
            "createdAt": now,
            "updatedAt": now
        }
        db.fee_structures.insert_one(struct_doc)
        
        # Assign to students in specified classes
        students = list(db.students.find({"classId": {"$in": class_ids}}))
        for student in students:
            student_id = student.get("studentId")
            class_id = student.get("classId")
            
            student_fee_doc = {
                "studentId": student_id,
                "classId": class_id,
                "feeStructureId": fee_struct_id,
                "academicYear": academic_year,
                "totalAmount": total_amount,
                "paidAmount": 0.0,
                "pendingAmount": total_amount,
                "status": "UNPAID",
                "lastReminderAt": None,
                "createdAt": now,
                "updatedAt": now
            }
            try:
                db.student_fees.insert_one(student_fee_doc)
            except Exception:
                pass
                
            # Create notification
            db.fee_notifications.insert_one({
                "studentId": student_id,
                "title": "Fee Assigned",
                "message": f"A new fee structure '{title}' has been assigned to you. Total amount: {total_amount}.",
                "isRead": False,
                "type": "FEE_ASSIGNMENT",
                "createdAt": now
            })
            
        # Run overdue checks immediately to set correct initial statuses if due date is already passed
        FeesService.update_overdue_fees()
        
        # Get updated structure to return
        saved_struct = db.fee_structures.find_one({"feeStructureId": fee_struct_id})
        return success_response(
            message="Fee structure created and assigned successfully.",
            data=serialize_doc(saved_struct),
            status_code=201
        )

    @staticmethod
    def get_fee_structures(academic_year=None, class_id=None, status=None):
        """Retrieves fee structures based on filters."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        FeesService.update_overdue_fees()
        
        query = {}
        if academic_year:
            query["academicYear"] = academic_year
        if class_id:
            query["classIds"] = class_id
        if status:
            query["status"] = status
            
        structures = list(db.fee_structures.find(query))
        return success_response(data=serialize_doc(structures))

    @staticmethod
    def get_fee_structure(fee_structure_id):
        """Retrieves details of a single fee structure."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        FeesService.update_overdue_fees()
        
        struct = db.fee_structures.find_one({"feeStructureId": fee_structure_id})
        if not struct:
            return error_response("Fee structure not found.", 404)
        return success_response(data=serialize_doc(struct))

    @staticmethod
    def update_fee_structure(fee_structure_id, title, academic_year, class_ids, fee_items, due_date):
        """Updates a fee structure only if no payments have been recorded."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # Verify exists
        struct = db.fee_structures.find_one({"feeStructureId": fee_structure_id})
        if not struct:
            return error_response("Fee structure not found.", 404)
            
        # Only allow updates if no payments have been recorded
        if db.fee_payments.find_one({"feeStructureId": fee_structure_id}):
            return error_response("Cannot update fee structure because payments have already been recorded.", 400)
            
        # Validate class IDs
        for cid in class_ids:
            class_filter = {"_id": cid}
            try:
                class_filter = {"_id": ObjectId(cid)}
            except Exception:
                pass
            if not db.classes.find_one(class_filter):
                return error_response(f"Class ID '{cid}' not found.", 404)
                
        total_amount = sum(item["amount"] for item in fee_items)
        now = datetime.now(timezone.utc)
        
        # Update structure doc
        db.fee_structures.update_one(
            {"feeStructureId": fee_structure_id},
            {"$set": {
                "title": title,
                "academicYear": academic_year,
                "classIds": class_ids,
                "feeItems": fee_items,
                "totalAmount": total_amount,
                "dueDate": due_date,
                "updatedAt": now
            }}
        )
        
        # Re-sync student assignments
        # 1. Delete student_fees for classes no longer assigned
        db.student_fees.delete_many({
            "feeStructureId": fee_structure_id,
            "classId": {"$nin": class_ids}
        })
        
        # 2. Add / Update for students in current class list
        students = list(db.students.find({"classId": {"$in": class_ids}}))
        for student in students:
            student_id = student.get("studentId")
            class_id = student.get("classId")
            
            existing = db.student_fees.find_one({"studentId": student_id, "feeStructureId": fee_structure_id})
            if existing:
                db.student_fees.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "classId": class_id,
                        "totalAmount": total_amount,
                        "pendingAmount": total_amount,
                        "academicYear": academic_year,
                        "updatedAt": now
                    }}
                )
            else:
                db.student_fees.insert_one({
                    "studentId": student_id,
                    "classId": class_id,
                    "feeStructureId": fee_structure_id,
                    "academicYear": academic_year,
                    "totalAmount": total_amount,
                    "paidAmount": 0.0,
                    "pendingAmount": total_amount,
                    "status": "UNPAID",
                    "lastReminderAt": None,
                    "createdAt": now,
                    "updatedAt": now
                })
                
                db.fee_notifications.insert_one({
                    "studentId": student_id,
                    "title": "Fee Assigned",
                    "message": f"A new fee structure '{title}' has been assigned to you. Total amount: {total_amount}.",
                    "isRead": False,
                    "type": "FEE_ASSIGNMENT",
                    "createdAt": now
                })
                
        # Run overdue checks immediately
        FeesService.update_overdue_fees()
        
        updated_struct = db.fee_structures.find_one({"feeStructureId": fee_structure_id})
        return success_response(
            message="Fee structure updated and assignments synchronized successfully.",
            data=serialize_doc(updated_struct)
        )

    @staticmethod
    def delete_fee_structure(fee_structure_id):
        """Deletes a fee structure and its assignments only if no payments exist."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        struct = db.fee_structures.find_one({"feeStructureId": fee_structure_id})
        if not struct:
            return error_response("Fee structure not found.", 404)
            
        # Check payments
        if db.fee_payments.find_one({"feeStructureId": fee_structure_id}):
            return error_response("Cannot delete fee structure because payments have already been recorded.", 400)
            
        # Delete structure and assignments
        db.fee_structures.delete_one({"feeStructureId": fee_structure_id})
        db.student_fees.delete_many({"feeStructureId": fee_structure_id})
        
        return success_response(message="Fee structure and assignments deleted successfully.")

    @staticmethod
    def get_dashboard():
        """Returns aggregated dashboard statistics for super admins."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        FeesService.update_overdue_fees()
        
        pipeline = [
            {"$group": {
                "_id": None,
                "totalFees": {"$sum": "$totalAmount"},
                "collected": {"$sum": "$paidAmount"},
                "pending": {"$sum": "$pendingAmount"}
            }}
        ]
        agg_res = list(db.student_fees.aggregate(pipeline))
        totals = agg_res[0] if agg_res else {"totalFees": 0, "collected": 0, "pending": 0}
        
        paid_count = db.student_fees.count_documents({"status": "PAID"})
        pending_count = db.student_fees.count_documents({"status": {"$in": ["UNPAID", "PARTIALLY_PAID"]}})
        overdue_count = db.student_fees.count_documents({"status": "OVERDUE"})
        
        data = {
            "totalFees": totals.get("totalFees", 0),
            "collected": totals.get("collected", 0),
            "pending": totals.get("pending", 0),
            "paidStudents": paid_count,
            "pendingStudents": pending_count,
            "overdueStudents": overdue_count
        }
        return success_response(data=data)

    @staticmethod
    def get_student_fee_list(class_id=None, status=None, student_name=None):
        """Returns matching student fees with names and fee titles."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        FeesService.update_overdue_fees()
        
        # Resolve student IDs by name if query is provided
        student_ids = None
        if student_name:
            matching_students = list(db.students.find({"name": {"$regex": student_name, "$options": "i"}}))
            student_ids = [s["studentId"] for s in matching_students]
            if not student_ids:
                return success_response(data=[])
                
        query = {}
        if class_id:
            query["classId"] = class_id
        if status:
            query["status"] = status
        if student_ids is not None:
            query["studentId"] = {"$in": student_ids}
            
        fees_records = list(db.student_fees.find(query))
        
        # Populate details
        result = []
        for rec in fees_records:
            s_doc = db.students.find_one({"studentId": rec["studentId"]})
            struct_doc = db.fee_structures.find_one({"feeStructureId": rec["feeStructureId"]})
            
            rec_serialized = serialize_doc(rec)
            rec_serialized["studentName"] = s_doc.get("name") if s_doc else "Unknown Student"
            rec_serialized["feeStructureTitle"] = struct_doc.get("title") if struct_doc else "Unknown Fee Structure"
            result.append(rec_serialized)
            
        return success_response(data=result)

    @staticmethod
    def send_reminders(student_ids, message):
        """Updates last reminder times and creates reminder notification records."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # Validate student IDs
        for sid in student_ids:
            if not db.students.find_one({"studentId": sid}):
                return error_response(f"Student ID '{sid}' not found.", 400)
                
        now = datetime.now(timezone.utc)
        
        # Update last reminder
        db.student_fees.update_many(
            {"studentId": {"$in": student_ids}, "status": {"$ne": "PAID"}},
            {"$set": {"lastReminderAt": now, "updatedAt": now}}
        )
        
        # Create notification records
        for sid in student_ids:
            db.fee_notifications.insert_one({
                "studentId": sid,
                "title": "Fee Reminder",
                "message": message,
                "isRead": False,
                "type": "FEE_REMINDER",
                "createdAt": now
            })
            
        return success_response(message="Fee reminders sent successfully.")

    @staticmethod
    def record_payment(student_id, fee_structure_id, amount, payment_mode, transaction_id, received_by):
        """Validates and records a student's payment, updates student fee record and status."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        # Verify student exists
        struct_student = db.students.find_one({"studentId": student_id})
        if not struct_student:
            return error_response("Student not found.", 400)
            
        # Verify fee structure exists
        fee_struct = db.fee_structures.find_one({"feeStructureId": fee_structure_id})
        if not fee_struct:
            return error_response("Fee structure not found.", 400)
            
        # Verify student fee assignment exists
        student_fee = db.student_fees.find_one({"studentId": student_id, "feeStructureId": fee_structure_id})
        if not student_fee:
            return error_response("No fee structure assignment found for this student.", 400)
            
        # Validate payment amount <= pending
        if amount > student_fee.get("pendingAmount", 0):
            return error_response("Payment amount exceeds pending fee amount.", 400)
            
        # Validate transaction ID uniqueness
        if db.fee_payments.find_one({"transactionId": transaction_id}):
            return error_response("Transaction ID already exists.", 400)
            
        # Generate paymentId
        count = db.fee_payments.count_documents({})
        payment_id = f"PAY{count + 1:03d}"
        while db.fee_payments.find_one({"paymentId": payment_id}):
            count += 1
            payment_id = f"PAY{count + 1:03d}"
            
        now = datetime.now(timezone.utc)
        
        # Create payment record
        payment_doc = {
            "paymentId": payment_id,
            "studentId": student_id,
            "feeStructureId": fee_structure_id,
            "amount": amount,
            "paymentMode": payment_mode,
            "transactionId": transaction_id,
            "paidOn": now,
            "receivedBy": received_by
        }
        db.fee_payments.insert_one(payment_doc)
        
        # Update student fee totals and status
        new_paid = student_fee.get("paidAmount", 0) + amount
        new_pending = student_fee.get("pendingAmount", 0) - amount
        
        if new_pending <= 0:
            new_status = "PAID"
        else:
            # Check if overdue
            due_date_str = fee_struct.get("dueDate")
            current_date_str = now.strftime("%Y-%m-%d")
            if due_date_str and current_date_str > due_date_str:
                new_status = "OVERDUE"
            else:
                new_status = "PARTIALLY_PAID"
                
        db.student_fees.update_one(
            {"_id": student_fee["_id"]},
            {"$set": {
                "paidAmount": new_paid,
                "pendingAmount": new_pending,
                "status": new_status,
                "updatedAt": now
            }}
        )
        
        # Create payment notification
        db.fee_notifications.insert_one({
            "studentId": student_id,
            "title": "Payment Recorded",
            "message": f"A payment of {amount} has been recorded for '{fee_struct.get('title')}'. Status is now {new_status}.",
            "isRead": False,
            "type": "FEE_PAYMENT",
            "createdAt": now
        })
        
        return success_response(
            message="Payment recorded successfully.",
            data=serialize_doc(payment_doc),
            status_code=201
        )

    @staticmethod
    def get_payment_history(student_id=None, class_id=None, date=None, payment_mode=None):
        """Retrieves and filters fee payments."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        query = {}
        if student_id:
            query["studentId"] = student_id
            
        # Resolve class student IDs if class filter is provided
        if class_id:
            class_students = list(db.students.find({"classId": class_id}))
            class_student_ids = [s["studentId"] for s in class_students]
            if not class_student_ids:
                return success_response(data=[])
            if "studentId" in query:
                # Intersect with target studentId
                if query["studentId"] not in class_student_ids:
                    return success_response(data=[])
            else:
                query["studentId"] = {"$in": class_student_ids}
                
        if payment_mode:
            query["paymentMode"] = payment_mode
            
        if date:
            try:
                start_date = datetime.strptime(date, "%Y-%m-%d")
                end_date = start_date + timedelta(days=1)
                query["paidOn"] = {"$gte": start_date, "$lt": end_date}
            except ValueError:
                return error_response("Date must be in YYYY-MM-DD format.", 400)
                
        payments = list(db.fee_payments.find(query).sort("paidOn", -1))
        
        # Populate extra info
        result = []
        for p in payments:
            s_doc = db.students.find_one({"studentId": p["studentId"]})
            struct_doc = db.fee_structures.find_one({"feeStructureId": p["feeStructureId"]})
            
            p_serialized = serialize_doc(p)
            p_serialized["studentName"] = s_doc.get("name") if s_doc else "Unknown Student"
            p_serialized["feeStructureTitle"] = struct_doc.get("title") if struct_doc else "Unknown Fee Structure"
            p_serialized["classId"] = s_doc.get("classId") if s_doc else None
            result.append(p_serialized)
            
        return success_response(data=result)

    @staticmethod
    def get_teacher_overview(teacher_user_id, search=None, status=None):
        """Allows teachers to view student fees in their assigned classes."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        FeesService.update_overdue_fees()
        
        teacher = db.teachers.find_one({"userId": teacher_user_id})
        if not teacher:
            return error_response("Teacher profile not found.", 404)
            
        assigned_classes = teacher.get("assignedClasses", [])
        if not assigned_classes:
            return success_response(data=[])
            
        # Build student query
        student_query = {"classId": {"$in": assigned_classes}}
        if search:
            student_query["name"] = {"$regex": search, "$options": "i"}
            
        students = list(db.students.find(student_query))
        if not students:
            return success_response(data=[])
            
        student_ids = [s["studentId"] for s in students]
        
        # Query student fees
        fee_query = {"studentId": {"$in": student_ids}}
        if status:
            if status == "PENDING":
                fee_query["status"] = {"$in": ["UNPAID", "PARTIALLY_PAID", "OVERDUE"]}
            else:
                fee_query["status"] = status
                
        fees_records = list(db.student_fees.find(fee_query))
        
        # Populate
        result = []
        for rec in fees_records:
            s_doc = db.students.find_one({"studentId": rec["studentId"]})
            struct_doc = db.fee_structures.find_one({"feeStructureId": rec["feeStructureId"]})
            
            rec_serialized = serialize_doc(rec)
            rec_serialized["studentName"] = s_doc.get("name") if s_doc else "Unknown Student"
            rec_serialized["feeStructureTitle"] = struct_doc.get("title") if struct_doc else "Unknown Fee Structure"
            result.append(rec_serialized)
            
        return success_response(data=result)

    @staticmethod
    def get_teacher_student_details(teacher_user_id, student_id):
        """Allows teachers to view read-only fee details of a student in their assigned classes."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        FeesService.update_overdue_fees()
        
        teacher = db.teachers.find_one({"userId": teacher_user_id})
        if not teacher:
            return error_response("Teacher profile not found.", 404)
            
        student = db.students.find_one({"studentId": student_id})
        if not student:
            return error_response("Student profile not found.", 404)
            
        # Verify access
        assigned_classes = teacher.get("assignedClasses", [])
        if student.get("classId") not in assigned_classes:
            return error_response("Access denied. Student is not in your assigned classes.", 403)
            
        fees_records = list(db.student_fees.find({"studentId": student_id}))
        
        result = []
        for rec in fees_records:
            struct_doc = db.fee_structures.find_one({"feeStructureId": rec["feeStructureId"]})
            rec_serialized = serialize_doc(rec)
            rec_serialized["studentName"] = student.get("name")
            rec_serialized["feeStructureTitle"] = struct_doc.get("title") if struct_doc else "Unknown Fee Structure"
            rec_serialized["dueDate"] = struct_doc.get("dueDate") if struct_doc else None
            rec_serialized["feeItems"] = struct_doc.get("feeItems") if struct_doc else []
            result.append(rec_serialized)
            
        return success_response(data=result)

    @staticmethod
    def get_student_fees(student_user_id):
        """Allows students to view their fee assignments."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        FeesService.update_overdue_fees()
        
        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)
            
        student_id = student.get("studentId")
        fees_records = list(db.student_fees.find({"studentId": student_id}))
        
        result = []
        for rec in fees_records:
            struct_doc = db.fee_structures.find_one({"feeStructureId": rec["feeStructureId"]})
            rec_serialized = serialize_doc(rec)
            rec_serialized["title"] = struct_doc.get("title") if struct_doc else "Unknown Fee Structure"
            rec_serialized["dueDate"] = struct_doc.get("dueDate") if struct_doc else None
            rec_serialized["feeItems"] = struct_doc.get("feeItems") if struct_doc else []
            result.append(rec_serialized)
            
        return success_response(data=result)

    @staticmethod
    def get_student_payments(student_user_id):
        """Allows students to view their payment history."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)
            
        student_id = student.get("studentId")
        payments = list(db.fee_payments.find({"studentId": student_id}).sort("paidOn", -1))
        
        result = []
        for p in payments:
            struct_doc = db.fee_structures.find_one({"feeStructureId": p["feeStructureId"]})
            p_serialized = serialize_doc(p)
            p_serialized["feeStructureTitle"] = struct_doc.get("title") if struct_doc else "Unknown Fee Structure"
            result.append(p_serialized)
            
        return success_response(data=result)

    @staticmethod
    def get_student_notifications(student_user_id):
        """Allows students to view their fee notifications."""
        db = db_wrapper.db
        if db is None:
            return error_response("Database connection not ready.", 500)
            
        student = db.students.find_one({"userId": student_user_id})
        if not student:
            return error_response("Student profile not found.", 404)
            
        student_id = student.get("studentId")
        notifications = list(db.fee_notifications.find({"studentId": student_id}).sort("createdAt", -1))
        return success_response(data=serialize_doc(notifications))

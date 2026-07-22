# Digital Student Rank Card System - Data Models Schema Documentation

This document describes all Pydantic request-validation models and schemas used in the Digital Student Rank Card system. All data transfer objects (DTOs) and validation schemas are located under the [models/](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models) directory.

---

## Table of Contents
1. [Class Model (`CreateClassSchema`)](#1-class-model)
2. [Subject Model (`CreateSubjectSchema`)](#2-subject-model)
3. [Teacher Model (`CreateTeacherSchema`)](#3-teacher-model)
4. [Student Model (`CreateStudentSchema`)](#4-student-model)
5. [User Models (`UserLoginSchema`, `ChangePasswordSchema`, `ResetPasswordSchema`)](#5-user-models)
6. [Marks Models (`CreateMarksSchema`, `UpdateMarksSchema`, `PublishMarksSchema`)](#6-marks-models)
7. [Exam Models (`CreateExamSchema`, `UpdateExamSchema`, `BulkSubjectMarkSchema`, etc.)](#7-exam-models)
8. [Fees Models (`FeeItemSchema`, `CreateFeeStructureSchema`, `UpdateFeeStructureSchema`, `RecordPaymentSchema`, `SendReminderSchema`)](#8-fees-models)

---

## 1. Class Model

Defined in [class_model.py](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models/class_model.py).

### `CreateClassSchema`
Used when creating a new class grade/section.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **className** | `str` | **Yes** | Min length: 1<br>Max length: 50 | Name of the class, e.g., Grade 10. |
| **section** | `str` | **Yes** | Min length: 1<br>Max length: 10 | Section of the class, e.g., A. |
| **classTeacher** | `str` | No (Default: `None`) | None | `teacherId` of the class teacher. |

---

## 2. Subject Model

Defined in [subject_model.py](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models/subject_model.py).

### `CreateSubjectSchema`
Used when creating a new subject.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **subjectName** | `str` | **Yes** | Min length: 2<br>Max length: 100 | Name of the subject, e.g., Mathematics. |

---

## 3. Teacher Model

Defined in [teacher_model.py](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models/teacher_model.py).

### `CreateTeacherSchema`
Used when onboarding a teacher.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **userId** | `str` | **Yes** | Min length: 3<br>Max length: 50 | Unique login ID for the teacher. |
| **password** | `str` | **Yes** | Min length: 6 | Login password. |
| **name** | `str` | **Yes** | Min length: 2<br>Max length: 100 | Full name of the teacher. |
| **department** | `str` | **Yes** | Min length: 2<br>Max length: 100 | Teacher's department. |
| **teacherId** | `str` | No (Default: `None`) | None | Optional custom unique teacher ID. If not provided, it will match `userId`. |

---

## 4. Student Model

Defined in [student_model.py](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models/student_model.py).

### `CreateStudentSchema`
Used when onboarding a student.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **userId** | `str` | **Yes** | Min length: 3<br>Max length: 50 | Unique login ID for the student. |
| **password** | `str` | **Yes** | Min length: 6 | Login password. |
| **name** | `str` | **Yes** | Min length: 2<br>Max length: 100 | Full name of the student. |
| **classId** | `str` | **Yes** | None | ID of the class the student is enrolled in. |
| **rollNumber** | `str` | **Yes** | None | Roll number in the class. |
| **studentId** | `str` | No (Default: `None`) | None | Optional custom student ID. If not provided, it will match `userId`. |

---

## 5. User Models

Defined in [user_model.py](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models/user_model.py).

### `UserLoginSchema`
Used for authenticating users.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **userId** | `str` | **Yes** | Min length: 3<br>Max length: 50 | Unique identifier for the user login. |
| **password** | `str` | **Yes** | Min length: 6 | User password. |

### `ChangePasswordSchema`
Used when a user updates their password.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **oldPassword** | `str` | **Yes** | Min length: 6 | Current password. |
| **newPassword** | `str` | **Yes** | Min length: 6 | New password. |

### `ResetPasswordSchema`
Used by administrator to force reset a user's password.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **newPassword** | `str` | **Yes** | Min length: 6 | The new password to set. |

---

## 6. Marks Models

Defined in [marks_model.py](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models/marks_model.py).

### `CreateMarksSchema`
Used when recording individual subject marks.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **studentId** | `str` | **Yes** | None | `studentId` of the student. |
| **classId** | `str` | **Yes** | None | `classId` (string ID) of the class. |
| **subjectId** | `str` | **Yes** | None | `subjectId` (string ID) of the subject. |
| **exam** | `str` | **Yes** | None | Name of the exam, e.g., Midterm, Final. |
| **marks** | `float` | **Yes** | Value $\ge 0$ and $\le 100$ | Marks scored, between 0 and 100. |
| **academicYear** | `str` | **Yes** | None | Academic year, e.g., 2026. |

### `UpdateMarksSchema`
Used when editing recorded marks.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **marks** | `float` | **Yes** | Value $\ge 0$ and $\le 100$ | Updated marks scored, between 0 and 100. |

### `PublishMarksSchema`
Used when publishing marks for an entire class and exam.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **classId** | `str` | **Yes** | None | `classId` of the class to publish marks for. |
| **exam** | `str` | **Yes** | None | Name of the exam to publish marks for. |
| **academicYear** | `str` | **Yes** | None | Academic year to publish marks for. |

---

## 7. Exam Models

Defined in [exam_model.py](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models/exam_model.py).

### `CreateExamSchema`
Used when creating a scheduled exam.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **examId** | `str` | No (Default: `None`) | Min length: 2<br>Max length: 20 | Unique custom exam ID. |
| **examName** | `str` | **Yes** | Min length: 2<br>Max length: 100 | Name of the exam. |
| **classId** | `str` | **Yes** | Min length: 1 | The class ID for which the exam is created. |
| **academicYear** | `str` | **Yes** | Min length: 4<br>Max length: 9 | Academic year, e.g. 2026 or 2025-26. |
| **term** | `str` | **Yes** | Min length: 1<br>Max length: 50 | Term of the exam (e.g. Term 1, Term 2). |
| **maxMarks** | `int` | No (Default: `100`) | Value $\ge 1$ | Maximum marks for the exam. |
| **passMarks** | `int` | No (Default: `35`) | Value $\ge 0$ | Passing threshold marks. |
| **startDate** | `str` | **Yes** | Format: `YYYY-MM-DD` | Start date of the exam. |
| **endDate** | `str` | **Yes** | Format: `YYYY-MM-DD` | End date of the exam. |

> [!IMPORTANT]
> **Custom Schema Validations:**
> * `startDate` and `endDate` must conform exactly to `YYYY-MM-DD` format.
> * `passMarks` cannot exceed `maxMarks`.
> * `startDate` cannot be later than `endDate`.

### `UpdateExamSchema`
Used when updating an existing exam. All fields are optional, enabling partial updates.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **examName** | `str` | No (Default: `None`) | Min length: 2<br>Max length: 100 | Updated name. |
| **classId** | `str` | No (Default: `None`) | Min length: 1 | Updated class ID. |
| **academicYear** | `str` | No (Default: `None`) | Min length: 4<br>Max length: 9 | Updated academic year. |
| **term** | `str` | No (Default: `None`) | Min length: 1<br>Max length: 50 | Updated term. |
| **maxMarks** | `int` | No (Default: `None`) | Value $\ge 1$ | Updated max marks. |
| **passMarks** | `int` | No (Default: `None`) | Value $\ge 0$ | Updated passing marks. |
| **startDate** | `str` | No (Default: `None`) | Format: `YYYY-MM-DD` | Updated start date. |
| **endDate** | `str` | No (Default: `None`) | Format: `YYYY-MM-DD` | Updated end date. |

> [!IMPORTANT]
> **Conditional Custom Validations:**
> * If `startDate` and/or `endDate` are provided, they must conform to `YYYY-MM-DD`.
> * If **both** `passMarks` and `maxMarks` are being updated, `passMarks` must be less than or equal to `maxMarks`.
> * If **both** `startDate` and `endDate` are being updated, `startDate` must be before or equal to `endDate`.

### `BulkSubjectMarkSchema`
Represents marks scored in a single subject.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **subjectId** | `str` | **Yes** | None | ID of the subject. |
| **marks** | `float` | **Yes** | Value $\ge 0$ | Marks scored. |

### `BulkStudentMarkSchema`
Represents bulk mark entry for a single student.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **studentId** | `str` | **Yes** | None | ID of the student. |
| **subjects** | `List[BulkSubjectMarkSchema]` | **Yes** | Min length: 1 item | List of subject marks for the student. |

### `BulkMarkEntrySchema`
Used when updating marks for multiple students in bulk.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **students** | `List[BulkStudentMarkSchema]` | **Yes** | Min length: 1 item | List of students and their marks. |

### `UpdateStudentMarksSchema`
Used to update marks of a single student for multiple subjects.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **subjects** | `List[BulkSubjectMarkSchema]` | **Yes** | Min length: 1 item | List of subject marks to update. |

---

## 8. Fees Models

Defined in [fees_model.py](file:///c:/Users/ElsonBenanzal/Desktop/sc-be/models/fees_model.py).

### `FeeItemSchema`
Represents an individual fee component (e.g. Tuition, Transport).

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **name** | `str` | **Yes** | Min length: 1 | Name of the fee item. |
| **amount** | `float` | **Yes** | Value $\ge 0$ | Amount for this item. |

### `CreateFeeStructureSchema`
Used to create a new fee structure.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **title** | `str` | **Yes** | Min length: 1 | Title of the fee structure. |
| **academicYear** | `str` | **Yes** | Min length: 1 | Academic year. |
| **classIds** | `List[str]` | **Yes** | Min length: 1 item | List of class IDs assigned. |
| **feeItems** | `List[FeeItemSchema]` | **Yes** | Min length: 1 item | List of fee items. |
| **dueDate** | `str` | **Yes** | Format: `YYYY-MM-DD` | Due date for the fees. |

### `UpdateFeeStructureSchema`
Used to update an existing fee structure.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **title** | `str` | **Yes** | Min length: 1 | Title. |
| **academicYear** | `str` | **Yes** | Min length: 1 | Academic year. |
| **classIds** | `List[str]` | **Yes** | Min length: 1 item | List of class IDs assigned. |
| **feeItems** | `List[FeeItemSchema]` | **Yes** | Min length: 1 item | List of fee items. |
| **dueDate** | `str` | **Yes** | Format: `YYYY-MM-DD` | Due date. |

### `RecordPaymentSchema`
Used to record a fee payment from a student.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **studentId** | `str` | **Yes** | Min length: 1 | Student ID. |
| **feeStructureId** | `str` | **Yes** | Min length: 1 | Fee structure ID. |
| **amount** | `float` | **Yes** | Value $> 0$ | Paid amount. |
| **paymentMode** | `str` | **Yes** | Min length: 1 | Mode of payment (e.g. Cash, Card). |
| **transactionId** | `str` | **Yes** | Min length: 1 | Unique transaction ID. |

### `SendReminderSchema`
Used to send a manual reminder to list of students.

| Field Name | Type | Required? | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| **studentIds** | `List[str]` | **Yes** | Min length: 1 item | Student IDs. |
| **message** | `str` | **Yes** | Min length: 1 | Reminder message content. |


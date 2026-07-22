# Digital Student Rank Card Management System API Documentation

This document describes all API endpoints, their expected request JSON bodies (payloads), headers, and full success/error response JSON structures.

---

## Global Response & Error Formats

### Standard Success Structure
Every API endpoint returns a standard JSON envelope:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}
```

### Standard Error Structure
Whenever a request fails (e.g. invalid credentials, validation error, permission denied), it returns:
```json
{
  "success": false,
  "message": "Description of the error"
}
```

---

## 1. Authentication Endpoints

### 1.1 User Login
* **URL**: `/api/auth/login`
* **Method**: `POST`
* **Headers**:
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "userId": "admin",
  "password": "Admin@123"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6...",
    "user": {
      "userId": "admin",
      "role": "SUPER_ADMIN"
    }
  }
}
```
> [!NOTE]
> For teachers, the `user` block is:
> `{"userId": "teacher1", "role": "TEACHER", "name": "John Doe", "teacherId": "teacher1", "department": "Science & Maths", "assignedClasses": ["6a4759faf045ac1652f4b2c8"]}`
> For students, the `user` block is:
> `{"userId": "student1", "role": "STUDENT", "name": "Alice Smith", "studentId": "student1", "classId": "6a4759faf045ac1652f4b2c8", "rollNumber": "101"}`

* **Error Response (401 Unauthorized)**:
```json
{
  "success": false,
  "message": "Invalid credentials."
}
```

---

### 1.2 User Logout
* **URL**: `/api/auth/logout`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Logout successful."
}
```

---

### 1.3 Change Password
* **URL**: `/api/auth/change-password`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "oldPassword": "CurrentPassword123",
  "newPassword": "NewPassword123"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Password updated successfully."
}
```

---

## 2. Super Admin Endpoints (Requires `SUPER_ADMIN` authorization)

### 2.1 Create Teacher Account
* **URL**: `/api/admin/create-teacher`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "userId": "teacher1",
  "password": "Password@123",
  "name": "John Doe",
  "department": "Science & Maths",
  "teacherId": "teacher1"
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Teacher account created successfully.",
  "data": {
    "teacherId": "teacher1",
    "userId": "teacher1",
    "name": "John Doe",
    "department": "Science & Maths",
    "assignedClasses": []
  }
}
```

---

### 2.2 Create Student Account
* **URL**: `/api/admin/create-student`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "userId": "student1",
  "password": "Password@123",
  "name": "Alice Smith",
  "classId": "6a4759faf045ac1652f4b2c8",
  "rollNumber": "101",
  "studentId": "student1"
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Student account created successfully.",
  "data": {
    "studentId": "student1",
    "userId": "student1",
    "name": "Alice Smith",
    "classId": "6a4759faf045ac1652f4b2c8",
    "rollNumber": "101"
  }
}
```

---

### 2.3 Get All Teachers
* **URL**: `/api/admin/teachers`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759faf045ac1652f4b2cc",
      "teacherId": "teacher1",
      "userId": "teacher1",
      "name": "John Doe",
      "department": "Science & Maths",
      "assignedClasses": ["6a4759faf045ac1652f4b2c8"]
    }
  ]
}
```

---

### 2.4 Get All Students
* **URL**: `/api/admin/students`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759fbf045ac1652f4b2ce",
      "studentId": "student1",
      "userId": "student1",
      "name": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "rollNumber": "101"
    }
  ]
}
```

---

### 2.5 Reset Password
* **URL**: `/api/admin/reset-password/<userId>`
* **Method**: `PUT`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "newPassword": "NewPassword123"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Password for user 'teacher1' reset successfully."
}
```

---

### 2.6 Activate / Deactivate User Account
* **URL**: `/api/admin/set-status/<userId>`
* **Method**: `PUT`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "active": false
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "User 'teacher1' has been deactivated successfully."
}
```

---

### 2.7 Create Class
* **URL**: `/api/admin/create-class`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "className": "Class 10",
  "section": "A",
  "classTeacher": "teacher1"
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Class created successfully.",
  "data": {
    "_id": "6a4759faf045ac1652f4b2c8",
    "className": "Class 10",
    "section": "A",
    "classTeacher": "teacher1"
  }
}
```

---

### 2.8 Create Subject
* **URL**: `/api/admin/create-subject`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "subjectName": "Mathematics"
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Subject created successfully.",
  "data": {
    "_id": "6a4759faf045ac1652f4b2c9",
    "subjectName": "Mathematics"
  }
}
```

---

### 2.9 Assign Teacher to Class
* **URL**: `/api/admin/assign-teacher`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "teacherId": "teacher1",
  "classId": "6a4759faf045ac1652f4b2c8"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Teacher 'teacher1' successfully assigned to class '6a4759faf045ac1652f4b2c8'."
}
```

---

## 3. Teacher Endpoints (Requires `TEACHER` authorization)

### 3.1 Get Assigned Classes
* **URL**: `/api/teacher/classes`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759faf045ac1652f4b2c8",
      "className": "Class 10",
      "section": "A",
      "classTeacher": "teacher1"
    }
  ]
}
```

---

### 3.2 Get Students in Class
* **URL**: `/api/teacher/students/<classId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759fbf045ac1652f4b2ce",
      "studentId": "student1",
      "userId": "student1",
      "name": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "rollNumber": "101"
    }
  ]
}
```

---

### 3.3 Enter Student Marks
* **URL**: `/api/marks`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "studentId": "student1",
  "classId": "6a4759faf045ac1652f4b2c8",
  "subjectId": "6a4759faf045ac1652f4b2c9",
  "exam": "Final",
  "marks": 95,
  "academicYear": "2026"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Marks entered successfully."
}
```

---

### 3.4 Edit Student Marks
* **URL**: `/api/marks/<markId>`
* **Method**: `PUT`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "marks": 98
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Marks updated successfully."
}
```

---

### 3.5 Publish Marks
* **URL**: `/api/marks/publish`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "classId": "6a4759faf045ac1652f4b2c8",
  "exam": "Final",
  "academicYear": "2026"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Marks published and rankings computed successfully."
}
```

---

### 3.6 Get Class Rankings
* **URL**: `/api/teacher/rankings/<classId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters**:
  * `exam` (Required string, e.g. `Final`)
  * `academicYear` (Required string, e.g. `2026`)
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759fcefca6c33cc1b724f",
      "studentId": "student1",
      "name": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "exam": "Final",
      "academicYear": "2026",
      "totalMarks": 180.0,
      "percentage": 90.0,
      "grade": "A+",
      "passed": true,
      "rank": 1,
      "publishedAt": "2026-07-03T06:43:08.236000",
      "subjectMarks": [
        {
          "subjectId": "6a4759faf045ac1652f4b2c9",
          "subjectName": "Mathematics",
          "marks": 95.0,
          "teacherId": "teacher1"
        },
        {
          "subjectId": "6a4759faf045ac1652f4b2ca",
          "subjectName": "Science",
          "marks": 85.0,
          "teacherId": "teacher1"
        }
      ]
    }
  ]
}
```

---

## 4. Student Endpoints (Requires `STUDENT` authorization)

### 4.1 Get Profile Detail
* **URL**: `/api/student/profile`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "studentId": "student1",
    "userId": "student1",
    "name": "Alice Smith",
    "rollNumber": "101",
    "classId": "6a4759faf045ac1652f4b2c8",
    "class": {
      "className": "Class 10",
      "section": "A"
    }
  }
}
```

---

### 4.2 Get Student Marks
* **URL**: `/api/student/marks`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters** (Optional):
  * `exam` (string, e.g. `Final`)
  * `academicYear` (string, e.g. `2026`)
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759fcefca6c33cc1b724d",
      "studentId": "student1",
      "classId": "6a4759faf045ac1652f4b2c8",
      "subjectId": "6a4759faf045ac1652f4b2c9",
      "teacherId": "teacher1",
      "exam": "Final",
      "marks": 95.0,
      "academicYear": "2026",
      "createdAt": "2026-07-03T06:43:08.179000",
      "updatedAt": "2026-07-03T06:43:08.179000"
    }
  ]
}
```

---

### 4.3 Get Student Report Card
* **URL**: `/api/student/report-card`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters** (Optional):
  * `exam` (string, e.g. `Final`)
  * `academicYear` (string, e.g. `2026`)
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759fcefca6c33cc1b724f",
      "studentId": "student1",
      "name": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "exam": "Final",
      "academicYear": "2026",
      "totalMarks": 180.0,
      "percentage": 90.0,
      "grade": "A+",
      "passed": true,
      "rank": 1,
      "publishedAt": "2026-07-03T06:43:08.236000",
      "subjectMarks": [
        {
          "subjectId": "6a4759faf045ac1652f4b2c9",
          "subjectName": "Mathematics",
          "marks": 95.0,
          "teacherId": "teacher1"
        },
        {
          "subjectId": "6a4759faf045ac1652f4b2ca",
          "subjectName": "Science",
          "marks": 85.0,
          "teacherId": "teacher1"
        }
      ]
    }
  ]
}
```

---

### 4.4 Get Student Rank & Grade Overall Status
* **URL**: `/api/student/rank`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters** (Optional):
  * `exam` (string, e.g. `Final`)
  * `academicYear` (string, e.g. `2026`)
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "exam": "Final",
      "academicYear": "2026",
      "rank": 1,
      "totalMarks": 180.0,
      "percentage": 90.0,
      "grade": "A+",
      "passed": true
    }
  ]
}
```

---

## 5. Metadata Endpoints (Requires standard JWT login)

### 5.1 Get All Classes List
* **URL**: `/api/classes`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759faf045ac1652f4b2c8",
      "className": "Class 10",
      "section": "A",
      "classTeacher": "teacher1"
    }
  ]
}
```

---

### 5.2 Get All Subjects List
* **URL**: `/api/subjects`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a4759faf045ac1652f4b2c9",
      "subjectName": "Mathematics"
    }
  ]
}
```

---

## 6. Exam Management & Extensions (Phase 3)

### 6.1 Create Exam
* **URL**: `/api/exams`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "examId": "EXM_TEST_V2",
  "examName": "Final Term 11",
  "classId": "6a4773f94fd0b9c4a4b38a26",
  "academicYear": "2026",
  "term": "Term 2",
  "maxMarks": 100,
  "passMarks": 35,
  "startDate": "2026-11-01",
  "endDate": "2026-11-10"
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Exam created successfully.",
  "data": {
    "examId": "EXM_TEST_V2",
    "examName": "Final Term 11",
    "classId": "6a4773f94fd0b9c4a4b38a26",
    "academicYear": "2026",
    "term": "Term 2",
    "maxMarks": 100,
    "passMarks": 35,
    "startDate": "2026-11-01",
    "endDate": "2026-11-10",
    "status": "DRAFT",
    "createdBy": "teacher2",
    "createdAt": "2026-07-03T09:05:16.965864+00:00",
    "updatedAt": "2026-07-03T09:05:16.965864+00:00"
  }
}
```

---

### 6.2 Get Exams List
* **URL**: `/api/exams`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  "message": "Operation completed successfully.",
  "data": [
    {
      "examId": "EXM_TEST_001",
      "examName": "Mid Term 11",
      "classId": "6a4773f94fd0b9c4a4b38a26",
      "academicYear": "2026",
      "term": "Term 1",
      "maxMarks": 100,
      "passMarks": 40,
      "status": "DRAFT",
      "createdBy": "teacher2"
    }
  ]
}
```
*(Note: Teachers only retrieve exams they created; Admins retrieve all exams).*

---

### 6.3 Get Exam Details
* **URL**: `/api/exams/<examId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "examId": "EXM_TEST_001",
    "examName": "Mid Term 11",
    "classId": "6a4773f94fd0b9c4a4b38a26",
    "academicYear": "2026",
    "term": "Term 1",
    "maxMarks": 100,
    "passMarks": 40,
    "status": "DRAFT",
    "createdBy": "teacher2"
  }
}
```

---

### 6.4 Update Exam Properties
* **URL**: `/api/exams/<examId>`
* **Method**: `PUT`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "examName": "Updated Exam Name",
  "passMarks": 45
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam updated successfully.",
  "data": {
    "examId": "EXM_TEST_001",
    "examName": "Updated Exam Name",
    "classId": "6a4773f94fd0b9c4a4b38a26",
    "academicYear": "2026",
    "term": "Term 1",
    "maxMarks": 100,
    "passMarks": 45,
    "status": "DRAFT",
    "createdBy": "teacher2"
  }
}
```

---

### 6.5 Delete Exam
* **URL**: `/api/exams/<examId>`
* **Method**: `DELETE`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam and its associated marks/report cards deleted successfully."
}
```

---

### 6.6 Bulk Save Marks
* **URL**: `/api/exams/<examId>/marks/bulk`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "students": [
    {
      "studentId": "student3",
      "subjects": [
        {"subjectId": "6a4773f94fd0b9c4a4b38a27", "marks": 90},
        {"subjectId": "6a4773f94fd0b9c4a4b38a28", "marks": 80}
      ]
    },
    {
      "studentId": "student4",
      "subjects": [
        {"subjectId": "6a4773f94fd0b9c4a4b38a27", "marks": 90}
      ]
    }
  ]
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Marks saved successfully."
}
```

---

### 6.7 Get Mark Entry Spreadsheet Data
* **URL**: `/api/exams/<examId>/marksheet`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Marksheet sheet retrieved successfully.",
  "data": {
    "exam": {
      "examId": "EXM_TEST_001",
      "examName": "Mid Term 11",
      "classId": "6a4773f94fd0b9c4a4b38a26",
      "status": "DRAFT",
      "maxMarks": 100,
      "passMarks": 40
    },
    "classDetails": {
      "_id": "6a4773f94fd0b9c4a4b38a26",
      "className": "Class 11",
      "section": "B"
    },
    "subjects": [
      {
        "_id": "6a4773f94fd0b9c4a4b38a27",
        "subjectName": "Maths 11"
      }
    ],
    "students": [
      {
        "studentId": "student3",
        "name": "Charlie Brown",
        "rollNumber": "201"
      }
    ],
    "existingMarks": [
      {
        "studentId": "student3",
        "subjectId": "6a4773f94fd0b9c4a4b38a27",
        "marks": 90.0,
        "teacherId": "teacher2"
      }
    ]
  }
}
```

---

### 6.8 Publish Exam (Calculate Dense Ranks)
* **URL**: `/api/exams/<examId>/publish`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam published and rankings computed successfully."
}
```

---

### 6.9 Unlock Published Exam (Super Admin Only)
* **URL**: `/api/exams/<examId>/unlock`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam unlocked and status reset to DRAFT successfully."
}
```

---

### 6.10 Get Exam Statistics
* **URL**: `/api/exams/<examId>/statistics`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**: `None`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Statistics retrieved successfully.",
  "data": {
    "highestMark": 170.0,
    "lowestMark": 160.0,
    "average": 166.67,
    "passPercentage": 0.0,
    "failPercentage": 100.0,
    "gradeDistribution": {
      "A+": 0,
      "A": 0,
      "B": 0,
      "C": 0,
      "D": 0,
      "E": 0,
      "F": 3
    },
    "topStudents": [
      {
        "studentId": "student3",
        "name": "Charlie Brown",
        "totalMarks": 170.0,
        "rank": 1
      },
      {
        "studentId": "student4",
        "name": "Diana Prince",
        "totalMarks": 170.0,
        "rank": 1
      },
      {
        "studentId": "student5",
        "name": "Ethan Hunt",
        "totalMarks": 160.0,
        "rank": 2
      }
    ],
    "subjectWiseAverage": [
      {
        "subjectId": "6a4773f94fd0b9c4a4b38a27",
        "subjectName": "Maths 11",
        "average": 88.33
      },
      {
        "subjectId": "6a4773f94fd0b9c4a4b38a28",
        "subjectName": "Science 11",
        "average": 78.33
      }
    ]
  }
}
```

---

## 7. Discussion & Support Module Endpoints

### 7.1 Student: Create Discussion
* **URL**: `/api/discussions`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "title": "Need help in Mathematics",
  "category": "ACADEMIC",
  "priority": "MEDIUM",
  "message": "I have a doubt regarding Algebra Chapter 4."
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Discussion created successfully.",
  "data": {}
}
```

---

### 7.2 Student: Get My Discussions
* **URL**: `/api/student/discussions`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters** (Optional):
  * `status`: Filter by status (e.g. `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`)
  * `priority`: Filter by priority (e.g. `LOW`, `MEDIUM`, `HIGH`)
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a587bc8efca6c33cc1b7280",
      "discussionId": "DISC001",
      "studentId": "student1",
      "studentName": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "teacherId": "teacher1",
      "title": "Need help in Mathematics",
      "category": "ACADEMIC",
      "priority": "MEDIUM",
      "status": "OPEN",
      "createdAt": "2026-07-16T12:05:54.120000",
      "updatedAt": "2026-07-16T12:05:54.120000",
      "lastMessageAt": "2026-07-16T12:05:54.120000",
      "lastMessageBy": "student"
    }
  ]
}
```

---

### 7.3 Student: Get Discussion Details
* **URL**: `/api/discussions/<discussionId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "discussion": {
      "_id": "6a587bc8efca6c33cc1b7280",
      "discussionId": "DISC001",
      "studentId": "student1",
      "studentName": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "teacherId": "teacher1",
      "title": "Need help in Mathematics",
      "category": "ACADEMIC",
      "priority": "MEDIUM",
      "status": "OPEN",
      "createdAt": "2026-07-16T12:05:54.120000",
      "updatedAt": "2026-07-16T12:05:54.120000",
      "lastMessageAt": "2026-07-16T12:05:54.120000",
      "lastMessageBy": "student"
    },
    "messages": [
      {
        "_id": "6a587bc8efca6c33cc1b7281",
        "discussionId": "DISC001",
        "senderId": "student1",
        "senderRole": "STUDENT",
        "message": "I have a doubt regarding Algebra Chapter 4.",
        "attachments": [],
        "createdAt": "2026-07-16T12:05:54.120000",
        "isEdited": false,
        "editedAt": null
      }
    ]
  }
}
```

---

### 7.4 Student: Send Reply
* **URL**: `/api/discussions/<discussionId>/reply`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "message": "Thank you sir."
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Reply sent successfully.",
  "data": {}
}
```

---

### 7.5 Student: Delete Discussion
* **URL**: `/api/discussions/<discussionId>`
* **Method**: `DELETE`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Discussion deleted successfully.",
  "data": {}
}
```
> [!IMPORTANT]
> Deletion is only allowed if the discussion status is `OPEN` and it has no teacher or admin replies.

---

### 7.6 Teacher: Get Assigned Discussions
* **URL**: `/api/teacher/discussions`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters** (Optional):
  * `classId`: Filter by class grade/section ID
  * `status`: Filter by status
  * `category`: Filter by category
  * `priority`: Filter by priority
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a587bc8efca6c33cc1b7280",
      "discussionId": "DISC001",
      "studentId": "student1",
      "studentName": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "teacherId": "teacher1",
      "title": "Need help in Mathematics",
      "category": "ACADEMIC",
      "priority": "MEDIUM",
      "status": "OPEN",
      "createdAt": "2026-07-16T12:05:54.120000",
      "updatedAt": "2026-07-16T12:05:54.120000",
      "lastMessageAt": "2026-07-16T12:05:54.120000",
      "lastMessageBy": "student"
    }
  ]
}
```

---

### 7.7 Teacher: Get Discussion Details
* **URL**: `/api/teacher/discussions/<discussionId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "discussion": {
      "_id": "6a587bc8efca6c33cc1b7280",
      "discussionId": "DISC001",
      "studentId": "student1",
      "studentName": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "teacherId": "teacher1",
      "title": "Need help in Mathematics",
      "category": "ACADEMIC",
      "priority": "MEDIUM",
      "status": "OPEN",
      "createdAt": "2026-07-16T12:05:54.120000"
    },
    "messages": [
      {
        "_id": "6a587bc8efca6c33cc1b7281",
        "discussionId": "DISC001",
        "senderId": "student1",
        "senderRole": "STUDENT",
        "message": "I have a doubt regarding Algebra Chapter 4.",
        "createdAt": "2026-07-16T12:05:54.120000"
      }
    ]
  }
}
```

---

### 7.8 Teacher: Reply to Discussion
* **URL**: `/api/teacher/discussions/<discussionId>/reply`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "message": "Please refer to page 35 in your Mathematics textbook."
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Reply sent successfully.",
  "data": {}
}
```

---

### 7.9 Teacher: Change Status
* **URL**: `/api/teacher/discussions/<discussionId>/status`
* **Method**: `PUT`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "status": "RESOLVED"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Status updated successfully.",
  "data": {}
}
```
> [!WARNING]
> Teachers can update discussion status to `OPEN`, `IN_PROGRESS`, or `RESOLVED`. Setting the status to `CLOSED` is restricted to Super Admins.

---

### 7.10 Super Admin: Get All Discussions
* **URL**: `/api/admin/discussions`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters** (Optional):
  * `School`, `Class`, `Teacher`, `Student`, `Status`, `Category`, `Priority`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a587bc8efca6c33cc1b7280",
      "discussionId": "DISC001",
      "studentId": "student1",
      "studentName": "Alice Smith",
      "classId": "6a4759faf045ac1652f4b2c8",
      "teacherId": "teacher1",
      "title": "Need help in Mathematics",
      "category": "ACADEMIC",
      "priority": "MEDIUM",
      "status": "RESOLVED",
      "createdAt": "2026-07-16T12:05:54.120000"
    }
  ]
}
```

---

### 7.11 Super Admin: View Discussion
* **URL**: `/api/admin/discussions/<discussionId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "discussion": {
      "discussionId": "DISC001",
      "studentId": "student1",
      "title": "Need help in Mathematics",
      "status": "RESOLVED"
    },
    "messages": [
      {
        "senderId": "student1",
        "message": "I have a doubt regarding Algebra Chapter 4."
      }
    ]
  }
}
```

---

### 7.12 Super Admin: Reply to Discussion
* **URL**: `/api/admin/discussions/<discussionId>/reply`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "message": "Administrator reply content."
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Reply sent successfully.",
  "data": {}
}
```

---

### 7.13 Super Admin: Close Discussion
* **URL**: `/api/admin/discussions/<discussionId>/status`
* **Method**: `PUT`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "status": "CLOSED"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Status updated successfully.",
  "data": {}
}
```

---

### 7.14 Super Admin: Delete Discussion
* **URL**: `/api/admin/discussions/<discussionId>`
* **Method**: `DELETE`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Discussion deleted successfully.",
  "data": {}
}
```

---

### 7.15 Common: Discussion Statistics
* **URL**: `/api/discussions/statistics`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Discussion statistics retrieved successfully.",
  "data": {
    "totalDiscussions": 120,
    "open": 18,
    "inProgress": 20,
    "resolved": 72,
    "closed": 10,
    "highPriority": 6
  }
}
```

---

## 8. Fees Management Endpoints

### 8.1 Super Admin: Create Fee Structure
* **URL**: `/api/admin/fees`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "title": "Term 1 Fees",
  "academicYear": "2026-2027",
  "classIds": ["CLASS10A"],
  "feeItems": [
    {
      "name": "Tuition Fee",
      "amount": 20000
    },
    {
      "name": "Transport Fee",
      "amount": 3000
    }
  ],
  "dueDate": "2026-09-15"
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Fee structure created and assigned successfully.",
  "data": {
    "_id": "6a58ce48273723da28fd8895",
    "feeStructureId": "FEE001",
    "title": "Term 1 Fees",
    "academicYear": "2026-2027",
    "classIds": ["CLASS10A"],
    "feeItems": [
      {
        "name": "Tuition Fee",
        "amount": 20000.0
      },
      {
        "name": "Transport Fee",
        "amount": 3000.0
      }
    ],
    "totalAmount": 23000.0,
    "dueDate": "2026-09-15",
    "status": "ACTIVE",
    "createdBy": "admin",
    "createdAt": "2026-07-16T17:53:30.123456",
    "updatedAt": "2026-07-16T17:53:30.123456"
  }
}
```

---

### 8.2 Super Admin: Get Fee Structures
* **URL**: `/api/admin/fees`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters**:
  * `academicYear` (optional)
  * `classId` / `class` (optional)
  * `status` (optional)
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "feeStructureId": "FEE001",
      "title": "Term 1 Fees",
      "academicYear": "2026-2027",
      "classIds": ["CLASS10A"],
      "totalAmount": 23000.0,
      "dueDate": "2026-09-15",
      "status": "ACTIVE"
    }
  ]
}
```

---

### 8.3 Super Admin: Get Fee Structure
* **URL**: `/api/admin/fees/<feeStructureId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "feeStructureId": "FEE001",
    "title": "Term 1 Fees",
    "academicYear": "2026-2027",
    "classIds": ["CLASS10A"],
    "feeItems": [
      {
        "name": "Tuition Fee",
        "amount": 20000.0
      }
    ],
    "totalAmount": 20000.0,
    "dueDate": "2026-09-15",
    "status": "ACTIVE"
  }
}
```

---

### 8.4 Super Admin: Update Fee Structure
* **URL**: `/api/admin/fees/<feeStructureId>`
* **Method**: `PUT`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "title": "Term 1 Fees Updated",
  "academicYear": "2026-2027",
  "classIds": ["CLASS10A"],
  "feeItems": [
    {
      "name": "Tuition Fee",
      "amount": 22000.0
    }
  ],
  "dueDate": "2026-09-20"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Fee structure updated and assignments synchronized successfully.",
  "data": {
    "feeStructureId": "FEE001",
    "title": "Term 1 Fees Updated",
    "totalAmount": 22000.0,
    "dueDate": "2026-09-20"
  }
}
```

---

### 8.5 Super Admin: Delete Fee Structure
* **URL**: `/api/admin/fees/<feeStructureId>`
* **Method**: `DELETE`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Fee structure and assignments deleted successfully."
}
```

---

### 8.6 Super Admin: Fee Dashboard
* **URL**: `/api/admin/fees/dashboard`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "totalFees": 1500000.0,
    "collected": 900000.0,
    "pending": 600000.0,
    "paidStudents": 250,
    "pendingStudents": 120,
    "overdueStudents": 40
  }
}
```

---

### 8.7 Super Admin: Student Fee List
* **URL**: `/api/admin/fees/students`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters**:
  * `classId` / `class` (optional)
  * `status` (optional)
  * `studentName` / `name` (optional)
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "studentId": "student1",
      "studentName": "Alice Smith",
      "classId": "CLASS10A",
      "feeStructureId": "FEE001",
      "feeStructureTitle": "Term 1 Fees",
      "academicYear": "2026-2027",
      "totalAmount": 24000.0,
      "paidAmount": 12000.0,
      "pendingAmount": 12000.0,
      "status": "PARTIALLY_PAID",
      "lastReminderAt": null
    }
  ]
}
```

---

### 8.8 Super Admin: Send Fee Reminder
* **URL**: `/api/admin/fees/reminder`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "studentIds": ["student1", "student2"],
  "message": "Please pay your Term 1 fees before the due date."
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Fee reminders sent successfully."
}
```

---

### 8.9 Super Admin: Record Fee Payment
* **URL**: `/api/admin/fees/payment`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
  * `Content-Type: application/json`
* **Request Body**:
```json
{
  "studentId": "student1",
  "feeStructureId": "FEE001",
  "amount": 12000.0,
  "paymentMode": "Cash",
  "transactionId": "TXN123456"
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Payment recorded successfully.",
  "data": {
    "paymentId": "PAY001",
    "studentId": "student1",
    "feeStructureId": "FEE001",
    "amount": 12000.0,
    "paymentMode": "Cash",
    "transactionId": "TXN123456",
    "paidOn": "2026-07-16T17:56:13.123456",
    "receivedBy": "admin"
  }
}
```

---

### 8.10 Super Admin: Payment History
* **URL**: `/api/admin/fees/payments`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters**:
  * `studentId` / `student` (optional)
  * `classId` / `class` (optional)
  * `date` (optional, YYYY-MM-DD)
  * `paymentMode` (optional)
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "paymentId": "PAY001",
      "studentId": "student1",
      "studentName": "Alice Smith",
      "classId": "CLASS10A",
      "feeStructureId": "FEE001",
      "feeStructureTitle": "Term 1 Fees",
      "amount": 12000.0,
      "paymentMode": "Cash",
      "transactionId": "TXN123456",
      "paidOn": "2026-07-16T17:56:13.123456",
      "receivedBy": "admin"
    }
  ]
}
```

---

### 8.11 Teacher: Fee Overview
* **URL**: `/api/teacher/fees`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Query Parameters**:
  * `search` (optional, searches student name)
  * `status` (optional, filters by status, e.g. "PENDING")
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "studentId": "student1",
      "studentName": "Alice Smith",
      "feeStructureTitle": "Term 1 Fees",
      "totalAmount": 24000.0,
      "paidAmount": 12000.0,
      "pendingAmount": 12000.0,
      "status": "PARTIALLY_PAID"
    }
  ]
}
```

---

### 8.12 Teacher: Student Fee Details
* **URL**: `/api/teacher/fees/<studentId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "studentId": "student1",
      "studentName": "Alice Smith",
      "feeStructureTitle": "Term 1 Fees",
      "dueDate": "2026-09-15",
      "feeItems": [
        {"name": "Tuition Fee", "amount": 20000.0}
      ],
      "totalAmount": 24000.0,
      "paidAmount": 12000.0,
      "pendingAmount": 12000.0,
      "status": "PARTIALLY_PAID"
    }
  ]
}
```

---

### 8.13 Student: My Fees
* **URL**: `/api/student/fees`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "feeStructureId": "FEE001",
      "title": "Term 1 Fees",
      "dueDate": "2026-09-15",
      "feeItems": [
        {"name": "Tuition Fee", "amount": 20000.0}
      ],
      "totalAmount": 24000.0,
      "paidAmount": 12000.0,
      "pendingAmount": 12000.0,
      "status": "PARTIALLY_PAID"
    }
  ]
}
```

---

### 8.14 Student: Payment History
* **URL**: `/api/student/fees/payments`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "paymentId": "PAY001",
      "feeStructureTitle": "Term 1 Fees",
      "amount": 12000.0,
      "paymentMode": "Cash",
      "transactionId": "TXN123456",
      "paidOn": "2026-07-16T17:56:13.123456"
    }
  ]
}
```

---

### 8.15 Student: Notifications
* **URL**: `/api/student/fees/notifications`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "_id": "6a58ce48273723da28fd8899",
      "studentId": "student1",
      "title": "Fee Reminder",
      "message": "Please pay your Term 1 fees before the due date.",
      "isRead": false,
      "type": "FEE_REMINDER",
      "createdAt": "2026-07-16T17:57:00.123456"
    }
  ]
}
```

---

## 9. Online Examination Module

### 9.1 Super Admin: Create Online Exam
* **URL**: `/api/admin/exams`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**:
```json
{
  "title": "Mathematics Online Test",
  "subjectId": "SUB001",
  "classIds": ["CLASS10A"],
  "academicYear": "2026-2027",
  "duration": 60,
  "passingMarks": 20,
  "startDateTime": "2026-09-10T09:00:00Z",
  "endDateTime": "2026-09-10T10:00:00Z",
  "instructions": "Answer all questions.",
  "questions": [
    {
      "question": "What is 15 x 5?",
      "type": "MCQ",
      "options": ["55", "65", "75", "85"],
      "correctAnswer": "75",
      "marks": 5,
      "negativeMarks": 0,
      "explanation": "15 times 5 is 75."
    }
  ]
}
```
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Online exam created successfully.",
  "data": {
    "examId": "EXM1721461234",
    "title": "Mathematics Online Test",
    "subjectId": "SUB001",
    "classIds": ["CLASS10A"],
    "academicYear": "2026-2027",
    "duration": 60,
    "totalMarks": 5,
    "passingMarks": 20,
    "startDateTime": "2026-09-10T09:00:00Z",
    "endDateTime": "2026-09-10T10:00:00Z",
    "instructions": "Answer all questions.",
    "status": "DRAFT",
    "createdBy": "admin",
    "createdAt": "...",
    "updatedAt": "...",
    "questions": [
      {
        "questionId": "Q001",
        "examId": "EXM1721461234",
        "question": "What is 15 x 5?",
        "type": "MCQ",
        "options": ["55", "65", "75", "85"],
        "correctAnswer": "75",
        "marks": 5,
        "negativeMarks": 0,
        "explanation": "15 times 5 is 75.",
        "order": 1
      }
    ]
  }
}
```

---

### 9.2 Super Admin: Update Online Exam
* **URL**: `/api/admin/exams/<examId>`
* **Method**: `PUT`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**:
```json
{
  "title": "Updated Mathematics Online Test",
  "instructions": "Attempt carefully."
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam updated successfully.",
  "data": {
    "examId": "EXM1721461234",
    "title": "Updated Mathematics Online Test",
    "instructions": "Attempt carefully."
  }
}
```

---

### 9.3 Super Admin: Delete Online Exam
* **URL**: `/api/admin/exams/<examId>`
* **Method**: `DELETE`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam deleted successfully."
}
```

---

### 9.4 Super Admin: Publish Online Exam
* **URL**: `/api/admin/exams/<examId>/publish`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam published successfully and notifications dispatched."
}
```

---

### 9.5 Super Admin: Close Online Exam
* **URL**: `/api/admin/exams/<examId>/close`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam closed successfully and active attempts auto-submitted."
}
```

---

### 9.6 Super Admin: Get Online Exams
* **URL**: `/api/admin/exams`
* **Method**: `GET`
* **Query Parameters**:
  * `classId`: Filter by class ID
  * `subjectId`: Filter by subject ID
  * `academicYear`: Filter by academic year
  * `status`: Filter by status
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": []
}
```

---

### 9.7 Super Admin: Publish Results
* **URL**: `/api/admin/exams/<examId>/publish-results`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam results published successfully and notifications dispatched."
}
```

---

### 9.8 Teacher: View Assigned Exams
* **URL**: `/api/teacher/exams`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": []
}
```

---

### 9.9 Teacher: Live Monitoring
* **URL**: `/api/teacher/exams/<examId>/live`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "studentsStarted": 5,
    "studentsSubmitted": 3,
    "studentsPending": 2,
    "activeCount": 2
  }
}
```

---

### 9.10 Teacher: View Student Attempts
* **URL**: `/api/teacher/exams/<examId>/attempts`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "attemptId": "ATT1721461234",
      "examId": "EXM1721461234",
      "studentId": "student_test",
      "startedAt": "...",
      "submittedAt": "...",
      "status": "SUBMITTED",
      "timeTaken": 45,
      "student": {
        "studentId": "student_test",
        "name": "Alice Smith",
        "rollNumber": "101",
        "classId": "CLASS10A"
      }
    }
  ]
}
```

---

### 9.11 Student: My Exams
* **URL**: `/api/student/exams`
* **Method**: `GET`
* **Query Parameters**:
  * `academicYear`: Filter by academic year
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": []
}
```

---

### 9.12 Student: Start Exam
* **URL**: `/api/student/exams/<examId>/start`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (201 Created)**:
```json
{
  "success": true,
  "message": "Exam attempt started successfully.",
  "data": {
    "attemptId": "ATT1721461234",
    "examId": "EXM1721461234",
    "studentId": "student_test",
    "startedAt": "...",
    "submittedAt": null,
    "status": "IN_PROGRESS",
    "timeTaken": 0
  }
}
```

---

### 9.13 Student: Get Exam Questions
* **URL**: `/api/student/exams/<examId>`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": [
    {
      "questionId": "Q001",
      "examId": "EXM1721461234",
      "question": "What is 15 x 5?",
      "type": "MCQ",
      "options": ["55", "65", "75", "85"],
      "order": 1
    }
  ]
}
```

---

### 9.14 Student: Auto Save Answer
* **URL**: `/api/student/exams/<examId>/save-answer`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Request Body**:
```json
{
  "questionId": "Q001",
  "selectedAnswer": "75"
}
```
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Answer saved successfully."
}
```

---

### 9.15 Student: Submit Exam
* **URL**: `/api/student/exams/<examId>/submit`
* **Method**: `POST`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Exam submitted and auto-evaluated successfully."
}
```

---

### 9.16 Student: View Result
* **URL**: `/api/student/exams/<examId>/result`
* **Method**: `GET`
* **Headers**:
  * `Authorization: Bearer <jwt_access_token>`
* **Success Response (200 OK - Results Published)**:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {
    "totalQuestions": 3,
    "correctAnswers": 2,
    "wrongAnswers": 1,
    "score": 15,
    "percentage": 75.0,
    "grade": "B",
    "passed": true,
    "review": [
      {
        "questionId": "Q001",
        "question": "What is 15 x 5?",
        "type": "MCQ",
        "options": ["55", "65", "75", "85"],
        "order": 1,
        "correctAnswer": "75",
        "studentAnswer": "75",
        "explanation": "15 times 5 is 75.",
        "marks": 5,
        "isCorrect": true,
        "marksAwarded": 5
      }
    ]
  }
}
```
* **Success Response (200 OK - Results Not Yet Published)**:
```json
{
  "success": true,
  "message": "Results have not been published yet.",
  "data": null
}
```



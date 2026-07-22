# Digital Student Rank Card Management System Backend API

This is a production-ready REST API backend built with **Python 3.12+**, **Flask**, and **MongoDB (PyMongo)**. It implements role-based access control (SUPER_ADMIN, TEACHER, STUDENT), JWT authorization, and an automatic class ranking and grading system.

## Tech Stack

- **Python 3.12+**
- **Flask** & Blueprints (Modular architecture)
- **PyMongo** (MongoDB Client driver)
- **Flask-JWT-Extended** (JWT Authentication & token blocklist check on logout)
- **bcrypt** (Password hashing)
- **python-dotenv** (Environment variable loading)
- **Flask-CORS** (Cross-origin Resource Sharing)
- **Pydantic** (Payload validation)

---

## Getting Started

### 1. Installation

Clone or verify the codebase, then install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the root directory (one is seeded automatically):

```env
MONGO_URI=mongodb://localhost:27017/student_rank_card_db
JWT_SECRET_KEY=super-secret-jwt-key-change-this-in-production
PORT=5000
FLASK_ENV=development

# Seed Super Admin
DEFAULT_ADMIN_USER_ID=admin
DEFAULT_ADMIN_PASSWORD=Admin@123
```

### 3. Run the Server

```bash
python app.py
```

The database seeder will automatically create the initial `SUPER_ADMIN` account matching the `DEFAULT_ADMIN_USER_ID` and `DEFAULT_ADMIN_PASSWORD` in your `.env` config.

---

## API Documentation

### Authentication

- `POST /api/auth/login` - Authenticate credentials and receive a JWT token.
- `POST /api/auth/logout` - Revokes access by blocklisting the JWT token.
- `POST /api/auth/change-password` - Allows the logged-in user to change their password.

### Super Admin Endpoints (Requires `SUPER_ADMIN` role)

- `POST /api/admin/create-teacher` - Create a teacher account.
- `POST /api/admin/create-student` - Create a student account.
- `GET /api/admin/teachers` - Fetch all teacher records.
- `GET /api/admin/students` - Fetch all student records.
- `PUT /api/admin/reset-password/<userId>` - Reset any user's password.
- `PUT /api/admin/set-status/<userId>` - Activate/deactivate accounts.
- `POST /api/admin/create-class` - Setup a class structure.
- `POST /api/admin/create-subject` - Define a system subject.
- `POST /api/admin/assign-teacher` - Assign a teacher to a class.

### Teacher Endpoints (Requires `TEACHER` role)

- `GET /api/teacher/classes` - View all classes assigned to the logged-in teacher.
- `GET /api/teacher/students/<classId>` - Fetch all students enrolled in an assigned class.
- `POST /api/marks` - Enter a student's marks for a subject and exam.
- `PUT /api/marks/<markId>` - Edit a marks entry.
- `POST /api/marks/publish` - Publish class marks. Generates report cards, grades, and rankings.
- `GET /api/teacher/rankings/<classId>` - View published student ranking list for a class.

### Student Endpoints (Requires `STUDENT` role)

- `GET /api/student/profile` - View profile info and class details.
- `GET /api/student/marks` - View marks history.
- `GET /api/student/report-card` - View published report cards.
- `GET /api/student/rank` - View published overall ranks and grade results.

---

## Ranking & Grading Business Logic

When a teacher calls `/api/marks/publish` for an exam:
1. The system aggregates all marks for each student in the specified class.
2. Percentage is calculated as: `(total_marks_scored / (total_subjects * 100)) * 100`.
3. Grades are computed using thresholds:
   - **A+** (>= 90%)
   - **A** (80% - 89.9%)
   - **B** (70% - 79.9%)
   - **C** (60% - 69.9%)
   - **D** (50% - 59.9%)
   - **E** (40% - 49.9%)
   - **F** (< 40%)
4. A student is marked **PASS** if their overall percentage is >= 40% **AND** they score >= 40 in every subject for that exam. Otherwise, they are marked **FAIL**.
5. Ranks are calculated dynamically using fractional/competition ranking (e.g. ties share a rank, next rank skips accordingly).
6. **Automatic Updates**: If a mark is updated after reports are published, the system automatically recalculates the ranks and report cards for the entire class to keep rankings consistent.

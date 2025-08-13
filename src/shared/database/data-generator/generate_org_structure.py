# generate_org_structure.py
import json
from faker import Faker
from pathlib import Path
import slugify

# --------------------------
# CONFIG: Fixed counts
# --------------------------
NUM_DEPARTMENTS = 3  # must not exceed length of DEPARTMENT_NAMES
COURSES_PER_DEPT = 3
SOCIETIES_PER_DEPT = 3
DEPT_ADMINS_PER_DEPT = 2
STAFF_ADMINS_PER_DEPT = 2
OFFICERS_PER_SOCIETY = 1
DOMAIN = "example.edu"

# --------------------------
# Static campus-style names
# --------------------------
DEPARTMENT_NAMES = [
    "Engineering Department",
    "Computing Department",
    "Literature Department",
    "Economics Department",
    "Physics Department"
]

COURSES_MAP = {
    "Engineering Department": ["Mechanical Engineering", "Civil Engineering", "Electrical Engineering"],
    "Computing Department": ["Computer Science", "Software Engineering", "Artificial Intelligence"],
    "Literature Department": ["English Literature", "Comparative Literature", "Creative Writing"],
    "Economics Department": ["Economics", "Business Administration", "International Trade"],
    "Physics Department": ["Physics", "Astrophysics", "Quantum Mechanics"]
}

SOCIETIES_MAP = {
    "Engineering Department": ["Robotics Society", "Engineering Without Borders", "Automotive Club"],
    "Computing Department": ["AI Society", "Cybersecurity Club", "Game Development Society"],
    "Literature Department": ["Creative Writing Society", "Poetry Club", "Book Lovers Society"],
    "Economics Department": ["Finance Society", "Entrepreneurship Club", "Debating Society"],
    "Physics Department": ["Astronomy Club", "Quantum Society", "Science Outreach Club"]
}

# --------------------------
# Setup Faker (deterministic)
# --------------------------
fake = Faker()
Faker.seed(42)

# --------------------------
# Data containers
# --------------------------
departments = []
courses = []
societies = []
users = []
uid_counter = 1


def make_email(name, suffix):
    return f"{slugify.slugify(name)}-{suffix}@{DOMAIN}"


def add_user(name, email, role_scope, scope_id, department_id):
    global uid_counter
    users.append({
        "id": uid_counter,
        "name": name,
        "email": email,
        "role_scope": role_scope,
        "scope_id": scope_id,        # dept_id if dept/staff, society_id if officer
        "department_id": department_id
    })
    uid_counter += 1


# --------------------------
# 1️. Generate Departments, Courses, Societies
# --------------------------
for dept_id in range(1, NUM_DEPARTMENTS + 1):
    dept_name = DEPARTMENT_NAMES[dept_id - 1]
    dept_email = make_email(dept_name, "dept")
    departments.append({
        "id": dept_id,
        "name": dept_name,
        "email": dept_email
    })

    # Courses
    for course_name in COURSES_MAP[dept_name][:COURSES_PER_DEPT]:
        course_id = len(courses) + 1
        course_email = make_email(course_name, "course")
        courses.append({
            "id": course_id,
            "department_id": dept_id,
            "name": course_name,
            "email": course_email
        })

    # Societies
    for soc_name in SOCIETIES_MAP[dept_name][:SOCIETIES_PER_DEPT]:
        soc_id = len(societies) + 1
        soc_email = make_email(soc_name, "soc")
        societies.append({
            "id": soc_id,
            "department_id": dept_id,
            "name": soc_name,
            "email": soc_email
        })


# --------------------------
# 2️. Generate Admin Users
# --------------------------
for dept in departments:
    # Dept admins
    for _ in range(DEPT_ADMINS_PER_DEPT):
        add_user(fake.name(), fake.email(), "department", dept["id"], dept["id"])
    # Staff admins
    for _ in range(STAFF_ADMINS_PER_DEPT):
        add_user(fake.name(), fake.email(), "staff", dept["id"], dept["id"])

for soc in societies:
    dept_id = soc["department_id"]
    for _ in range(OFFICERS_PER_SOCIETY):
        add_user(fake.name(), fake.email(), "society_officer", soc["id"], dept_id)


# --------------------------
# 3️. Export to JSON
# --------------------------
data = {
    "departments": departments,
    "courses": courses,
    "societies": societies,
    "users": users
}

output_file = Path("org_structure.json")
with output_file.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Generated {output_file} with:")
print(f"- {len(departments)} departments")
print(f"- {len(courses)} courses")
print(f"- {len(societies)} societies")
print(f"- {len(users)} users (admins)")


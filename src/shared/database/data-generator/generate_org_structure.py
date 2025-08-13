 # generate_org_structure.py
import json
from faker import Faker
from pathlib import Path
import slugify

# --------------------------
# CONFIG: Fixed counts
# --------------------------
NUM_DEPARTMENTS = 2
COURSES_PER_DEPT = 3
SOCIETIES_PER_DEPT = 3
DEPT_ADMINS_PER_DEPT = 2
STAFF_ADMINS_PER_DEPT = 2
OFFICERS_PER_SOCIETY = 1
DOMAIN = "example.edu"

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
    """Generate slugified mailing list email."""
    return f"{slugify.slugify(name)}-{suffix}@{DOMAIN}"


def add_user(name, email, role_scope, scope_id):
    """Add a user (admin) to users list."""
    global uid_counter
    users.append({
        "id": uid_counter,
        "name": name,
        "email": email,
        "role_scope": role_scope,
        "scope_id": scope_id
    })
    uid_counter += 1


# --------------------------
#  1. Generate Departments, Courses, Societies
# --------------------------
for dept_id in range(1, NUM_DEPARTMENTS + 1):
    dept_name = f"{fake.company()} Department"
    dept_email = make_email(dept_name, "dept")
    departments.append({
        "id": dept_id,
        "name": dept_name,
        "email": dept_email
    })

    # Courses
    for _ in range(COURSES_PER_DEPT):
        course_id = len(courses) + 1
        course_name = f"{fake.bs().title()} {100 + course_id}"
        course_email = make_email(course_name, "course")
        courses.append({
            "id": course_id,
            "department_id": dept_id,
            "name": course_name,
            "email": course_email
        })

    # Societies
    for _ in range(SOCIETIES_PER_DEPT):
        soc_id = len(societies) + 1
        soc_name = f"{fake.word().title()} Society"
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
        add_user(fake.name(), fake.email(), "department", dept["id"])

    # Staff admins
    for _ in range(STAFF_ADMINS_PER_DEPT):
        add_user(fake.name(), fake.email(), "staff", dept["id"])

for soc in societies:
    for _ in range(OFFICERS_PER_SOCIETY):
        add_user(fake.name(), fake.email(), "society_officer", soc["id"])


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

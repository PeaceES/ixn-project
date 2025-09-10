import os, json, pyodbc

CS = os.environ["SQL_CS"]

# Try a few common locations for org_structure.json, relative to script and workspace root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../../"))
CANDIDATES = [
    os.path.join(SCRIPT_DIR, "org_structure.json"),
    os.path.join(SCRIPT_DIR, "../../org_structure.json"),
    os.path.join(SCRIPT_DIR, "../../../org_structure.json"),
    os.path.join(SCRIPT_DIR, "../../../../src/shared/database/data-generator/org_structure.json"),
    os.path.join(WORKSPACE_ROOT, "src/shared/database/data-generator/org_structure.json"),
]
ORG_PATH = next((p for p in CANDIDATES if os.path.exists(p)), None)
if not ORG_PATH:
    raise FileNotFoundError("org_structure.json not found. Place it next to this script or update CANDIDATES.")

print(f"Using {ORG_PATH}")

with open(ORG_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

with pyodbc.connect(CS) as cn, cn.cursor() as cur:
    # Departments
    for d in data.get("departments", []):
        cur.execute("""
            IF NOT EXISTS (SELECT 1 FROM dbo.OrgEntity WHERE EntityType=N'department' AND EntityId=?)
               INSERT dbo.OrgEntity(EntityType, EntityId, Name, Email, DepartmentId)
               VALUES (N'department', ?, ?, ?, ?)
        """, d["id"], d["id"], d["name"], d["email"], d["id"])

    # Courses
    for c in data.get("courses", []):
        cur.execute("""
            IF NOT EXISTS (SELECT 1 FROM dbo.OrgEntity WHERE EntityType=N'course' AND EntityId=?)
               INSERT dbo.OrgEntity(EntityType, EntityId, Name, Email, DepartmentId)
               VALUES (N'course', ?, ?, ?, ?)
        """, c["id"], c["id"], c["name"], c["email"], c["department_id"])

    # Societies
    for s in data.get("societies", []):
        cur.execute("""
            IF NOT EXISTS (SELECT 1 FROM dbo.OrgEntity WHERE EntityType=N'society' AND EntityId=?)
               INSERT dbo.OrgEntity(EntityType, EntityId, Name, Email, DepartmentId)
               VALUES (N'society', ?, ?, ?, ?)
        """, s["id"], s["id"], s["name"], s["email"], s["department_id"])

    cn.commit()

print("✅ Seeded OrgEntity from org_structure.json")

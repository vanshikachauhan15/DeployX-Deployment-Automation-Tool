import os
import json

def analyze_repo(project_path):
    report = {
        "auto_runnable": True,
        "type": "unknown",
        "issues": [],
        "solutions": []
    }

    if os.path.exists(os.path.join(project_path, "docker-compose.yml")):
        report["auto_runnable"] = False
        report["issues"].append("Docker based project")
        report["solutions"].append("Use docker-compose up")

    has_backend = os.path.exists(os.path.join(project_path, "backend"))
    has_frontend = os.path.exists(os.path.join(project_path, "frontend"))

    if has_backend and has_frontend:
        report["type"] = "complex_mern"

    pkg_path = None
    for root, _, files in os.walk(project_path):
        if "package.json" in files:
            pkg_path = os.path.join(root, "package.json")
            break

    if pkg_path:
        with open(pkg_path) as f:
            pkg = json.load(f)

        deps = json.dumps(pkg.get("dependencies", {})).lower()
        scripts = pkg.get("scripts", {})

        if "mongoose" in deps or "mongodb" in deps:
            report["auto_runnable"] = False
            report["issues"].append("MongoDB required")
            report["solutions"].append("Start MongoDB & configure env")

        if not ("start" in scripts or "dev" in scripts):
            report["auto_runnable"] = False
            report["issues"].append("No start/dev script")
            report["solutions"].append("Add start or dev script")

    if report["type"] == "complex_mern":
        report["auto_runnable"] = False
        report["issues"].append("Enterprise MERN project")
        report["solutions"].append("Manual / Docker setup required")

    return report

from api import database
from api.storage import ensure_storage_dirs


def main() -> None:
    ensure_storage_dirs()
    database.init_db()
    workflows = database.load_example_workflows()
    print(f"Seeded {len(workflows)} workflow(s).")
    for workflow in workflows:
        print(f"- {workflow['name']} -> /api/generated/{workflow['slug']}/run")


if __name__ == "__main__":
    main()

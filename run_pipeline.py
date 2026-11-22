import argparse
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from src.loading.clean_and_load import main as extract_clean_load

DBT_DIR = Path(__file__).parent / "dbt_project"


def run_dbt(*args):
    subprocess.run(["dbt", *args, "--profiles-dir", str(DBT_DIR)], cwd=DBT_DIR, check=True)


def main(skip_load=False):
    load_dotenv()
    if not skip_load:
        extract_clean_load()
    run_dbt("deps")
    run_dbt("run", "--select", "staging", "marts")
    run_dbt("test")
    run_dbt("run", "--select", "reports")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-load", action="store_true")
    main(parser.parse_args().skip_load)
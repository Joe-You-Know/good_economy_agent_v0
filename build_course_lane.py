import argparse
from pathlib import Path
from agent.course_lane import build

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Good Economy Agent course lane bundle.")
    parser.add_argument("--config", default="config.course_lane.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    bundle = build(root, config_path=Path(args.config))
    print("Course lane bundle created.")
    print(f"Bundle: {bundle['bundle_dir']}")
    print("Revenue collected: $0.00")

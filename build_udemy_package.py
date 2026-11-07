import argparse
from pathlib import Path

from agent.udemy_lane import build


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a local Udemy-ready course submission package.")
    parser.add_argument("--config", default="config.udemy_lane.json")
    parser.add_argument("--blueprint", default="data/udemy_course_blueprint.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    result = build(root, config_path=Path(args.config), blueprint_path=Path(args.blueprint))
    manifest = result["manifest"]
    validation = manifest["validation"]
    print("Udemy course package created.")
    print(f"Bundle: {result['output_dir']}")
    print(f"Planned video minutes: {validation['total_planned_video_minutes']:.0f}")
    print(f"Lecture count: {validation['lecture_count']}")
    print("Udemy published: false")
    print("Revenue collected: $0.00")

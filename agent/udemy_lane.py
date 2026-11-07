import json
import re
import struct
import zlib
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def word_count(text):
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def lecture_minutes(blueprint):
    return sum(float(lecture.get("estimated_minutes", 0)) for lecture in blueprint.get("lectures", []))


def guardrail_flags(config):
    return {
        "negative_ethics_allowed": bool(config.get("negative_ethics_allowed")),
        "external_actions_allowed": bool(config.get("external_actions_allowed")),
        "publish_to_udemy_allowed": bool(config.get("publish_to_udemy_allowed")),
        "fake_urgency_allowed": bool(config.get("fake_urgency_allowed")),
        "fake_testimonials_allowed": bool(config.get("fake_testimonials_allowed")),
        "earnings_claims_allowed": bool(config.get("earnings_claims_allowed")),
        "unsupported_safety_guarantees_allowed": bool(config.get("unsupported_safety_guarantees_allowed")),
    }


def validate_package_inputs(blueprint, config):
    checks = []
    blocked = []

    minutes = lecture_minutes(blueprint)
    lecture_count = len(blueprint.get("lectures", []))
    description_words = word_count(blueprint.get("description", ""))
    flags = guardrail_flags(config)

    checks.append({
        "name": "minimum_video_minutes",
        "passed": minutes >= config["minimum_video_minutes"],
        "observed": minutes,
        "required": config["minimum_video_minutes"],
    })
    checks.append({
        "name": "minimum_lecture_count",
        "passed": lecture_count >= config["minimum_lecture_count"],
        "observed": lecture_count,
        "required": config["minimum_lecture_count"],
    })
    checks.append({
        "name": "minimum_description_words",
        "passed": description_words > config["minimum_description_words"],
        "observed": description_words,
        "required": f">{config['minimum_description_words']}",
    })
    checks.append({
        "name": "ai_use_disclosure",
        "passed": bool(blueprint.get("ai_disclosure")) if config.get("ai_use_disclosure_required") else True,
        "observed": bool(blueprint.get("ai_disclosure")),
        "required": config.get("ai_use_disclosure_required"),
    })

    for flag, value in flags.items():
        checks.append({
            "name": flag,
            "passed": value is False,
            "observed": value,
            "required": False,
        })

    for claim in blueprint.get("forbidden_claims", []):
        positive_surfaces = "\n".join([
            blueprint.get("title", ""),
            blueprint.get("subtitle", ""),
            blueprint.get("description", ""),
            "\n".join(blueprint.get("what_you_will_learn", [])),
            "\n".join(blueprint.get("requirements", [])),
            "\n".join(blueprint.get("intended_learners", [])),
        ])
        checks.append({
            "name": f"forbidden_claim_absent::{claim}",
            "passed": claim not in positive_surfaces,
            "observed": "present" if claim in positive_surfaces else "absent",
            "required": "absent",
        })

    for check in checks:
        if not check["passed"]:
            blocked.append(check)

    return {
        "allowed": not blocked,
        "checks": checks,
        "blocked_checks": blocked,
        "total_planned_video_minutes": minutes,
        "lecture_count": lecture_count,
        "description_word_count": description_words,
        "negative_ethics_debt": 0.0 if not blocked else len(blocked),
    }


def md_list(items):
    return "\n".join(f"- {item}" for item in items)


def quiz_markdown(quizzes):
    sections = []
    for quiz in quizzes:
        lines = [f"## {quiz['title']}", ""]
        for idx, question in enumerate(quiz.get("questions", []), 1):
            lines.append(f"### Question {idx}")
            lines.append("")
            lines.append(question["prompt"])
            lines.append("")
            lines.extend(f"- {choice}" for choice in question.get("choices", []))
            lines.append("")
            lines.append(f"Answer: {question['answer']}")
            lines.append("")
        sections.append("\n".join(lines).strip())
    return "\n\n".join(sections)


def write_png(path, width, height, pixel_fn):
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    rows = []
    for y in range(height):
        row = bytearray()
        row.append(0)
        for x in range(width):
            row.extend(pixel_fn(x, y))
        rows.append(bytes(row))

    raw = b"".join(rows)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6))
    png += chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def create_course_image(path):
    width = 1600
    height = 900

    def rect(x, y, box):
        x1, y1, x2, y2 = box
        return x1 <= x <= x2 and y1 <= y <= y2

    def pixel(x, y):
        bg = (244, 247, 244)
        grid = (228, 233, 230)
        terminal = (24, 35, 48)
        terminal_top = (16, 118, 110)
        panel = (250, 252, 250)
        accent = (20, 139, 126)
        amber = (220, 154, 52)
        muted = (95, 111, 122)

        color = bg
        if x % 80 == 0 or y % 80 == 0:
            color = grid

        if rect(x, y, (170, 170, 1030, 700)):
            color = terminal
        if rect(x, y, (170, 170, 1030, 245)):
            color = terminal_top
        if rect(x, y, (230, 315, 950, 365)) or rect(x, y, (230, 420, 860, 470)) or rect(x, y, (230, 525, 780, 575)):
            color = panel
        if rect(x, y, (250, 332, 330, 348)) or rect(x, y, (250, 437, 330, 453)) or rect(x, y, (250, 542, 330, 558)):
            color = accent
        if rect(x, y, (350, 333, 900, 347)) or rect(x, y, (350, 438, 810, 452)) or rect(x, y, (350, 543, 730, 557)):
            color = muted

        cx, cy = 1210, 435
        dx = abs(x - cx)
        dy = abs(y - cy)
        if dx + dy < 245:
            color = (236, 248, 244)
        if 178 < dx + dy < 192:
            color = accent
        if rect(x, y, (1125, 420, 1185, 480)) or rect(x, y, (1185, 480, 1320, 525)):
            color = accent
        if rect(x, y, (1188, 285, 1232, 390)):
            color = amber
        if rect(x, y, (1160, 360, 1260, 390)):
            color = amber

        return color

    write_png(path, width, height, pixel)
    return {"path": str(path), "width": width, "height": height}


def write_outputs(root, blueprint, config, validation):
    output_dir = Path(root) / "outputs" / "udemy_course_package"
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {}

    def write(name, text):
        path = output_dir / name
        path.write_text(text.strip() + "\n", encoding="utf-8")
        files[name] = str(path)

    checks_lines = []
    for check in validation["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        checks_lines.append(f"- {status}: {check['name']} observed={check['observed']} required={check['required']}")

    write("00_submission_checklist.md", f"""
# Udemy Submission Checklist

## Status

Local package only. Not published to Udemy.

## Course

- Title: {blueprint['title']}
- Subtitle: {blueprint['subtitle']}
- Category: {blueprint['category']} / {blueprint['subcategory']}
- Level: {blueprint['level']}
- Language: {blueprint['language']}
- Planned video time: {validation['total_planned_video_minutes']:.0f} minutes
- Planned lectures: {validation['lecture_count']}
- Suggested Udemy base price: ${blueprint['base_price_usd']:.2f}

## Minimum requirement checks

{chr(10).join(checks_lines)}

## Required human/media work before submission

- Record at least {config['minimum_video_minutes']} minutes of HD video.
- Record at least {config['minimum_lecture_count']} separate lectures.
- Use clear audio that comes from both channels and stays synced to video.
- Upload a course image that follows Udemy image standards.
- Add a complete instructor bio and profile picture in Udemy.
- Review all scripts manually before recording.
- Submit to Udemy quality review only after the recorded media exists.

## Boundaries

- No fake urgency.
- No fake testimonials.
- No earnings claims.
- No unsupported safety guarantees.
- No claim of official Claude or Anthropic endorsement.
- Revenue counts only after settled external buyer payment evidence.
""")

    write("01_udemy_landing_page.md", f"""
# Udemy Landing Page Draft

## Course title

{blueprint['title']}

## Subtitle

{blueprint['subtitle']}

## Course description

{blueprint['description']}

## AI-use disclosure

{blueprint['ai_disclosure']}

## Important disclaimer

{blueprint['official_disclaimer']}

{blueprint['safety_disclaimer']}

{blueprint['testimonial_disclaimer']}

## What you will learn

{md_list(blueprint['what_you_will_learn'])}

## Requirements

{md_list(blueprint['requirements'])}

## Intended learners

{md_list(blueprint['intended_learners'])}

## Not for

{md_list(blueprint['not_for'])}
""")

    curriculum_lines = []
    for lecture in blueprint["lectures"]:
        curriculum_lines.extend([
            f"## Lecture {lecture['number']}: {lecture['title']}",
            "",
            f"- Estimated video time: {lecture['estimated_minutes']} minutes",
            f"- Objective: {lecture['objective']}",
            f"- Screen plan: {lecture['screen_plan']}",
            "",
        ])
    write("02_curriculum_and_video_plan.md", f"""
# Curriculum and Video Plan

Total planned video time: {validation['total_planned_video_minutes']:.0f} minutes.

{chr(10).join(curriculum_lines)}
""")

    script_sections = []
    for lecture in blueprint["lectures"]:
        points = "\n".join(f"{idx}. {point}" for idx, point in enumerate(lecture["script_points"], 1))
        script_sections.append(f"""
## Lecture {lecture['number']}: {lecture['title']}

Estimated time: {lecture['estimated_minutes']} minutes

Objective: {lecture['objective']}

Screen plan: {lecture['screen_plan']}

Narration/script outline:

{points}

Closing line:

Before moving on, write down one concrete way this lecture changes your own command-review workflow. Keep the answer specific and testable.
""".strip())
    write("03_full_lecture_scripts.md", f"""
# Full Lecture Scripts

These are recording scripts. They still require human review, live demonstration recording, and final technical verification before Udemy submission.

{chr(10).join(script_sections)}
""")

    write("04_recording_plan.md", f"""
# Recording Plan

## Setup

- Resolution: 1920x1080 or 1280x720.
- Audio: clear dual-channel audio, checked before recording.
- Workspace: disposable folder only.
- Secrets: no credentials, private source code, private browsing data, API keys, cookies, or personal documents on screen.
- Terminal: large readable font.

## Recording order

1. Record Lecture 1 with a static risk map.
2. Record Lecture 2 while completing the command-risk table.
3. Record Lecture 3 while building the hook policy table.
4. Record Lecture 4 in a disposable workspace using simulations/dry-run inputs.
5. Record Lecture 5 with a sample log and privacy review.
6. Record Lecture 6 with the capstone worksheet.

## Quality gate

- No destructive command is executed.
- No private information appears on screen.
- Audio is synced and understandable.
- Every lecture has a clear start, outcome, and close.
- Limitations are stated without overclaiming.
""")

    assignments = []
    for assignment in blueprint.get("assignments", []):
        assignments.append(f"## {assignment['title']}\n\n{assignment['instructions']}")
    write("05_assignments_quizzes.md", f"""
# Assignments and Quizzes

{chr(10).join(assignments)}

{quiz_markdown(blueprint.get('quizzes', []))}
""")

    write("06_ai_ethics_and_claims_review.md", f"""
# AI, Ethics, and Claims Review

## AI disclosure

{blueprint['ai_disclosure']}

## Official-status disclosure

{blueprint['official_disclaimer']}

## Safety disclosure

{blueprint['safety_disclaimer']}

## Testimonial disclosure

{blueprint['testimonial_disclaimer']}

## Forbidden claims

{md_list(blueprint['forbidden_claims'])}

## Ethics result

- Negative ethics allowed: {config['negative_ethics_allowed']}
- External actions allowed by this package: {config['external_actions_allowed']}
- Publish to Udemy allowed by this package: {config['publish_to_udemy_allowed']}
- Negative ethics debt: {validation['negative_ethics_debt']}
""")

    write("07_revenue_and_platform_notes.md", f"""
# Revenue and Platform Notes

## Udemy channel

Suggested Udemy base price: ${blueprint['base_price_usd']:.2f}

Udemy publication is not complete until the recorded course is uploaded and accepted through Udemy quality review. This package performs no Udemy upload and collects no Udemy payment.

## Existing Payhip beta

Payhip beta URL: {blueprint['source_payhip_beta_url']}

The Payhip product remains the immediate paid beta channel. Udemy would be a marketplace channel after recording and review.

## Revenue recognition

Revenue remains $0.00 for this Udemy package until an external buyer payment settles and evidence is recorded. Listings, drafts, wishlists, unpaid carts, coupons, and self-payments are not revenue.
""")

    write("08_publish_instructions.md", f"""
# Udemy Publish Instructions

## Before logging in to Udemy

1. Record the six planned lectures.
2. Verify total recorded video time is at least {config['minimum_video_minutes']} minutes.
3. Verify there are at least {config['minimum_lecture_count']} lectures.
4. Verify audio/video quality.
5. Create or upload a compliant course image.
6. Prepare instructor bio and profile picture.
7. Review AI-use disclosure and all limitation statements.

## Udemy fields to paste

- Title: see `01_udemy_landing_page.md`.
- Subtitle: see `01_udemy_landing_page.md`.
- Description: see `01_udemy_landing_page.md`.
- What you will learn: see `01_udemy_landing_page.md`.
- Requirements: see `01_udemy_landing_page.md`.
- Intended learners: see `01_udemy_landing_page.md`.
- Course curriculum: see `02_curriculum_and_video_plan.md`.

## Do not submit if

- Any lecture is missing.
- Recorded video is under {config['minimum_video_minutes']} minutes.
- The course lacks AI-use disclosure.
- Any fake urgency, fake testimonial, earnings claim, or safety guarantee appears.
- The course image or instructor profile is incomplete.
""")

    image_info = create_course_image(output_dir / "udemy_course_image_concept.png")
    files["udemy_course_image_concept.png"] = image_info["path"]

    write("09_course_image_brief.md", f"""
# Course Image Brief

## Generated concept

- File: `udemy_course_image_concept.png`
- Dimensions: {image_info['width']} x {image_info['height']} px
- Format: PNG
- Text in image: none

## Rationale

The image uses a simple abstract terminal and review/check motif to communicate command review without using the course title, unsupported logos, fake badges, certification marks, or sensational imagery.

## Udemy image notes

- Keep the course title out of the image.
- Use a unique image for this course.
- Keep the design simple and readable after mobile cropping.
- Do not use Claude, Anthropic, Udemy, or other third-party logos unless rights and policy review support it.
""")

    manifest = {
        "course_id": blueprint["course_id"],
        "title": blueprint["title"],
        "source_payhip_beta_url": blueprint["source_payhip_beta_url"],
        "files": files,
        "validation": validation,
        "external_actions_performed": False,
        "udemy_published": False,
        "payment_collected": False,
        "revenue_countable_now": False,
        "course_image": image_info,
        "next_step": "Record videos and complete Udemy media/profile requirements before any Udemy submission.",
        "official_reference_urls": config.get("official_reference_urls", []),
    }
    (output_dir / "udemy_submission_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    files["udemy_submission_manifest.json"] = str(output_dir / "udemy_submission_manifest.json")
    return {"output_dir": str(output_dir), "files": files, "manifest": manifest}


def build(root, config_path=None, blueprint_path=None):
    root = Path(root)
    config_file = Path(config_path) if config_path else Path("config.udemy_lane.json")
    blueprint_file = Path(blueprint_path) if blueprint_path else Path("data/udemy_course_blueprint.json")
    if not config_file.is_absolute():
        config_file = root / config_file
    if not blueprint_file.is_absolute():
        blueprint_file = root / blueprint_file

    config = load_json(config_file)
    blueprint = load_json(blueprint_file)
    validation = validate_package_inputs(blueprint, config)
    if not validation["allowed"]:
        blocked = ", ".join(check["name"] for check in validation["blocked_checks"])
        raise SystemExit(f"Udemy package blocked by validation: {blocked}")
    return write_outputs(root, blueprint, config, validation)

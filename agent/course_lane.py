import json
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def score_course(o, config):
    w = config["course_lane_weights"]
    positive = {
        "problem_specificity": o["problem_specificity"] * w["problem_specificity"],
        "learner_benefit": o["learner_benefit"] * w["learner_benefit"],
        "public_good_safety_value": o["public_good_safety_value"] * w["public_good_safety_value"],
        "build_feasibility": o["build_feasibility"] * w["build_feasibility"],
        "evidence_basis": o["evidence_basis"] * w["evidence_basis"],
        "revenue_feasibility": o["revenue_feasibility"] * w["revenue_feasibility"],
    }
    negative = {
        "negative_ethics_risk": o["negative_ethics_risk"] * w["negative_ethics_risk"],
        "unsupported_claim_risk": o["unsupported_claim_risk"] * w["unsupported_claim_risk"],
        "audience_dependency": o["audience_dependency"] * w["audience_dependency"],
    }
    score = sum(positive.values()) - sum(negative.values())
    return round(score, 6), {
        "positive_components": positive,
        "negative_components": negative,
        "positive_total": round(sum(positive.values()), 6),
        "negative_total": round(sum(negative.values()), 6),
        "raw_score": round(score, 6),
        "interpretation": "Higher is better. Negative ethics, unsupported claims, and audience dependency are intentionally expensive."
    }


def ethics_check(o, config):
    blocked = []
    reasons = []
    negative_debt = 0.0

    if o["negative_ethics_risk"] > 0.15:
        blocked.append("negative_ethics_risk")
        negative_debt += o["negative_ethics_risk"]
    if o["unsupported_claim_risk"] > 0.15:
        blocked.append("unsupported_claim_risk")
        negative_debt += o["unsupported_claim_risk"]
    for key, debt in [
        ("external_actions_allowed", 0.25),
        ("cold_outreach_allowed", 0.25),
        ("testimonials_allowed_without_real_student_use", 0.5),
        ("fake_urgency_allowed", 0.5),
        ("earnings_claims_allowed", 0.5),
    ]:
        if config.get(key, False):
            blocked.append(key)
            negative_debt += debt

    allowed = negative_debt == 0.0
    if allowed:
        reasons.append("Allowed: specific opt-in education product below negative-risk thresholds.")
    else:
        reasons.append("Blocked: clean course baseline cannot accept negative ethics debt.")

    positive_score = round((o["learner_benefit"] + o["public_good_safety_value"] + o["problem_specificity"] + o["evidence_basis"]) / 4, 4)
    return {
        "allowed": allowed,
        "negative_debt": round(negative_debt, 6),
        "positive_score": positive_score,
        "blocked_categories": blocked,
        "reasons": reasons,
        "separate_ledgers_note": "Positive ethics cannot erase negative ethics debt."
    }


def write_bundle(root, o, score, audit, ethics, config):
    bundle = Path(root) / "outputs" / "course_bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    refund_days = config.get("default_refund_window_days", 14)
    price = o["suggested_beta_price_usd"]
    audience = o["audience"].rstrip(".")

    files = {}

    def w(name, text):
        path = bundle / name
        path.write_text(text.strip() + "\n", encoding="utf-8")
        files[name] = str(path)

    forbidden = "\n".join("- " + x for x in o["forbidden_claims"])

    w("landing_page_beta.md", f"""
# {o['title']}

## Beta Course Invitation

This beta mini-course is for **{audience}**.

## The micro-problem

{o['micro_problem']}

## Before

{o['before_state']}

## After

{o['after_state']}

## What you will learn

- Why destructive command guards matter when using AI coding tools.
- How to think about pre-execution safety checks.
- How to install and test a local Bash command safety hook.
- How to evaluate limitations instead of assuming perfect protection.
- How to adapt the pattern to your own workflow.

## Beta price

**${price:.2f}**

This beta price is offered because the course is being refined. The course does not yet have student success stories, testimonials, or outcome guarantees.

## Important limitations

This course does not guarantee safety. It teaches a defensive pattern that can reduce some obvious risks. You remain responsible for your own system, tools, backups, and command execution choices.

## Refund policy

If the beta course does not match this description, request a refund within {refund_days} days.

## Ethical sales commitments

- No fake urgency.
- No fake testimonials.
- No earnings claims.
- No claim of official endorsement.
- No claim that this prevents all destructive commands.
- No cold outreach required to buy.
""")

    w("free_lesson.md", f"""
# Free Lesson: Why Pre-Execution Command Guards Matter

## Course context

{o['title']}

## The core safety problem

AI-assisted coding tools can propose or execute shell commands. Shell commands are powerful because they can change files, databases, branches, and production systems.

A safety hook is not a replacement for judgment. It is a guardrail that can catch obvious high-risk patterns before execution.

## Examples of patterns worth blocking or reviewing

- Recursive force deletion such as `rm -rf`.
- SQL destruction such as `DROP TABLE`.
- Forced history rewrite such as `git push --force`.
- Table truncation such as `TRUNCATE`.
- Broad deletion such as `DELETE FROM table` without a `WHERE` clause.

## Defensive mindset

The purpose is not to eliminate all risk. The purpose is to increase recovery time, visibility, and choice.

A good hook should:

1. detect obvious high-risk commands,
2. block or require review,
3. log the attempted command,
4. avoid interfering with normal safe commands,
5. be easy to test locally.

## Practice question

List three commands in your own workflow that would be dangerous if executed by mistake. For each one, write the reason it is dangerous and what evidence you would want before allowing it.
""")

    w("beta_curriculum.md", f"""
# Beta Curriculum

## Course title

{o['title']}

## Format

Four short sessions or modules. Each module can be delivered live or asynchronously.

## Module 1 - Threat Model for AI Coding Agents

Outcome: learner can explain why terminal-capable agents need local safety boundaries.

## Module 2 - Pattern-Based Bash Blocking

Outcome: learner can identify dangerous command families and write conservative matching rules.

## Module 3 - Logging and Local Verification

Outcome: learner can test a hook without risking their real project.

## Module 4 - Adapting the Hook to Your Workflow

Outcome: learner can modify hook policy while preserving safety.

## Beta feedback questions

1. Which step was confusing?
2. Which command pattern felt most relevant?
3. Did the limitations feel clear?
4. What would you need before trusting this in a real project?
5. What should be added, removed, or simplified?
""")

    w("worksheets.md", """
# Worksheets

## Worksheet 1 - Command Risk Inventory

| Command pattern | Why it is risky | Safe alternative/review step | Should block? |
|---|---|---|---|
| `rm -rf` | Recursive force deletion | require manual review/backups | yes |
| `DROP TABLE` | Destroys database table | require migration review | yes |
| `git push --force` | Rewrites remote history | require branch/protection review | yes |

## Worksheet 2 - Hook Acceptance Checklist

- [ ] Blocks recursive force deletion patterns.
- [ ] Blocks force-push patterns.
- [ ] Blocks destructive SQL patterns.
- [ ] Allows ordinary commands such as `git status`.
- [ ] Logs blocked attempts.
- [ ] Uses a sandboxable log path for tests.
- [ ] Includes self-tests.
- [ ] Documents limitations.

## Worksheet 3 - Limitation Statement

Write a plain-language limitation statement for your tool.
""")

    w("refund_and_testimonial_policy.md", f"""
# Refund and Testimonial Policy

## Refunds

Beta buyers may request a refund within {refund_days} days if the course does not match the published description.

## Testimonials

Testimonials may only be used if:

- the student actually took or used the course,
- the statement is truthful,
- permission is documented,
- material connections are disclosed,
- the testimonial is not presented as typical unless evidence supports that.

## Prohibited marketing claims

{forbidden}

## No fake urgency

Do not claim limited seats unless there is a real capacity limit.

## No earnings claims

This course teaches safety practices. It does not make income claims.
""")

    w("ethics_review.md", f"""
# Ethics Review

## Course

{o['title']}

## Positive ethics claim

{o['positive_ethics_claim']}

## Negative ethics debt

{ethics['negative_debt']}

## Positive ethics score

{ethics['positive_score']}

## Decision

Allowed: {ethics['allowed']}

## Reasons

{chr(10).join('- ' + reason for reason in ethics['reasons'])}

## Separate ledger rule

Positive education value cannot erase negative ethics debt. This bundle creates no testimonials, no fake urgency, no outreach, and no payment collection.
""")

    ladder = config.get("course_price_ladder_usd", {})
    w("revenue_path.md", f"""
# Revenue Path

## Current countable revenue

$0.00

This bundle performs no external action and collects no payment.

## Clean future revenue path

1. Publish the free lesson.
2. Publish the beta landing page in an opt-in location.
3. Offer the beta course at ${price:.2f}.
4. Deliver the course only to opt-in buyers.
5. Collect feedback and real testimonials only after actual use.
6. Raise price only after evidence of value.

## Price ladder

- Free sample: ${ladder.get('free_sample', 0):.2f}
- Micro-product: ${ladder.get('micro_product', 17):.2f}
- Beta course low: ${ladder.get('beta_course_low', 49):.2f}
- Beta target: ${ladder.get('beta_course_target', 97):.2f}
- Premium future-only after proof: ${ladder.get('premium_course_future_only_after_proof', 197):.2f}

## Revenue validation requirements

Revenue counts only after:

- payment is received from an external party,
- the buyer opted in,
- claims were truthful,
- no fake urgency/testimonials were used,
- fees are deducted,
- the revenue event is traceable to logged actions.
""")

    manifest = {
        "course": o,
        "score": score,
        "score_audit": audit,
        "ethics": ethics,
        "files": files,
        "external_actions_performed": False,
        "payment_collected": False,
        "revenue_countable_now": False,
        "next_allowed_step": "Human review, then optionally publish free lesson and beta page in an opt-in location."
    }
    (bundle / "bundle_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    files["bundle_manifest.json"] = str(bundle / "bundle_manifest.json")
    (bundle / "course_score.json").write_text(json.dumps({"score": score, "audit": audit, "ethics": ethics}, indent=2), encoding="utf-8")
    files["course_score.json"] = str(bundle / "course_score.json")

    file_list = "\n".join(f"- `{name}`" for name in files)
    w("final_course_lane_report.md", f"""
# Course Lane Final Report

## Selected course

{o['title']}

## Micro-problem

{o['micro_problem']}

## Before -> After

**Before:** {o['before_state']}

**After:** {o['after_state']}

## Audience

{o['audience']}

## Suggested beta price

${price:.2f}

## Score

{score}

## Score audit

```json
{json.dumps(audit, indent=2)}
```

## Ethics

```json
{json.dumps(ethics, indent=2)}
```

## Generated files

{file_list}

## External actions

None.

## Revenue collected

$0.00.

## Countability status

This is not countable revenue yet. It is a local course-validation bundle that can be reviewed before any opt-in publication or sale.

## Clean next step

Human review, then optionally publish the free lesson and beta page in an opt-in location. Do not use cold outreach, fake urgency, fake testimonials, or unsupported claims.
""")
    return {"bundle_dir": str(bundle), "files": files, "manifest": manifest}


def build(root, config_path=None):
    root = Path(root)
    config_file = Path(config_path) if config_path else Path("config.course_lane.json")
    if not config_file.is_absolute():
        config_file = root / config_file
    config = load_json(config_file)
    opportunities = load_json(root / "data" / "course_opportunities.json")

    candidates = []
    for o in opportunities:
        score, audit = score_course(o, config)
        ethics = ethics_check(o, config)
        if ethics["allowed"]:
            candidates.append((score, o, audit, ethics))
    if not candidates:
        raise SystemExit("No course opportunities passed the ethics gate.")

    candidates.sort(key=lambda x: x[0], reverse=True)
    score, best, audit, ethics = candidates[0]
    return write_bundle(root, best, score, audit, ethics, config)

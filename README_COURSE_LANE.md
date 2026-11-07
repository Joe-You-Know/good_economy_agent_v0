# Good Economy Agent - Course Lane v0

This drop-in package adds a **course/product validation lane** to Good Economy Agent without enabling external actions.

It generates a local course-validation bundle for:

**Claude Code Safety Hooks: Block Destructive Bash Commands Before They Execute**

The lane creates:

```text
outputs/course_bundle/
  bundle_manifest.json
  course_score.json
  landing_page_beta.md
  free_lesson.md
  beta_curriculum.md
  worksheets.md
  refund_and_testimonial_policy.md
  ethics_review.md
  revenue_path.md
  final_course_lane_report.md
```

It does **not** publish, message, collect payment, browse, create fake urgency, create testimonials, or spend API credit.

Run:

```powershell
py build_course_lane.py --config config.course_lane.json
```

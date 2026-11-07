import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repoRoot = path.resolve("D:/GoodEconomyAgent/good_economy_agent_v0");
const setupDir = path.join(repoRoot, "outputs", "listing_payment_setup", "course_safety_hooks");
const uploadDir = path.join(repoRoot, "outputs", "course_product_upload");
const zipPath = path.join(uploadDir, "Claude_Code_Safety_Hooks_Beta_Course.zip");
const coverPath = path.join(uploadDir, "Claude_Code_Safety_Hooks_Beta_Course_Cover.png");
const reportPath = path.join(setupDir, "PAYHIP_COURSE_PUBLISH_REPORT_2026-06-18.md");
const jsonReportPath = path.join(setupDir, "PAYHIP_COURSE_PUBLISH_REPORT_2026-06-18.json");
const screenshotPath = path.join(setupDir, "PAYHIP_COURSE_PUBLISH_SCREENSHOT_2026-06-18.png");

const product = {
  name: "Claude Code Safety Hooks: Block Destructive Bash Commands Before They Execute - Beta Course",
  price: "49.00",
  paymentDestination: "Payhip checkout; expected PayPal payout destination is josephfredrickson@live.com",
  description: `Independent beta course for developers and AI-assisted coders who use terminal-capable coding agents.

The micro-problem: AI coding agents can accidentally execute destructive shell commands unless a pre-execution hook blocks obvious high-risk patterns.

Before: the learner uses AI coding tools without a local safety hook for destructive Bash commands.

After: the learner can install, test, and reason about a local PreToolUse-style Bash safety hook that blocks destructive patterns and logs attempts.

What you receive:
- Free introductory lesson.
- Beta course curriculum.
- Command-risk inventory worksheet.
- Hook acceptance checklist.
- Refund and testimonial policy.
- Buyer README with support boundaries.

What you will learn:
- Why destructive command guards matter when using AI coding tools.
- How to think about pre-execution safety checks.
- How to identify dangerous command families such as recursive force deletion, destructive SQL, and forced history rewrites.
- How to test a local Bash command safety hook.
- How to evaluate limitations instead of assuming perfect protection.

Important limitations:
This course does not guarantee safety. It teaches a defensive pattern that can reduce some obvious risks. You remain responsible for your own system, tools, backups, and command execution choices.

This is not official Claude, Anthropic, or Payhip documentation. It is not sponsored by or endorsed by Anthropic. It is not legal, financial, security, or professional advice.

There are no student testimonials yet because this is a beta course. No outcome guarantees or earnings claims are made.

Refund policy:
If the beta course does not match this description, request a refund through Payhip within 14 days.

Support boundary:
Do not send private source code, account credentials, cookies, API keys, browsing data, medical information, legal documents, financial account information, or personal documents for support.`,
};

const payhipEmail = process.env.PAYHIP_EMAIL || "";
const payhipPassword = process.env.PAYHIP_PASSWORD || "";

function nowIso() {
  return new Date().toISOString();
}

function writeReport(result) {
  fs.mkdirSync(setupDir, { recursive: true });
  fs.writeFileSync(jsonReportPath, JSON.stringify(result, null, 2) + "\n", "utf8");
  const lines = [
    "# Payhip Course Publish Report",
    "",
    `Generated UTC: ${result.timestamp_utc}`,
    "",
    "## Status",
    "",
    result.status,
    "",
    "## Product",
    "",
    `- Product: ${product.name}`,
    `- Price: USD ${product.price}`,
    `- Payment path: ${product.paymentDestination}`,
    result.public_url ? `- Public URL: ${result.public_url}` : "- Public URL: not available",
    "",
    "## Actions",
    "",
    ...(result.actions.length ? result.actions.map((item) => `- ${item}`) : ["- none"]),
    "",
    "## Observations",
    "",
    ...(result.observations.length ? result.observations.map((item) => `- ${item}`) : ["- none"]),
    "",
    "## Boundaries",
    "",
    `- External write attempted: ${result.external_write_attempted}`,
    `- External write completed: ${result.external_write_completed}`,
    `- Product set visible: ${result.product_set_visible}`,
    `- Fake urgency used: ${result.fake_urgency_used}`,
    `- Fake testimonials used: ${result.fake_testimonials_used}`,
    `- Revenue recorded: ${result.revenue_recorded}`,
    "",
    "## Evidence",
    "",
    `- JSON report: ${jsonReportPath}`,
    result.screenshot_path ? `- Screenshot: ${result.screenshot_path}` : "- Screenshot: not available",
    "",
  ];
  fs.writeFileSync(reportPath, lines.join("\n"), "utf8");
  console.log(lines.join("\n"));
}

function htmlFromText(text) {
  return text
    .split(/\n{2,}/)
    .map((paragraph) => {
      if (paragraph.includes("\n- ")) {
        const [head, ...items] = paragraph.split("\n");
        const list = items
          .filter((line) => line.trim().startsWith("- "))
          .map((line) => `<li>${escapeHtml(line.trim().slice(2))}</li>`)
          .join("");
        return `<p>${escapeHtml(head)}</p><ul>${list}</ul>`;
      }
      return `<p>${escapeHtml(paragraph).replace(/\n/g, "<br>")}</p>`;
    })
    .join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function bodyText(page) {
  return page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
}

async function fillFirst(page, locators, value) {
  for (const locator of locators) {
    try {
      const first = locator.first();
      if ((await first.count()) && (await first.isVisible({ timeout: 1500 }))) {
        await first.fill(value);
        return true;
      }
    } catch {}
  }
  return false;
}

async function clickFirst(page, locators) {
  for (const locator of locators) {
    try {
      const first = locator.first();
      if ((await first.count()) && (await first.isVisible({ timeout: 1500 }))) {
        await first.click();
        return true;
      }
    } catch {}
  }
  return false;
}

async function loginIfNeeded(page, result) {
  const passwordInput = page
    .locator('input[type="password"], input[name*="password" i], input[id*="password" i]')
    .first();
  const needsPassword = await passwordInput.isVisible({ timeout: 5000 }).catch(() => false);
  if (!needsPassword) return true;

  const text = await bodyText(page);
  if (/captcha|verify you are human|two-factor|2fa|verification code|authenticator/i.test(text)) {
    result.status = "blocked_needs_user_verification";
    result.observations.push("Payhip requested CAPTCHA, two-factor, or verification-code handling.");
    return false;
  }

  if (!payhipEmail || !payhipPassword) {
    result.status = "blocked_needs_login";
    result.observations.push("Payhip login is visible and PAYHIP_EMAIL/PAYHIP_PASSWORD were not provided to this process.");
    return false;
  }

  const emailFilled = await fillFirst(
    page,
    [
      page.locator('input[type="email"]'),
      page.locator('input[name*="email" i]'),
      page.locator('input[id*="email" i]'),
      page.locator('input[placeholder*="email" i]'),
      page.locator('input[type="text"]'),
    ],
    payhipEmail,
  );
  if (!emailFilled) {
    result.status = "blocked_login_email_field_not_found";
    result.observations.push("Payhip login page was visible but email field was not found.");
    return false;
  }

  await passwordInput.fill(payhipPassword);
  result.actions.push("Submitted Payhip login form using process-provided credentials.");
  const clicked = await clickFirst(page, [
    page.getByRole("button", { name: /log in|login|sign in|continue/i }),
    page.locator('button[type="submit"], input[type="submit"]'),
  ]);
  if (!clicked) await passwordInput.press("Enter");

  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(2500);

  const afterText = await bodyText(page);
  if (/captcha|verify you are human|two-factor|2fa|verification code|authenticator/i.test(afterText)) {
    result.status = "blocked_needs_user_verification";
    result.observations.push("Payhip requested CAPTCHA, two-factor, or verification-code handling after login submission.");
    return false;
  }

  const stillPassword = await passwordInput.isVisible({ timeout: 2000 }).catch(() => false);
  if (stillPassword) {
    result.status = "blocked_login_not_accepted";
    result.observations.push("Payhip password field remains visible after login attempt.");
    return false;
  }
  return true;
}

async function fillExactForm(page, result) {
  await page.waitForSelector("form#addproduct #p_name, #p_name", { timeout: 30000 });
  await page.locator("#p_name").fill(product.name);
  await page.locator("#p_price").fill(product.price);

  const visibleRadio = page.locator('input[name="product_status"][value="visible"]').first();
  if (await visibleRadio.count()) {
    await visibleRadio.check({ force: true });
    result.product_set_visible = true;
  } else {
    result.observations.push("Visible product-status radio was not found; Payhip default may still be visible.");
  }

  const html = htmlFromText(product.description);
  await page.evaluate(
    ({ plain, htmlValue }) => {
      const editor = document.querySelector(".ql-editor");
      if (editor) {
        editor.innerHTML = htmlValue;
        editor.classList.remove("ql-blank");
        editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: plain }));
      }
      const hidden = document.querySelector('input[name="p_desc"], textarea[name="p_desc"], textarea[name*="desc" i]');
      if (hidden) {
        hidden.value = htmlValue;
        hidden.dispatchEvent(new Event("input", { bubbles: true }));
        hidden.dispatchEvent(new Event("change", { bubbles: true }));
      }
    },
    { plain: product.description, htmlValue: html },
  );

  const fileInput = page.locator("#ebook_files input[type=file], .upload-ebook-row input[type=file], input[type=file]").first();
  await fileInput.setInputFiles(zipPath);
  result.actions.push("Uploaded beta course ZIP.");
  await page.waitForTimeout(3000);

  const coverInput = page.locator(".upload-preview-img-row input[type=file]").first();
  if ((await coverInput.count()) && fs.existsSync(coverPath)) {
    await coverInput.setInputFiles(coverPath);
    result.actions.push("Uploaded course cover image.");
    await page.waitForTimeout(3000);
  } else {
    result.observations.push("Cover input was not found or cover image was missing.");
  }

  const state = {
    name: await page.locator("#p_name").inputValue().catch(() => ""),
    price: await page.locator("#p_price").inputValue().catch(() => ""),
    visibleChecked: await page
      .locator('input[name="product_status"][value="visible"]')
      .isChecked()
      .catch(() => false),
  };
  result.observations.push(`Title field after fill: ${state.name}`);
  result.observations.push(`Price field after fill: ${state.price}`);
  result.observations.push(`Visible checked after fill: ${state.visibleChecked}`);
  return state;
}

async function extractPublicUrl(page) {
  const candidates = await page
    .locator('input[value*="payhip.com/b/"], input[value*="payhip.com/"], a[href*="payhip.com/b/"], a[href*="/b/"]')
    .evaluateAll((els) =>
      els
        .map((el) => el.value || el.href || el.textContent || "")
        .map((value) => String(value).trim())
        .filter((value) => /https:\/\/payhip\.com\/b\//.test(value)),
    )
    .catch(() => []);
  return candidates[0] || "";
}

async function verifyPublicPage(browser, url, result) {
  if (!url) return;
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 }).catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const text = await bodyText(page);
  result.public_verification = {
    url: page.url(),
    has_title: text.includes("Claude Code Safety Hooks"),
    has_price: /\$49|49\.00|USD\s*49/i.test(text),
    has_no_guarantee: /does not guarantee safety|No safety guarantee/i.test(text),
    has_no_testimonial_disclosure: /no student testimonials yet/i.test(text),
    has_official_disclaimer: /not official Claude|not sponsored by or endorsed/i.test(text),
  };
  await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});
  if (fs.existsSync(screenshotPath)) result.screenshot_path = screenshotPath;
  await context.close().catch(() => {});
}

async function main() {
  const result = {
    timestamp_utc: nowIso(),
    status: "started",
    public_url: "",
    public_verification: {},
    actions: [],
    observations: [],
    external_write_attempted: false,
    external_write_completed: false,
    product_set_visible: false,
    fake_urgency_used: false,
    fake_testimonials_used: false,
    revenue_recorded: "$0.00",
    screenshot_path: "",
  };

  try {
    if (!fs.existsSync(zipPath)) throw new Error(`Missing upload ZIP: ${zipPath}`);
    if (!fs.existsSync(coverPath)) result.observations.push(`Cover image missing: ${coverPath}`);

    const browser = await chromium.launch({
      executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
      headless: false,
      args: ["--start-maximized"],
    });
    const context = await browser.newContext({ viewport: null, acceptDownloads: true });
    const page = await context.newPage();

    await page.goto("https://payhip.com/product/add/digital", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    if (!(await loginIfNeeded(page, result))) {
      writeReport(result);
      await browser.close().catch(() => {});
      return;
    }

    if (!/payhip\.com\/product\/add\/digital/.test(page.url())) {
      await page.goto("https://payhip.com/product/add/digital", { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    }

    await fillExactForm(page, result);
    result.external_write_attempted = true;
    result.actions.push("Submitted Payhip Add Product form with visible status.");
    await page.locator("#addsubmit").click();
    await page.waitForTimeout(8000);
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});

    const text = await bodyText(page);
    if (/required|error|failed|invalid|uploading/i.test(text) && !/Product Added|added successfully/i.test(text)) {
      result.status = "blocked_payhip_validation_error";
      result.observations.push("Payhip page text suggests a validation/upload error after submission.");
      result.observations.push(`Current URL: ${page.url()}`);
      await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});
      if (fs.existsSync(screenshotPath)) result.screenshot_path = screenshotPath;
      writeReport(result);
      await browser.close().catch(() => {});
      return;
    }

    result.public_url = await extractPublicUrl(page);
    if (!result.public_url && /https:\/\/payhip\.com\/b\//.test(text)) {
      result.public_url = text.match(/https:\/\/payhip\.com\/b\/[A-Za-z0-9]+/)?.[0] || "";
    }
    result.external_write_completed = Boolean(result.public_url || /Product Added|added successfully/i.test(text));
    result.status = result.external_write_completed ? "published_visible_course_product" : "submitted_needs_manual_verification";
    result.observations.push(`Current URL after submit: ${page.url()}`);
    if (result.public_url) result.observations.push(`Detected public URL: ${result.public_url}`);

    await verifyPublicPage(browser, result.public_url, result);
    writeReport(result);
    await browser.close().catch(() => {});
  } catch (error) {
    result.status = "failed";
    result.observations.push(error?.message || String(error));
    writeReport(result);
    process.exitCode = 1;
  }
}

main();

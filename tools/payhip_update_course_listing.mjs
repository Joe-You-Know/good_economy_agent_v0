import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repoRoot = path.resolve("D:/GoodEconomyAgent/good_economy_agent_v0");
const setupDir = path.join(repoRoot, "outputs", "listing_payment_setup", "course_safety_hooks");
const reportPath = path.join(setupDir, "PAYHIP_COURSE_UPDATE_REPORT_2026-06-18.md");
const jsonReportPath = path.join(setupDir, "PAYHIP_COURSE_UPDATE_REPORT_2026-06-18.json");
const screenshotPath = path.join(setupDir, "PAYHIP_COURSE_UPDATE_SCREENSHOT_2026-06-18.png");

const product = {
  publicUrl: "https://payhip.com/b/pFYwh",
  name: "Claude Code Safety Hooks: Block Destructive Bash Commands Before They Execute - Beta Course",
  needle: "Claude Code Safety Hooks",
  price: "49.00",
};

const payhipEmail = process.env.PAYHIP_EMAIL || "";
const payhipPassword = process.env.PAYHIP_PASSWORD || "";

function nowIso() {
  return new Date().toISOString();
}

function normalizePrice(value) {
  const number = Number.parseFloat(String(value || "").replace(/[^0-9.]/g, ""));
  return Number.isFinite(number) ? number.toFixed(2) : "";
}

function descriptionHtml() {
  return `
<p>Independent beta course for developers and AI-assisted coders who use terminal-capable coding agents.</p>

<p><strong>The micro-problem:</strong></p>
<p>AI coding agents can accidentally execute destructive shell commands unless a pre-execution hook blocks obvious high-risk patterns.</p>

<p><strong>Before:</strong></p>
<p>The learner uses AI coding tools without a local safety hook for destructive Bash commands.</p>

<p><strong>After:</strong></p>
<p>The learner can install, test, and reason about a local PreToolUse-style Bash safety hook that blocks destructive patterns and logs attempts.</p>

<p><strong>What you receive:</strong></p>
<ul>
  <li>Free introductory lesson.</li>
  <li>Beta course curriculum.</li>
  <li>Command-risk inventory worksheet.</li>
  <li>Hook acceptance checklist.</li>
  <li>Refund and testimonial policy.</li>
  <li>Buyer README with support boundaries.</li>
</ul>

<p><strong>What you will learn:</strong></p>
<ul>
  <li>Why destructive command guards matter when using AI coding tools.</li>
  <li>How to think about pre-execution safety checks.</li>
  <li>How to identify dangerous command families such as recursive force deletion, destructive SQL, and forced history rewrites.</li>
  <li>How to test a local Bash command safety hook.</li>
  <li>How to evaluate limitations instead of assuming perfect protection.</li>
</ul>

<p><strong>Important limitations:</strong></p>
<p>This course does not guarantee safety. It teaches a defensive pattern that can reduce some obvious risks. You remain responsible for your own system, tools, backups, and command execution choices.</p>

<p>This is not official Claude, Anthropic, or Payhip documentation. It is not sponsored by or endorsed by Anthropic. It is not legal, financial, security, or professional advice.</p>

<p>There are no student testimonials yet because this is a beta course. No outcome guarantees or earnings claims are made.</p>

<p><strong>Refund policy:</strong></p>
<p>If the beta course does not match this description, request a refund through Payhip within 14 days.</p>

<p><strong>Support boundary:</strong></p>
<p>Do not send private source code, account credentials, cookies, API keys, browsing data, medical information, legal documents, financial account information, or personal documents for support.</p>
`.trim();
}

function writeReport(result) {
  fs.mkdirSync(setupDir, { recursive: true });
  fs.writeFileSync(jsonReportPath, JSON.stringify(result, null, 2) + "\n", "utf8");
  const lines = [
    "# Payhip Course Update Report",
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
    `- Public URL: ${product.publicUrl}`,
    `- Price: USD ${product.price}`,
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
    `- Product visible after update: ${result.product_visible}`,
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
    result.observations.push("Payhip login is visible and process credentials were not provided.");
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
  const stillPasswordVisible = await passwordInput.isVisible({ timeout: 2000 }).catch(() => false);
  if (stillPasswordVisible) {
    result.status = "blocked_login_not_accepted";
    result.observations.push("Payhip password field remained visible after login attempt.");
    return false;
  }
  return true;
}

async function markEditControlForProduct(page, title) {
  return page.evaluate((productTitle) => {
    const clear = () => {
      document.querySelectorAll("[data-codex-course-edit-target]").forEach((el) => {
        el.removeAttribute("data-codex-course-edit-target");
      });
    };
    clear();
    const norm = (value) => String(value || "").replace(/\s+/g, " ").trim();
    const titleNodes = [...document.querySelectorAll("body *")]
      .filter((el) => norm(el.textContent).includes(productTitle))
      .sort((a, b) => norm(a.textContent).length - norm(b.textContent).length);

    for (const titleNode of titleNodes) {
      let current = titleNode;
      for (let depth = 0; current && depth < 10; depth += 1, current = current.parentElement) {
        const controls = [...current.querySelectorAll("a[href], button, input[type='button'], input[type='submit']")];
        for (const control of controls) {
          const text = norm(control.innerText || control.value || control.getAttribute("aria-label"));
          const href = norm(control.href || control.getAttribute("href"));
          if (/edit|manage|update|modify|product\/edit|product\/addit|products\/edit/i.test(`${text} ${href}`)) {
            control.setAttribute("data-codex-course-edit-target", "1");
            return true;
          }
        }
        if (current.matches?.("a[href]")) {
          const href = norm(current.href || current.getAttribute("href"));
          if (/product|edit|manage/i.test(href)) {
            current.setAttribute("data-codex-course-edit-target", "1");
            return true;
          }
        }
      }
    }
    return false;
  }, title);
}

async function openProductEditForm(page, result) {
  await page.goto("https://payhip.com/products", { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  if (!(await loginIfNeeded(page, result))) return false;

  const lookupUrls = [
    "https://payhip.com/products",
    "https://payhip.com/dashboard",
    product.publicUrl,
  ];
  let foundVisibleProduct = false;
  for (const url of lookupUrls) {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    const text = await bodyText(page);
    result.observations.push(`Lookup URL reached: ${page.url()}`);
    result.observations.push(`Lookup body excerpt: ${text.replace(/\s+/g, " ").trim().slice(0, 500)}`);
    if (text.includes(product.name) || text.includes(product.needle)) {
      foundVisibleProduct = true;
      break;
    }
  }

  if (!foundVisibleProduct) {
    result.status = "blocked_product_not_found_on_products_page";
    result.observations.push("The expected course product title was not visible on known Payhip management/public lookup pages.");
    result.observations.push(`Current URL: ${page.url()}`);
    return false;
  }

  const marked = (await markEditControlForProduct(page, product.name)) || (await markEditControlForProduct(page, product.needle));
  if (!marked) {
    await page.goto(product.publicUrl, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  }
  const markedAfterFallback =
    marked ||
    (await markEditControlForProduct(page, product.name)) ||
    (await markEditControlForProduct(page, product.needle));
  if (!markedAfterFallback) {
    result.status = "blocked_edit_control_not_found";
    result.observations.push("The expected course product was visible, but no nearby edit/manage control was found.");
    return false;
  }

  await page.locator("[data-codex-course-edit-target='1']").first().click();
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const formVisible = await page.locator("#p_name, input[name='p_name']").first().isVisible({ timeout: 10000 }).catch(() => false);
  if (!formVisible) {
    result.status = "blocked_product_edit_form_not_found";
    result.observations.push(`Clicked edit/manage control, but product form was not found. Current URL: ${page.url()}`);
    return false;
  }
  return true;
}

async function updateForm(page, result) {
  const nameInput = page.locator("#p_name, input[name='p_name']").first();
  const priceInput = page.locator("#p_price, input[name='p_price']").first();
  const currentName = await nameInput.inputValue().catch(() => "");
  const currentPrice = await priceInput.inputValue().catch(() => "");
  result.observations.push(`Current title field: ${currentName}`);
  result.observations.push(`Current price field: ${currentPrice}`);

  if (currentName !== product.name) {
    await nameInput.fill(product.name);
    result.actions.push("Updated title field.");
  }
  if (normalizePrice(currentPrice) !== normalizePrice(product.price)) {
    await priceInput.fill(product.price);
    result.actions.push("Updated price field.");
  }

  const visibleRadio = page.locator('input[name="product_status"][value="visible"]').first();
  if (await visibleRadio.count()) {
    await visibleRadio.check({ force: true });
    result.product_visible = true;
  }

  await page.evaluate((htmlValue) => {
    const editor = document.querySelector(".ql-editor");
    if (editor) {
      editor.innerHTML = htmlValue;
      editor.classList.remove("ql-blank");
      editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: editor.innerText || "" }));
    }
    const hidden = document.querySelector('input[name="p_desc"], textarea[name="p_desc"], textarea[name*="desc" i]');
    if (hidden) {
      hidden.value = htmlValue;
      hidden.dispatchEvent(new Event("input", { bubbles: true }));
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }, descriptionHtml());
  result.actions.push("Replaced description with formatted approved beta-course copy.");

  result.external_write_attempted = true;
  const saved = await clickFirst(page, [
    page.locator("#addsubmit"),
    page.getByRole("button", { name: /save|update|submit/i }),
    page.locator('button[type="submit"], input[type="submit"]'),
  ]);
  if (!saved) {
    result.status = "blocked_save_control_not_found";
    result.observations.push("Updated fields in browser, but no save/update control was found.");
    return;
  }

  await page.waitForTimeout(6000);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const text = await bodyText(page);
  if (/error|required|failed|invalid/i.test(text)) {
    result.status = "submitted_but_page_reports_possible_error";
    result.observations.push("Save was clicked, but the page text suggests a possible validation error.");
  } else {
    result.status = "updated_existing_course_product";
    result.external_write_completed = true;
  }
}

async function verifyPublic(browser, result) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(product.publicUrl, { waitUntil: "domcontentloaded", timeout: 45000 }).catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const text = await bodyText(page);
  result.public_verification = {
    has_title: text.includes("Claude Code Safety Hooks"),
    has_price: /\$49|49\.00/i.test(text),
    has_no_guarantee: /does not guarantee safety/i.test(text),
    has_no_testimonial_disclosure: /no student testimonials yet/i.test(text),
    has_official_disclaimer: /not sponsored by or endorsed by Anthropic/i.test(text),
    has_formatting_glitch: /limitations:This|policy:If|boundary:Do/i.test(text),
  };
  fs.mkdirSync(setupDir, { recursive: true });
  await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});
  if (fs.existsSync(screenshotPath)) result.screenshot_path = screenshotPath;
  await context.close().catch(() => {});
}

async function main() {
  const result = {
    timestamp_utc: nowIso(),
    status: "started",
    actions: [],
    observations: [],
    public_verification: {},
    external_write_attempted: false,
    external_write_completed: false,
    product_visible: false,
    fake_urgency_used: false,
    fake_testimonials_used: false,
    revenue_recorded: "$0.00",
    screenshot_path: "",
  };

  const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: false,
    args: ["--start-maximized"],
  });
  const context = await browser.newContext({ viewport: null, acceptDownloads: true });
  const page = await context.newPage();

  try {
    if (await openProductEditForm(page, result)) {
      await updateForm(page, result);
    } else if (result.status === "started") {
      result.status = "blocked_product_edit_route_not_available";
      result.observations.push("The course product edit route was not reached.");
    }
    await verifyPublic(browser, result);
  } catch (error) {
    result.status = "failed";
    result.observations.push(error?.message || String(error));
  } finally {
    result.timestamp_utc = nowIso();
    writeReport(result);
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

main().catch((error) => {
  const result = {
    timestamp_utc: nowIso(),
    status: "failed",
    actions: [],
    observations: [error?.message || String(error)],
    public_verification: {},
    external_write_attempted: false,
    external_write_completed: false,
    product_visible: false,
    fake_urgency_used: false,
    fake_testimonials_used: false,
    revenue_recorded: "$0.00",
    screenshot_path: "",
  };
  writeReport(result);
  process.exitCode = 1;
});

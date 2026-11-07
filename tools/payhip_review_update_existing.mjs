import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repoRoot = path.resolve("D:/GoodEconomyAgent/good_economy_agent_v0");
const setupDir = path.join(
  repoRoot,
  "outputs",
  "listing_payment_setup",
  "constructivert_browser_extension",
);
const uploadDir = path.join(setupDir, "upload");
const reportPath = path.join(setupDir, "PAYHIP_REVIEW_UPDATE_REPORT_2026-06-18.md");
const jsonReportPath = path.join(setupDir, "PAYHIP_REVIEW_UPDATE_REPORT_2026-06-18.json");
const screenshotPath = path.join(uploadDir, "PAYHIP_REVIEW_UPDATE_SCREENSHOT_2026-06-18.png");

const approved = {
  publicUrl: "https://payhip.com/b/FUqdj",
  productName: "ConstructiveRT Chrome v0.1.14 Technical Preview",
  priceUsd: "9",
  paymentDestination: "PayPal: josephfredrickson@live.com",
  description: `ConstructiveRT Chrome is an experimental browser-boundary observation tool for technical users who want to study how active pages produce DOM geometry reads, CSS/style writes, layout shifts, mutation pressure, and distributed attribute-storm behavior.

Version 0.1.14 adds distributed attribute-storm packetization and counters for class, style, dimension/SVG, and ARIA-state activity. It includes a popup/dashboard workflow for locking a target tab, running an observation epoch, and exporting a run summary.

This package is a technical preview intended for local testing, research, debugging, and inspection workflows. It is not a performance optimizer, security tool, ad blocker, financial tool, medical tool, legal tool, or browser replacement.

Included:
- ConstructiveRT Chrome v0.1.14 technical preview package.
- Load-unpacked Chrome installation notes.
- Local testing workflow.
- Safety and support boundary.

Permission disclosure:
ConstructiveRT requests broad page access because it observes page-boundary behavior on pages you choose to inspect. Use it only in browser profiles and on sites where that inspection boundary is appropriate.

Support boundary:
Support is limited to install/load-unpacked guidance, basic run-summary interpretation, known limitations, and bug reports. Do not send private browsing data, account credentials, cookies, form entries, personal documents, medical data, legal documents, or financial account information for support.`,
};

function nowIso() {
  return new Date().toISOString();
}

function normalizeText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function normalizePrice(value) {
  const number = Number.parseFloat(String(value || "").replace(/[^0-9.]/g, ""));
  return Number.isFinite(number) ? number.toFixed(2) : "";
}

function toHtml(description) {
  return description
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${paragraph.replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function writeReports(result) {
  fs.mkdirSync(setupDir, { recursive: true });
  fs.writeFileSync(jsonReportPath, JSON.stringify(result, null, 2) + "\n", "utf8");

  const lines = [
    "# Payhip Review/Update Report",
    "",
    `Generated UTC: ${result.timestamp_utc}`,
    "",
    "## Status",
    "",
    result.status,
    "",
    "## Scope",
    "",
    "Reviewed the existing Payhip product against the approved local listing/payment setup plan. No revenue was recorded.",
    "",
    "## Product",
    "",
    `- Expected product: ${approved.productName}`,
    `- Public URL: ${approved.publicUrl}`,
    `- Expected price: USD ${approved.priceUsd}`,
    `- Expected earned-income destination: ${approved.paymentDestination}`,
    "",
    "## Actions",
    "",
    ...(result.actions.length ? result.actions.map((item) => `- ${item}`) : ["- none"]),
    "",
    "## Observations",
    "",
    ...(result.observations.length ? result.observations.map((item) => `- ${item}`) : ["- none"]),
    "",
    "## Mismatches",
    "",
    ...(result.mismatches.length ? result.mismatches.map((item) => `- ${item}`) : ["- none"]),
    "",
    "## Boundaries",
    "",
    `- External writes attempted: ${result.external_writes_attempted}`,
    `- External writes completed: ${result.external_writes_completed}`,
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

async function waitForManualLogin(page, result) {
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  const passwordVisible = await page
    .locator('input[type="password"], input[name*="password" i], input[id*="password" i]')
    .first()
    .isVisible({ timeout: 3000 })
    .catch(() => false);
  if (!passwordVisible) return true;

  result.observations.push("Payhip login page is visible; waiting for manual login in the opened browser window.");
  await page.bringToFront().catch(() => {});
  const deadline = Date.now() + 300000;
  while (Date.now() < deadline) {
    await page.waitForTimeout(2500);
    const stillPassword = await page
      .locator('input[type="password"], input[name*="password" i], input[id*="password" i]')
      .first()
      .isVisible({ timeout: 1000 })
      .catch(() => false);
    const body = await page.locator("body").innerText({ timeout: 2000 }).catch(() => "");
    if (/captcha|verify you are human|two-factor|2fa|verification code|authenticator/i.test(body)) {
      result.status = "blocked_needs_user_verification";
      result.observations.push("Payhip requires CAPTCHA, two-factor, or verification-code handling.");
      return false;
    }
    if (!stillPassword && /payhip\.com\/(products|dashboard|product)/.test(page.url())) {
      result.observations.push("Manual login appears complete.");
      return true;
    }
  }
  result.status = "blocked_needs_manual_login";
  result.observations.push("Timed out waiting for manual login.");
  return false;
}

async function goToExistingProduct(page, result) {
  await page.goto("https://payhip.com/products", { waitUntil: "domcontentloaded" });
  if (!(await waitForManualLogin(page, result))) return false;
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});

  let body = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
  if (!body.includes(approved.productName)) {
    result.observations.push("Product name was not immediately visible on the products page; checking public product page for owner edit controls.");
    await page.goto(approved.publicUrl, { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    body = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
  }

  if (/payhip\.com\/product\/add/i.test(page.url())) {
    result.status = "blocked_add_product_page";
    result.observations.push("Refused to operate on the Payhip add-product page.");
    return false;
  }

  const clickedEdit = await clickFirst(page, [
    page.getByRole("link", { name: /edit/i }),
    page.getByRole("button", { name: /edit/i }),
    page.locator(`text=${approved.productName}`).locator("..").getByRole("link", { name: /edit/i }),
    page.locator(`a:has-text("${approved.productName}")`),
  ]);
  if (clickedEdit) {
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  }

  const productFormVisible = await page
    .locator("#p_name, input[name='p_name'], input[name*='name' i]")
    .first()
    .isVisible({ timeout: 5000 })
    .catch(() => false);
  if (!productFormVisible) {
    result.status = "blocked_product_edit_form_not_found";
    result.observations.push(`Could not find the product edit form. Current URL: ${page.url()}`);
    return false;
  }

  if (/payhip\.com\/product\/add/i.test(page.url())) {
    result.status = "blocked_add_product_page";
    result.observations.push("Refused to operate after reaching an add-product form instead of an edit form.");
    return false;
  }

  return true;
}

async function inspectAndUpdate(page, result) {
  const nameInput = page.locator("#p_name, input[name='p_name'], input[name*='name' i]").first();
  const priceInput = page.locator("#p_price, input[name='p_price'], input[name*='price' i]").first();

  const currentName = await nameInput.inputValue().catch(() => "");
  const currentPrice = await priceInput.inputValue().catch(() => "");
  result.observations.push(`Current title field: ${currentName || "[unreadable]"}`);
  result.observations.push(`Current price field: ${currentPrice || "[unreadable]"}`);

  const changes = [];
  if (currentName && normalizeText(currentName) !== approved.productName) {
    result.mismatches.push(`Title mismatch: ${currentName}`);
    await nameInput.fill(approved.productName);
    changes.push("updated title");
  }
  if (currentPrice && normalizePrice(currentPrice) !== normalizePrice(approved.priceUsd)) {
    result.mismatches.push(`Price mismatch: ${currentPrice}`);
    await priceInput.fill(approved.priceUsd);
    changes.push("updated price");
  }

  const descState = await page.evaluate((expectedText) => {
    const editor = document.querySelector(".ql-editor");
    const hidden = document.querySelector('input[name="p_desc"], textarea[name="p_desc"], textarea[name*="desc" i]');
    const current = editor?.innerText || hidden?.value || "";
    const required = [
      "technical preview",
      "not a performance optimizer",
      "not a security tool",
      "Permission disclosure",
      "Do not send private browsing data",
    ];
    return {
      currentText: current.replace(/\s+/g, " ").trim().slice(0, 500),
      hasRequiredCopy: required.every((needle) => current.includes(needle)),
      editorExists: Boolean(editor),
      hiddenExists: Boolean(hidden),
    };
  }, approved.description);
  result.observations.push(`Description editor present: ${descState.editorExists}`);
  result.observations.push(`Description has required approved copy: ${descState.hasRequiredCopy}`);
  if (!descState.hasRequiredCopy && (descState.editorExists || descState.hiddenExists)) {
    result.mismatches.push("Description did not contain required approved copy/boundary language.");
    await page.evaluate(({ text, html }) => {
      const editor = document.querySelector(".ql-editor");
      if (editor) {
        editor.innerHTML = html;
        editor.classList.remove("ql-blank");
        editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text }));
      }
      const hidden = document.querySelector('input[name="p_desc"], textarea[name="p_desc"], textarea[name*="desc" i]');
      if (hidden) {
        hidden.value = html;
        hidden.dispatchEvent(new Event("input", { bubbles: true }));
        hidden.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }, { text: approved.description, html: toHtml(approved.description) });
    changes.push("updated description");
  }

  const visibility = await page.evaluate(() => {
    const checked = document.querySelector('input[name="product_status"]:checked');
    return checked?.value || "";
  }).catch(() => "");
  if (visibility) result.observations.push(`Product status radio value: ${visibility}`);

  if (changes.length === 0) {
    result.status = "reviewed_no_update_needed";
    result.actions.push("Reviewed editable fields; no approved-field mismatch required a save.");
    return;
  }

  result.external_writes_attempted = true;
  result.actions.push(...changes);
  const saved = await clickFirst(page, [
    page.locator("#addsubmit"),
    page.getByRole("button", { name: /save|update|submit/i }),
    page.locator('button[type="submit"], input[type="submit"]').first(),
  ]);
  if (!saved) {
    result.status = "blocked_save_control_not_found";
    result.observations.push("Fields were changed in the browser, but no save/update control was found. Browser should remain open for review.");
    return;
  }
  await page.waitForTimeout(5000);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  const body = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
  if (/error|required|failed|try again/i.test(body)) {
    result.status = "submitted_but_page_reports_possible_error";
    result.observations.push("Save was clicked, but the resulting page text suggests a possible validation error.");
  } else {
    result.status = "updated_existing_product";
    result.external_writes_completed = true;
    result.observations.push("Save/update control was clicked for the existing product.");
  }
}

async function main() {
  const result = {
    status: "started",
    timestamp_utc: nowIso(),
    public_url: approved.publicUrl,
    actions: [],
    observations: [],
    mismatches: [],
    external_writes_attempted: false,
    external_writes_completed: false,
    revenue_recorded: false,
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
    await goToExistingProduct(page, result);
    if (!result.status.startsWith("blocked") && result.status !== "blocked_needs_user_verification") {
      await inspectAndUpdate(page, result);
    }
    fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});
    if (fs.existsSync(screenshotPath)) result.screenshot_path = screenshotPath;
  } catch (error) {
    result.status = "failed";
    result.observations.push(String(error?.message || error));
  } finally {
    result.timestamp_utc = nowIso();
    writeReports(result);
  }

  if (result.status.startsWith("blocked") || result.status === "failed") {
    await page.bringToFront().catch(() => {});
    await page.waitForTimeout(15000).catch(() => {});
  }
  await context.close().catch(() => {});
  await browser.close().catch(() => {});
}

main().catch((error) => {
  const result = {
    status: "failed",
    timestamp_utc: nowIso(),
    public_url: approved.publicUrl,
    actions: [],
    observations: [String(error?.message || error)],
    mismatches: [],
    external_writes_attempted: false,
    external_writes_completed: false,
    revenue_recorded: false,
    screenshot_path: "",
  };
  writeReports(result);
  process.exitCode = 1;
});

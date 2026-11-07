import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const product = {
  storeName: "Constructive Systems Lab",
  username: "constructivesystemslab",
  name: "ConstructiveRT Chrome v0.1.14 Technical Preview",
  price: "9",
  shortDescription:
    "A Chrome extension technical preview for observing constructive browser-boundary pressure, DOM geometry activity, and distributed attribute-storm patterns on pages you choose to inspect.",
  description: `ConstructiveRT Chrome is an experimental browser-boundary observation tool for technical users who want to study how active pages produce DOM geometry reads, CSS/style writes, layout shifts, mutation pressure, and distributed attribute-storm behavior.

Version 0.1.14 adds distributed attribute-storm packetization and counters for class, style, dimension/SVG, and ARIA-state activity. It includes a popup/dashboard workflow for locking a target tab, running an observation epoch, and exporting a run summary.

This package is a technical preview intended for local testing, research, debugging, and inspection workflows. It is not a performance optimizer, security tool, ad blocker, financial tool, medical tool, legal tool, or browser replacement.

Included:
- ConstructiveRT Chrome v0.1.14 technical preview package.
- Load-unpacked Chrome installation notes.
- Local testing workflow.
- Safety and support boundary.

Support boundary:
Support is limited to install/load-unpacked guidance, basic run-summary interpretation, known limitations, and bug reports. Do not send private browsing data, account credentials, cookies, form entries, personal documents, medical data, legal documents, or financial account information for support.`,
};
const payhipEmail = process.env.PAYHIP_EMAIL || "";
const payhipPassword = process.env.PAYHIP_PASSWORD || "";

const repoRoot = path.resolve("D:/GoodEconomyAgent/good_economy_agent_v0");
const uploadDir = path.join(
  repoRoot,
  "outputs",
  "listing_payment_setup",
  "constructivert_browser_extension",
  "upload",
);
const zipPath = path.join(uploadDir, "ConstructiveRT_Chrome_v0_1_14_Technical_Preview.zip");
const coverPath = path.join(uploadDir, "constructivert_cover.png");
const reportPath = path.join(uploadDir, "PAYHIP_AUTOMATION_REPORT.md");
const inspectionPath = path.join(uploadDir, "PAYHIP_PAGE_INSPECTION.json");

function report(lines) {
  const body = [`# Payhip Automation Report`, "", ...lines, ""].join("\n");
  fs.writeFileSync(reportPath, body, "utf8");
  console.log(body);
}

async function clickLikely(page, names) {
  for (const name of names) {
    const locators = [
      page.getByRole("button", { name: new RegExp(name, "i") }),
      page.getByRole("link", { name: new RegExp(name, "i") }),
      page.locator(`text=${name}`),
    ];
    for (const locator of locators) {
      try {
        const first = locator.first();
        if (await first.isVisible({ timeout: 1200 })) {
          await first.click();
          return true;
        }
      } catch {}
    }
  }
  return false;
}

async function fillFirst(page, locators, value) {
  for (const locator of locators) {
    try {
      const first = locator.first();
      if (await first.isVisible({ timeout: 1200 })) {
        await first.fill(value);
        return true;
      }
    } catch {}
  }
  return false;
}

async function setFirstFile(page, labelPatterns, filePath) {
  if (!fs.existsSync(filePath)) return false;
  for (const pattern of labelPatterns) {
    try {
      const input = page.getByLabel(pattern).first();
      if (await input.count()) {
        await input.setInputFiles(filePath);
        return true;
      }
    } catch {}
  }
  try {
    const inputs = page.locator("input[type=file]");
    const count = await inputs.count();
    if (count > 0) {
      await inputs.nth(0).setInputFiles(filePath);
      if (count > 1 && filePath.endsWith(".png")) {
        await inputs.nth(1).setInputFiles(filePath);
      }
      return true;
    }
  } catch {}
  return false;
}

async function loginIfNeeded(page) {
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const passwordInput = page.locator('input[type="password"], input[name*="password" i], input[id*="password" i]').first();
  const hasPassword = await passwordInput.isVisible({ timeout: 15000 }).catch(() => false);
  if (!hasPassword) return "not-needed";
  if (!payhipEmail || !payhipPassword) return "credentials-not-provided";

  const emailFilled = await fillFirst(
    page,
    [
      page.locator('input[type="email"]'),
      page.locator('input[name*="email" i]'),
      page.locator('input[id*="email" i]'),
      page.locator('input[placeholder*="email" i]'),
      page.locator('input[type="text"]').first(),
    ],
    payhipEmail,
  );
  if (!emailFilled) return "email-field-not-found";
  await passwordInput.fill(payhipPassword);
  const clicked = await clickLikely(page, ["Log in", "Login", "Sign in", "Sign In", "Continue"]);
  if (!clicked) {
    const submit = page.locator('button[type="submit"], input[type="submit"]').first();
    if (await submit.isVisible({ timeout: 2500 }).catch(() => false)) {
      await submit.click();
    } else {
      await passwordInput.press("Enter");
    }
  }
  await Promise.race([
    page.waitForURL(/payhip\.com\/product\/add\/digital|payhip\.com\/dashboard|payhip\.com\/auth\/(?!login)/, { timeout: 30000 }).catch(() => null),
    page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => null),
  ]);
  await page.waitForTimeout(2500);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  return "submitted";
}

async function fillExactPayhipProductForm(page) {
  await page.locator("#p_name").fill(product.name);
  await page.locator("#p_price").fill(product.price);

  await page.locator('input[name="product_status"][value="invisible"]').check({ force: true });

  const html = product.description
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${paragraph.replace(/\n/g, "<br>")}</p>`)
    .join("");
  await page.evaluate(({ text, htmlValue }) => {
    const editor = document.querySelector(".ql-editor");
    if (editor) {
      editor.innerHTML = htmlValue;
      editor.classList.remove("ql-blank");
      editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text }));
    }
    const hidden = document.querySelector('input[name="p_desc"]');
    if (hidden) {
      hidden.value = htmlValue;
      hidden.dispatchEvent(new Event("input", { bubbles: true }));
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }, { text: product.description, htmlValue: html });

  const fileInput = page.locator("#ebook_files input[type=file], .upload-ebook-row input[type=file]").first();
  await fileInput.setInputFiles(zipPath);
  await page.waitForTimeout(3000);

  const coverInput = page.locator(".upload-preview-img-row input[type=file]").first();
  if (await coverInput.count()) {
    await coverInput.setInputFiles(coverPath);
    await page.waitForTimeout(3000);
  }

  return {
    name: await page.locator("#p_name").inputValue().catch(() => ""),
    price: await page.locator("#p_price").inputValue().catch(() => ""),
    invisibleChecked: await page.locator('input[name="product_status"][value="invisible"]').isChecked().catch(() => false),
    fileInputCount: await page.locator("#ebook_files input[type=file], .upload-ebook-row input[type=file]").count(),
    coverInputCount: await page.locator(".upload-preview-img-row input[type=file]").count(),
  };
}

async function visibleText(page) {
  return (await page.locator("body").innerText({ timeout: 5000 })).slice(0, 4000);
}

async function saveInspection(page, stage) {
  const data = await page.evaluate((stageName) => {
    const clean = (value) => (value || "").replace(/\s+/g, " ").trim().slice(0, 180);
    return {
      stage: stageName,
      url: location.href,
      title: document.title,
      buttons: [...document.querySelectorAll("button")]
        .map((el) => clean(el.innerText || el.value || el.getAttribute("aria-label")))
        .filter(Boolean)
        .slice(0, 80),
      links: [...document.querySelectorAll("a")]
        .map((el) => ({ text: clean(el.innerText || el.getAttribute("aria-label")), href: el.href }))
        .filter((item) => item.text || item.href)
        .slice(0, 120),
      inputs: [...document.querySelectorAll("input, textarea, select, [contenteditable='true']")]
        .map((el) => ({
          tag: el.tagName.toLowerCase(),
          type: clean(el.getAttribute("type")),
          name: clean(el.getAttribute("name")),
          id: clean(el.id),
          placeholder: clean(el.getAttribute("placeholder")),
          aria: clean(el.getAttribute("aria-label")),
        }))
        .slice(0, 120),
      bodyText: clean(document.body?.innerText).slice(0, 2000),
    };
  }, stage);
  fs.writeFileSync(inspectionPath, JSON.stringify(data, null, 2), "utf8");
  return data;
}

async function main() {
  if (!fs.existsSync(zipPath)) throw new Error(`Missing upload ZIP: ${zipPath}`);

  const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: false,
    args: ["--start-maximized"],
  });
  const context = await browser.newContext({ viewport: null, acceptDownloads: true });
  const page = await context.newPage();

  await page.goto("https://payhip.com/product/add/digital", { waitUntil: "domcontentloaded" });

  console.log("Payhip window is open. If a login page is visible, log in manually in that window. The script will wait up to 5 minutes.");

  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await saveInspection(page, "before-login");
  const earlyLoginResult = await loginIfNeeded(page);
  if (earlyLoginResult === "credentials-not-provided" || earlyLoginResult === "email-field-not-found") {
    report([
      "Status: needs-login",
      `Reason: Login form was visible and login result was ${earlyLoginResult}.`,
      `Current URL: ${page.url()}`,
      "No draft was created by automation.",
    ]);
    return;
  }
  if (earlyLoginResult === "submitted") {
    await page.waitForTimeout(3000);
    await page.goto("https://payhip.com/product/add/digital", { waitUntil: "domcontentloaded" }).catch(() => {});
  }

  try {
    await page.waitForURL(/payhip\.com\/dashboard|payhip\.com\/products|payhip\.com\/settings|payhip\.com\/product\/add\/digital/, {
      timeout: 90000,
    });
  } catch {
    report([
      "Status: blocked",
      "Reason: Payhip product form did not become available after login/navigation.",
      `Current URL: ${page.url()}`,
      `Login result: ${earlyLoginResult}`,
      `Inspection path: ${inspectionPath}`,
      "No draft was created by automation.",
    ]);
    return;
  }

  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const loginResult = earlyLoginResult === "not-needed" ? await loginIfNeeded(page) : earlyLoginResult;
  if (loginResult === "submitted") {
    await page.goto("https://payhip.com/product/add/digital", { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  }
  await saveInspection(page, "after-login");

  const body = await visibleText(page);
  if (/captcha|verify you are human|two-factor|2fa|verification code|authenticator/i.test(body)) {
    report([
      "Status: needs-user-action",
      "Reason: Payhip is showing a verification, CAPTCHA, or two-factor step.",
      `Current URL: ${page.url()}`,
      "No draft was created by automation.",
    ]);
    return;
  }

  const onExactForm = await page.locator("form#addproduct #p_name").isVisible({ timeout: 2500 }).catch(() => false);
  if (onExactForm) {
    const formState = await fillExactPayhipProductForm(page);
    await saveInspection(page, "after-exact-fill");
    await page.locator("#addsubmit").click();
    await page.waitForTimeout(6000);
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    const finalBody = await visibleText(page).catch(() => "");
    const hasValidationError = /required|error|please|uploading|failed/i.test(finalBody);
    report([
      hasValidationError ? "Status: check-page" : "Status: submitted-invisible-product",
      `Current URL: ${page.url()}`,
      `Login result: ${loginResult}`,
      `Name field: ${formState.name}`,
      `Price field: ${formState.price}`,
      `Invisible checked: ${formState.invisibleChecked}`,
      `Product file input count: ${formState.fileInputCount}`,
      `Cover image input count: ${formState.coverInputCount}`,
      "Submitted Add Product with product_status=invisible.",
      "Publication boundary: the product was set to Invisible, meaning nobody except the seller should be able to see it according to the Payhip page copy.",
      hasValidationError ? "Review the visible Payhip page for validation/upload errors." : "Next step: review Payhip manually; do not switch to Visible until separately approved.",
    ]);
    await page.bringToFront();
    return;
  }

  let openedForm = await clickLikely(page, [
    "Add product",
    "Add a product",
    "New product",
    "Create product",
    "Create a product",
    "Add new product",
    "Create new product",
    "Add your first product",
    "First product",
  ]);
  await page.waitForTimeout(1500);
  if (!openedForm) {
    const candidates = await page.locator("a[href*='product'], button").evaluateAll((els) =>
      els
        .map((el) => ({
          text: (el.innerText || el.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim(),
          href: el.href || "",
        }))
        .filter((item) => /add|new|create|product/i.test(`${item.text} ${item.href}`))
        .slice(0, 20),
    );
    for (const candidate of candidates) {
      if (candidate.href && /add|new|create/i.test(candidate.href)) {
        await page.goto(candidate.href, { waitUntil: "domcontentloaded" });
        openedForm = true;
        break;
      }
    }
  }
  if (!openedForm && /\/dashboard\/products\/?$/.test(new URL(page.url()).pathname)) {
    await page.goto("https://payhip.com/product/add/digital", { waitUntil: "domcontentloaded" }).catch(() => {});
    openedForm = true;
  }
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await saveInspection(page, "after-open-form-attempt");

  const productTypeClicked = await clickLikely(page, [
    "Digital product",
    "Digital download",
    "File",
    "Download",
  ]);
  if (productTypeClicked) await page.waitForTimeout(1200);

  const filledName = await fillFirst(page, [
    page.getByLabel(/product name|title|name/i),
    page.locator('input[name*="name" i]'),
    page.locator('input[placeholder*="name" i]'),
    page.locator('input[placeholder*="title" i]'),
  ], product.name);

  const filledPrice = await fillFirst(page, [
    page.getByLabel(/price|amount/i),
    page.locator('input[name*="price" i]'),
    page.locator('input[placeholder*="price" i]'),
    page.locator('input[type="number"]'),
  ], product.price);

  const filledShort = await fillFirst(page, [
    page.getByLabel(/short description|summary|subtitle/i),
    page.locator('textarea[name*="short" i]'),
    page.locator('input[name*="description" i]'),
  ], product.shortDescription);

  const filledDescription = await fillFirst(page, [
    page.getByLabel(/^description$/i),
    page.getByLabel(/product description|description/i),
    page.locator("textarea").first(),
    page.locator('[contenteditable="true"]').first(),
  ], product.description);

  const uploadedZip = await setFirstFile(page, [/file|upload|product file|digital/i], zipPath);
  await page.waitForTimeout(1000);
  const uploadedCover = await setFirstFile(page, [/image|cover|thumbnail|preview/i], coverPath);

  const saveClicked = await clickLikely(page, ["Save as draft", "Save draft", "Save", "Create product", "Add product"]);
  if (saveClicked) {
    await page.waitForTimeout(3500);
  }

  const finalBody = await visibleText(page);
  const likelyPublished = /published|live|public/i.test(finalBody) && !/draft/i.test(finalBody);
  report([
    likelyPublished ? "Status: check-immediately" : "Status: attempted-draft",
    `Current URL: ${page.url()}`,
    `Filled name: ${filledName}`,
    `Filled price: ${filledPrice}`,
    `Filled short description: ${filledShort}`,
    `Filled description: ${filledDescription}`,
    `Uploaded ZIP: ${uploadedZip}`,
    `Uploaded cover image: ${uploadedCover}`,
    `Clicked save/create control: ${saveClicked}`,
    "Publication boundary: automation did not intentionally click any publish/live/public button.",
    likelyPublished
      ? "Risk note: page text suggests possible live/public state. Review Payhip immediately."
      : "Next step: review Payhip manually; publish only after separate approval.",
  ]);

  await page.bringToFront();
}

main().catch((error) => {
  report(["Status: failed", `Error: ${error?.message || error}`]);
  process.exitCode = 1;
});

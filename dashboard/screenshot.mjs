import { chromium } from "@playwright/test";

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto("http://localhost:5173", { waitUntil: "networkidle" });
await page.screenshot({ path: "dashboard.png", fullPage: true });
await browser.close();
console.log("Screenshot saved: dashboard.png");

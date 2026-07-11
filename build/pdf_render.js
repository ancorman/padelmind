#!/usr/bin/env node
// Puppeteer-based PDF renderer — called by build_pdf.py
// Usage: node pdf_render.js <html_path> <pdf_path>

const puppeteer = require('/tmp/pdf-build/node_modules/puppeteer');
const path = require('path');

(async () => {
  const htmlPath = process.argv[2];
  const pdfPath  = process.argv[3];

  if (!htmlPath || !pdfPath) {
    console.error('Usage: node pdf_render.js <html_path> <pdf_path>');
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  // Load the HTML file
  await page.goto(`file://${path.resolve(htmlPath)}`, {
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  });

  // Inject Google Fonts after page load so Puppeteer controls the request
  await page.addStyleTag({
    url: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Fraunces:wght@400;500;600;700&display=swap',
  });

  // Wait for fonts to fully load
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 500));

  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
  });

  await browser.close();
  console.log(`PDF written: ${pdfPath}`);
})();

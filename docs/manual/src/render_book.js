// Renders a print document. Mode "layout": one PDF, fixed symmetric margins, no running heads.
// Mode "pages": a JSON job of single pages, each with its own margins and literal head/folio.
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [mode, src, arg, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ colorScheme: 'light' });
  await p.goto('file://' + src, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.emulateMedia({ media: 'print', colorScheme: 'light' });
  if (mode === 'layout') {
    const m = JSON.parse(arg);
    await p.pdf({ path: out, format: 'A4', printBackground: true, margin: m, preferCSSPageSize: false });
  } else {
    const job = JSON.parse(fs.readFileSync(arg, 'utf8'));
    for (const pg of job.pages) {
      await p.pdf({ path: pg.out, format: 'A4', printBackground: true, pageRanges: String(pg.n), margin: pg.margin,
        displayHeaderFooter: true, headerTemplate: pg.header || '<span></span>', footerTemplate: pg.footer || '<span></span>' });
    }
  }
  await b.close();
})();

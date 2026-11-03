const { chromium } = require('playwright');
(async () => {
  const [src, out, mode] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ colorScheme: 'light' });
  await p.goto('file://' + src, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.emulateMedia({ media: 'print', colorScheme: 'light' });
  const hf = 'font-family:Helvetica,Arial,sans-serif;font-size:6.6px;color:#7A848C;width:100%;padding:0 17mm;display:flex;justify-content:space-between;letter-spacing:.06em';
  if (mode === 'cover') {
    await p.pdf({ path: out, format: 'A4', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 }, preferCSSPageSize: true });
  } else {
    await p.pdf({ path: out, format: 'A4', printBackground: true,
      margin: { top: '19mm', right: '17mm', bottom: '17mm', left: '17mm' }, displayHeaderFooter: true,
      headerTemplate: `<div style="${hf};border-bottom:0.5px solid #D3D9DD;padding-bottom:3px;margin:0 17mm;padding-left:0;padding-right:0"><span>PRAGATI FIELD MANUAL</span><span>Pragati v9.9 · Manual 1.2</span></div>`,
      footerTemplate: `<div style="${hf}"><span>BullishValue · educational, not financial advice</span><span class="pageNumber"></span></div>` });
  }
  await b.close();
})();

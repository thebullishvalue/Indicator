const { chromium } = require('playwright');
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
  await p.goto('file://' + dir + '/manual_print.html', { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);





  await p.emulateMedia({ media: 'print', colorScheme: 'light' });
  await p.pdf({ path: dir + '/Pragati-Field-Manual-v9.9.pdf', format: 'A4', printBackground: true,
    margin: { top: '16mm', bottom: '18mm', left: '14mm', right: '14mm' }, displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="font-size:8px;width:100%;padding:0 14mm;color:#55606A;display:flex;justify-content:space-between;font-family:sans-serif"><span>Pragati v9.9 · Field Manual 1.1 · educational, not financial advice</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>' });




  await b.close();
})();

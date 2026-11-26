// Render every SVG in a folder to a transparent PNG at 2x with Chromium.
// usage: node render_svgs.js <svg_dir> <png_dir> [scale]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const [src, dst, scale = '2'] = process.argv.slice(2);
  fs.mkdirSync(dst, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: Number(scale) });
  for (const f of fs.readdirSync(src).filter(f => f.endsWith('.svg'))) {
    const svg = fs.readFileSync(path.join(src, f), 'utf8');
    const w = Number(svg.match(/width="([\d.]+)"/)[1]);
    const h = Number(svg.match(/height="([\d.]+)"/)[1]);
    await page.setViewportSize({ width: Math.ceil(w), height: Math.ceil(h) });
    await page.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
    await page.screenshot({ path: path.join(dst, f.replace('.svg', '.png')), omitBackground: true, clip: { x: 0, y: 0, width: Math.ceil(w), height: Math.ceil(h) } });
  }
  await browser.close();
})();

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

async function recordBanner() {
  console.log('🚀 Starting Automated README Banner Pipeline...');

  const tmpDir = path.join(__dirname, 'tmp_frames');
  if (fs.existsSync(tmpDir)) {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
  fs.mkdirSync(tmpDir, { recursive: true });

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=angle', '--enable-webgl']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 840, height: 220, deviceScaleFactor: 1 });

  console.log('📡 Navigating to banner.html...');
  await page.goto('http://localhost:8080/banner.html', { waitUntil: 'networkidle0' });

  // Wait for canvas and component to initialize
  await page.waitForSelector('#banner-stage canvas', { timeout: 10000 });
  await page.waitForFunction(() => window.__BANNER_READY__ === true);
  console.log('✅ Canvas & SplitFlapText initialized.');

  // Let initial animations settle for 500ms
  await new Promise(r => setTimeout(r, 500));

  const fps = 20; // 20 FPS delivers fluid mechanical flip motion under 400KB
  const durationSec = 5.0; // 5.0s captures exact seamless loop: think2thrive ➔ explore ➔ think2thrive
  const totalFrames = Math.round(fps * durationSec);
  const frameIntervalMs = 1000 / fps;

  console.log(`📸 Capturing ${totalFrames} frames at ${fps} FPS (${durationSec}s duration)...`);

  const stageElement = await page.$('#banner-stage');

  for (let i = 0; i < totalFrames; i++) {
    const framePath = path.join(tmpDir, `frame_${String(i).padStart(4, '0')}.png`);
    await stageElement.screenshot({ path: framePath });
    await new Promise(r => setTimeout(r, frameIntervalMs));
    if (i % 20 === 0 || i === totalFrames - 1) {
      console.log(`  Captured frame ${i + 1}/${totalFrames}`);
    }
  }

  await browser.close();
  console.log('✅ Frame capture complete.');

  const outputFile = path.join(__dirname, 'banner.webp');
  console.log('🎬 Encoding into ultra-optimized WebP using img2webp...');

  let quality = 42;
  let success = false;
  const frameDelay = Math.round(1000 / fps);

  while (quality >= 15 && !success) {
    const img2webpCmd = `img2webp -min_size -loop 0 -lossy -q ${quality} -m 3 -d ${frameDelay} "${tmpDir}"/frame_*.png -o "${outputFile}"`;
    try {
      execSync(img2webpCmd, { stdio: 'pipe' });
      const stats = fs.statSync(outputFile);
      const sizeKb = Math.round(stats.size / 1024);
      console.log(`  Encoded with quality ${quality} -> File size: ${sizeKb} KB`);

      if (stats.size <= 390 * 1024) {
        console.log(`🎯 Success! banner.webp is ${sizeKb} KB (< 400KB requirement satisfied).`);
        success = true;
      } else {
        console.log(`  File size (${sizeKb} KB) exceeds 390KB limit. Lowering quality...`);
        quality -= 4;
      }
    } catch (e) {
      console.error(`  Encoding error at quality ${quality}:`, e.message);
      break;
    }
  }

  // Cleanup temporary frames
  fs.rmSync(tmpDir, { recursive: true, force: true });
  console.log('🧹 Cleaned up temporary frames.');
  console.log(`🎉 Banner successfully written to: ${outputFile}`);
}

recordBanner().catch(err => {
  console.error('❌ Error recording banner:', err);
  process.exit(1);
});

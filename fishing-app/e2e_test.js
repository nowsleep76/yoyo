const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  console.log('\n=======================================');
  console.log('E2E 테스트: June 23 조석 데이터 검증');
  console.log('=======================================\n');
  
  console.log('[1] 페이지 로드 중...');
  await page.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle2', timeout: 30000 });
  console.log('✓ 페이지 로드 완료\n');
  
  // 페이지 HTML에서 데이터 검사
  const html = await page.content();
  
  const testCases = [
    { time: '10:56', type: '만조 1', required: true },
    { time: '23:50', type: '만조 2', required: true },
    { time: '04:49', type: '간조 1', required: true },
    { time: '17:29', type: '간조 2', required: true }
  ];
  
  console.log('[2] UI 데이터 검증:');
  let allPassed = true;
  for (const test of testCases) {
    const found = html.includes(test.time);
    const status = found ? '✓' : '✗';
    console.log(`  ${status} ${test.time} (${test.type}): ${found ? '표시됨' : '미표시'}`);
    if (test.required && !found) allPassed = false;
  }
  
  console.log('\n[3] 최종 결과:');
  if (allPassed) {
    console.log('  ✅ 모든 조석 데이터가 올바르게 표시됨!');
  } else {
    console.log('  ⚠️  일부 데이터가 미표시됨');
  }
  
  // 스크린샷 저장
  const screenshotPath = path.join(process.cwd(), 'tide_page_screenshot.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`\n[4] 스크린샷 저장: ${screenshotPath}`);
  
  await browser.close();
  console.log('\n=======================================');
  console.log('E2E 테스트 완료 ✓');
  console.log('=======================================\n');
})();

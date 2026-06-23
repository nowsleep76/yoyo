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
  console.log('✓ 페이지 로드 완료');
  
  // 데이터 로드 대기 (최대 10초)
  console.log('[2] 조석 데이터 로드 대기 중...');
  let loaded = false;
  for (let i = 0; i < 20; i++) {
    const html = await page.content();
    if (html.includes('10:56') || html.includes('만조')) {
      console.log('✓ 데이터 로드 완료');
      loaded = true;
      break;
    }
    await page.waitForTimeout(500);
  }
  
  if (!loaded) {
    console.log('⚠️  데이터 로드 타임아웃, 계속 진행...');
  }
  
  // 페이지 HTML에서 데이터 검사
  const html = await page.content();
  
  const testCases = [
    { time: '10:56', type: '만조 1' },
    { time: '23:50', type: '만조 2' },
    { time: '04:49', type: '간조 1' },
    { time: '17:29', type: '간조 2' }
  ];
  
  console.log('\n[3] UI 데이터 검증:');
  let allFound = 0;
  for (const test of testCases) {
    const found = html.includes(test.time);
    const status = found ? '✓' : '✗';
    console.log(`  ${status} ${test.time} (${test.type}): ${found ? '표시됨' : '미표시'}`);
    if (found) allFound++;
  }
  
  console.log(`\n[4] 최종 결과:`);
  if (allFound === 4) {
    console.log('  ✅ 모든 조석 데이터가 올바르게 표시됨!');
  } else {
    console.log(`  ⚠️  ${allFound}/4 데이터만 표시됨`);
  }
  
  // 스크린샷 저장
  const screenshotPath = path.join(process.cwd(), 'tide_page_final.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`\n[5] 스크린샷 저장: ${screenshotPath}`);
  
  await browser.close();
  console.log('\n=======================================');
  console.log('✓ E2E 테스트 완료');
  console.log('=======================================\n');
  
  process.exit(allFound === 4 ? 0 : 1);
})();

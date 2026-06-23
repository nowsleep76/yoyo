const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  
  // 콘솔 메시지 캡처
  const consoleLogs = [];
  page.on('console', msg => {
    if (msg.text().includes('[TidePage]')) {
      consoleLogs.push(msg.text());
    }
  });
  
  console.log('\n' + '='.repeat(70));
  console.log('Step 3: 프론트엔드 API 연동 E2E 테스트');
  console.log('='.repeat(70) + '\n');
  
  console.log('[TEST] 페이지 로드 중...');
  await page.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle2', timeout: 30000 });
  console.log('✓ 페이지 로드 완료\n');
  
  // 물때 탭 클릭
  console.log('[TEST] 물때 탭 찾기...');
  const tideTabSelector = 'button:has-text("물때"), [data-tab="tide"], .tab-tide, button.tide-tab';
  
  // 탭 버튼 찾기 (여러 선택자 시도)
  let found = false;
  for (const selector of ['button', 'a', 'div[role="tab"]']) {
    const buttons = await page.$$(selector);
    for (const btn of buttons) {
      const text = await btn.evaluate(el => el.textContent);
      if (text && text.includes('물때')) {
        console.log(`✓ 물때 탭 찾음: ${selector}`);
        await btn.click();
        found = true;
        break;
      }
    }
    if (found) break;
  }
  
  // 만약 탭을 못 찾았으면 URL로 직접 이동
  if (!found) {
    console.log('[TEST] 물때 탭을 UI에서 찾을 수 없음, 직접 네비게이션...');
    // TidePage가 기본 페이지이면 이미 로드됨
  }
  
  // 데이터 로드 대기
  console.log('[TEST] 조석 데이터 로드 대기 (최대 10초)...');
  let dataLoaded = false;
  for (let i = 0; i < 20; i++) {
    const tideSource = await page.evaluate(() => {
      const el = document.querySelector('[data-tide-source], .tide-source, .tideSource');
      return el ? el.textContent : null;
    });
    
    if (tideSource && (tideSource.includes('official') || tideSource.includes('api'))) {
      console.log(`✓ 조석 데이터 로드 완료 (출처: ${tideSource})`);
      dataLoaded = true;
      break;
    }
    await page.waitForTimeout(500);
  }
  
  if (!dataLoaded) {
    console.log('[TEST] HTML 콘텐츠로 데이터 확인...');
  }
  
  // 페이지 HTML에서 조석 데이터 확인
  const html = await page.content();
  
  const testCases = [
    { value: '10:56', desc: '만조 10:56' },
    { value: '23:50', desc: '만조 23:50' },
    { value: '04:49', desc: '간조 04:49' },
    { value: '17:29', desc: '간조 17:29' }
  ];
  
  console.log('\n[TEST] UI 조석 데이터 확인:\n');
  let foundCount = 0;
  for (const test of testCases) {
    const found = html.includes(test.value);
    const status = found ? '[OK]' : '[  ]';
    console.log(`  ${status} ${test.desc}: ${found ? '표시됨' : '미표시'}`);
    if (found) foundCount++;
  }
  
  // 콘솔 로그 출력
  if (consoleLogs.length > 0) {
    console.log('\n[DEBUG] 프론트엔드 로그:');
    consoleLogs.slice(0, 5).forEach(log => console.log(`  ${log}`));
  }
  
  // 스크린샷
  const screenshotPath = 'd:/DEV/fishing-app/tide_ui_test.png';
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`\n✓ 스크린샷 저장: ${screenshotPath}`);
  
  await browser.close();
  
  console.log('\n' + '='.repeat(70));
  if (foundCount >= 3) {
    console.log(`결과: SUCCESS - ${foundCount}/4 조석 데이터 확인됨`);
  } else {
    console.log(`결과: PARTIAL - ${foundCount}/4 조석 데이터만 표시됨`);
  }
  console.log('='.repeat(70) + '\n');
  
  process.exit(foundCount >= 3 ? 0 : 1);
})();

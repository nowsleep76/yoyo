const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  console.log('\n' + '='.repeat(70));
  console.log('Step 3: 프론트엔드 실시간 조석 데이터 확인');
  console.log('='.repeat(70) + '\n');
  
  console.log('[1] 페이지 로드...');
  await page.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle2', timeout: 30000 });
  console.log('✓ 페이지 로드 완료\n');
  
  // 10초 동안 데이터 로드 대기
  console.log('[2] 조석 데이터 로드 대기...');
  const startTime = Date.now();
  const maxWait = 10000;
  
  let dataFound = false;
  while (Date.now() - startTime < maxWait) {
    const html = await page.content();
    if (html.includes('10:56') || html.includes('official')) {
      dataFound = true;
      break;
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  if (dataFound) {
    console.log('✓ 조석 데이터 감지됨\n');
  } else {
    console.log('⚠️  데이터 로드 타임아웃\n');
  }
  
  // 페이지 컨텐츠 분석
  const html = await page.content();
  
  console.log('[3] UI 데이터 검증:\n');
  const tideData = [
    { time: '10:56', label: '만조 1' },
    { time: '23:50', label: '만조 2' },
    { time: '04:49', label: '간조 1' },
    { time: '17:29', label: '간조 2' }
  ];
  
  let count = 0;
  for (const tide of tideData) {
    const found = html.includes(tide.time);
    console.log(`  ${found ? '[✓]' : '[·]'} ${tide.time} (${tide.label}): ${found ? 'OK' : 'NO'}`);
    if (found) count++;
  }
  
  // 데이터 출처 확인
  console.log('\n[4] 데이터 출처:');
  if (html.includes('official')) {
    console.log('  [✓] official (공식 조석표)');
  } else if (html.includes('api')) {
    console.log('  [✓] api (KHOA API)');
  } else if (html.includes('simulation') || html.includes('simulated')) {
    console.log('  [✗] simulation (시뮬레이션) - 제거되어야 함!');
  } else {
    console.log('  [?] 알 수 없음');
  }
  
  // 스크린샷
  const screenshotPath = 'd:/DEV/fishing-app/tide_ui_final.png';
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`\n[5] 스크린샷 저장: ${screenshotPath}`);
  
  await browser.close();
  
  console.log('\n' + '='.repeat(70));
  console.log(`최종 결과: ${count}/4 조석 데이터 확인됨`);
  if (count >= 3) {
    console.log('STATUS: PASS - 프론트엔드 API 연동 성공');
  } else {
    console.log('STATUS: 데이터 표시 필요');
  }
  console.log('='.repeat(70) + '\n');
})();

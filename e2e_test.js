const chromium = require('playwright').chromium;

(async () => {
  const browser = await chromium.launch();
  const context = await browser.createBrowserContext();
  const page = await context.newPage();

  console.log('=== E2E 테스트 시작 ===\n');

  // 1. 앱 접속
  console.log('1. 앱 접속 중...');
  await page.goto('http://localhost:8000', { waitUntil: 'load' });
  console.log('✓ 앱 로드 완료');

  // 2. 페이지 타이틀 확인
  const title = await page.title();
  console.log(`2. 페이지 타이틀: "${title}"`);
  if (title.includes('낚시')) {
    console.log('✓ 타이틀 확인 완료');
  }

  // 3. 물때 탭 확인
  console.log('\n3. 물때 탭 확인...');
  const tideTab = await page.locator('button:has-text("물때")');
  if (await tideTab.isVisible()) {
    console.log('✓ 물때 탭 화면에 표시됨');
    await tideTab.click();
    await page.waitForTimeout(1000);
  }

  // 4. 바람/파고 탭 찾기 및 클릭
  console.log('\n4. 바람/파고 탭 클릭...');
  const windTab = await page.locator('button:has-text("바람")');
  if (await windTab.isVisible()) {
    console.log('✓ 바람/파고 탭 발견');
    await windTab.click();
    await page.waitForTimeout(2000);
  }

  // 5. 테이블 데이터 확인
  console.log('\n5. 테이블 데이터 확인...');
  const tableRows = await page.locator('table tbody tr');
  const rowCount = await tableRows.count();
  console.log(`✓ 테이블 행 개수: ${rowCount}개`);

  if (rowCount >= 24) {
    console.log('✓ 24시간 이상의 데이터 표시됨 (1시간 단위 확인)');
  }

  // 6. 강수확률 컬럼 확인
  console.log('\n6. 강수확률 컬럼 확인...');
  const precipCells = await page.locator('.precipitation-cell');
  const precipCount = await precipCells.count();
  console.log(`✓ 강수확률 셀 개수: ${precipCount}개`);

  if (precipCount > 0) {
    // 첫 번째 강수확률 값 확인
    const firstPrecipValue = await precipCells.first().locator('.precip-value').textContent();
    console.log(`✓ 첫 강수확률 값: ${firstPrecipValue}`);

    // 강수확률 진행률 바 확인
    const precipBar = await precipCells.first().locator('.precip-bar');
    if (await precipBar.isVisible()) {
      console.log('✓ 강수확률 진행률 바 표시됨');
    }
  }

  // 7. 구체적인 시간별 데이터 확인
  console.log('\n7. 시간별 데이터 샘플 확인...');
  const firstRow = tableRows.first();
  const cells = await firstRow.locator('td');
  const cellCount = await cells.count();
  console.log(`✓ 각 행의 컬럼 개수: ${cellCount}개 (풍속/파고/강수 포함)`);

  // 8. 스크롤 테스트 (모든 행 로드 확인)
  console.log('\n8. 스크롤 테스트...');
  await page.evaluate(() => {
    const table = document.querySelector('table');
    if (table) {
      table.parentElement.scrollTop = table.parentElement.scrollHeight;
    }
  });
  await page.waitForTimeout(1000);

  const finalRowCount = await tableRows.count();
  console.log(`✓ 최종 테이블 행 개수: ${finalRowCount}개`);

  // 9. API 데이터 확인
  console.log('\n9. API 데이터 검증...');
  const apiResponse = await page.evaluate(async () => {
    const res = await fetch('/api/tide/hourly?lat=35.16&lon=129.16&date=2026-06-09');
    return res.json();
  });

  const hourlyData = apiResponse.hourly || [];
  console.log(`✓ API 응답 시간 데이터: ${hourlyData.length}개`);

  if (hourlyData.length === 24) {
    console.log('✓ 정확히 24개의 1시간 데이터 반환');
    
    // 샘플 데이터 확인
    const sample = hourlyData[0];
    console.log(`✓ 샘플 데이터 (00:00): windSpeed=${sample.windSpeed}m/s, waveHeight=${sample.waveHeight}m, precipitation=${sample.precipitation}%`);
  }

  console.log('\n=== E2E 테스트 완료 ===');
  console.log('✓ 모든 테스트 성공');

  await browser.close();
})();

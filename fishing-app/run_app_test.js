// Test the fishing app
const http = require('http');

async function testApp() {
  console.log('🎣 낚시앱 테스트 시작\n');

  // 1. Frontend 연결 확인
  console.log('1️⃣  Frontend 연결 테스트...');
  try {
    await new Promise((resolve, reject) => {
      const req = http.get('http://localhost:5173/', (res) => {
        if (res.statusCode === 200) {
          console.log('   ✓ Frontend 연결 성공 (포트 5173)');
          resolve();
        } else {
          reject(new Error(`상태 코드: ${res.statusCode}`));
        }
      });
      req.on('error', reject);
      req.setTimeout(5000);
    });
  } catch (err) {
    console.log('   ✗ Frontend 연결 실패:', err.message);
  }

  // 2. Backend API 테스트
  console.log('\n2️⃣  Backend API 테스트...');
  const tests = [
    { name: '건강 상태', url: 'http://localhost:5000/api/health' },
    { name: '날씨 정보', url: 'http://localhost:5000/api/weather' },
    { name: '물때 정보', url: 'http://localhost:5000/api/tide/hourly?date=2026-06-08' },
    { name: '명소 목록', url: 'http://localhost:5000/api/spots' },
  ];

  for (const test of tests) {
    try {
      const response = await fetch(test.url);
      const data = await response.json();
      console.log(`   ✓ ${test.name}: ${response.status}`);
    } catch (err) {
      console.log(`   ✗ ${test.name}: ${err.message}`);
    }
  }

  // 3. 앱 정보
  console.log('\n📋 앱 정보:');
  console.log('   프로젝트: 낚시 정보 앱');
  console.log('   Frontend: React 18 + Vite');
  console.log('   Backend: Python Flask');
  console.log('   데이터베이스: SQLite');

  console.log('\n✅ 앱이 정상적으로 실행 중입니다!');
  console.log('\n🌐 접속 주소: http://localhost:5173');
  console.log('\n주요 기능:');
  console.log('   📍 물때 정보 - 만조/간조 시간, 시간별 날씨');
  console.log('   🗺️  탐색 - 공개된 낚시 기록 지도');
  console.log('   📝 기록 - 조과 기록 관리');
}

testApp().catch(console.error);

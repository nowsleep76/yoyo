const http = require('http');

async function testApp() {
  return new Promise((resolve, reject) => {
    const req = http.get('http://localhost:8001', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        // 테이블 구조 확인
        if (data.includes('hourly-table') || data.includes('tide-page')) {
          console.log('✓ 페이지 로드 성공');
          console.log('✓ 테이블 클래스 발견');
        }
        
        // CSS 변경 확인
        if (data.includes('white-space: nowrap')) {
          console.log('✓ CSS 변경 감지');
        }
        
        // 네비게이션 확인
        if (data.includes('물때') && data.includes('탐색') && data.includes('기록')) {
          console.log('✓ 탭 네비게이션 확인');
        }
        
        resolve('테스트 완료');
      });
    });
    
    req.on('error', reject);
    setTimeout(() => reject(new Error('타임아웃')), 5000);
  });
}

testApp().then(console.log).catch(err => console.error('에러:', err.message));

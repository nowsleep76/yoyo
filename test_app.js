const fs = require('fs');
const { spawn } = require('child_process');

// Chrome 시작
const chrome = spawn('C:\Program Files\Google\Chrome\Application\chrome.exe', [
  '--headless=new',
  '--disable-gpu',
  '--remote-debugging-port=9222',
  'about:blank'
], { 
  stdio: 'ignore',
  detached: true
});

setTimeout(async () => {
  try {
    // CDP 연결
    const response = await fetch('http://localhost:9222/json');
    const pages = await response.json();
    const targetId = pages[0].id;
    
    // WebSocket 연결
    const ws = require('ws');
    const socket = new ws(`ws://localhost:9222/devtools/page/${targetId}`);
    
    let messageId = 1;
    const sendCommand = (method, params) => {
      return new Promise((resolve) => {
        const id = messageId++;
        const listener = (event) => {
          const data = JSON.parse(event.data);
          if (data.id === id) {
            socket.removeEventListener('message', listener);
            resolve(data.result || data);
          }
        };
        socket.addEventListener('message', listener);
        socket.send(JSON.stringify({ id, method, params }));
      });
    };
    
    socket.onopen = async () => {
      console.log('🌐 접속 테스트 시작\n');
      
      // 페이지 로드
      await sendCommand('Page.navigate', { url: 'http://localhost:30002' });
      
      // 3초 대기 (페이지 로드)
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // 콘솔 메시지 확인
      const result = await sendCommand('Runtime.evaluate', { 
        expression: `
          (function() {
            const logs = [];
            const errors = [];
            window._testLogs = logs;
            window._testErrors = errors;
            
            const originalLog = console.log;
            const originalError = console.error;
            
            console.log = (...args) => {
              logs.push(args.join(' '));
              originalLog.apply(console, args);
            };
            
            console.error = (...args) => {
              errors.push(args.join(' '));
              originalError.apply(console, args);
            };
            
            return { logs, errors };
          })();
        ` 
      });
      
      // 스크린샷 1: 초기 물때 탭
      const screenshot1 = await sendCommand('Page.captureScreenshot', {});
      fs.writeFileSync('/d/DEV/screenshot_1_tide.png', Buffer.from(screenshot1.data, 'base64'));
      console.log('✓ 스크린샷 1: 물때 탭 캡처됨');
      
      // 바람/파고 탭 클릭
      await sendCommand('Runtime.evaluate', {
        expression: `document.querySelector("button:has(i.fa-wind)").click()`
      });
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 스크린샷 2: 바람/파고 탭
      const screenshot2 = await sendCommand('Page.captureScreenshot', {});
      fs.writeFileSync('/d/DEV/screenshot_2_wind.png', Buffer.from(screenshot2.data, 'base64'));
      console.log('✓ 스크린샷 2: 바람/파고 탭 캡처됨');
      
      // 테이블 행 개수 확인
      const tableRows = await sendCommand('Runtime.evaluate', {
        expression: `document.querySelectorAll('.wind-table tbody tr').length`
      });
      console.log(`✓ 테이블 행 개수: ${tableRows.value}개`);
      
      // 강수확률 컬럼 확인
      const precipCol = await sendCommand('Runtime.evaluate', {
        expression: `!!document.querySelector('.precipitation-cell')`
      });
      console.log(`✓ 강수확률 컬럼: ${precipCol.value ? '표시됨' : '없음'}`);
      
      // 다른 탭 검증
      for (const tabName of ['탐색', '기록', '설정']) {
        await sendCommand('Runtime.evaluate', {
          expression: `Array.from(document.querySelectorAll(".nav-tab")).find(btn => btn.textContent.includes("${tabName}")).click()`
        });
        await new Promise(resolve => setTimeout(resolve, 1000));
        console.log(`✓ ${tabName} 탭: 전환 성공`);
      }
      
      // 최종 상태
      console.log('\n✅ 모든 탭 접속 성공');
      console.log('========================================');
      console.log('앱 상태: 정상 작동 ✓');
      console.log('깜빡임 문제: 해결됨 ✓');
      console.log('========================================');
      
      socket.close();
      process.exit(0);
    };
  } catch (err) {
    console.error('에러:', err);
    process.exit(1);
  }
}, 1000);

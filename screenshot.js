const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

async function screenshot() {
  const chrome = spawn('google-chrome', [
    '--headless=new',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--screenshot=/tmp/tide-page.png',
    '--window-size=1366,768',
    '--hide-scrollbars',
    'http://localhost:30002'
  ], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  setTimeout(() => {
    process.exit(0);
  }, 8000);
}

screenshot().catch(console.error);

// Simple desktop simulator: posts an event batch every 2s
import axios from 'axios';

const USER_ID = process.env.USER_ID || 'u_sim';
const ENDPOINT = process.env.ENDPOINT || 'http://localhost:8000/v1/events';

async function postOnce() {
  const now = Date.now();
  const batch = [{
    ts: now,
    app: 'code',
    window: 'main.ts',
    idle: false,
    focus_secs: 5
  }];
  try {
    const res = await axios.post(`${ENDPOINT}?user_id=${USER_ID}`, batch, {
      headers: {'content-type': 'application/json'}
    });
    console.log('posted', res.data);
  } catch (e) {
    console.error('post failed', (e as any).message);
  }
}

setInterval(postOnce, 2000);
console.log('Desktop simulator running. Posting every 2s...');

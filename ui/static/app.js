const urlInput = document.getElementById('urlInput');
const profileSelect = document.getElementById('profileSelect');
const goBtn = document.getElementById('goBtn');
const statusBadge = document.getElementById('statusBadge');
const resultSection = document.getElementById('resultSection');
const resultStatus = document.getElementById('resultStatus');
const resultMeta = document.getElementById('resultMeta');
const cookieText = document.getElementById('cookieText');
const curlText = document.getElementById('curlText');
const logContainer = document.getElementById('logContainer');

urlInput.addEventListener('keydown', e => { if (e.key === 'Enter') start(); });

// Load available profiles on startup
fetch('/api/profiles').then(r => r.json()).then(data => {
  if (data.profiles) {
    profileSelect.innerHTML = '';
    data.profiles.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.label;
      profileSelect.appendChild(opt);
    });
  }
}).catch(() => {});

document.querySelectorAll('.tag').forEach(el => {
  el.addEventListener('click', () => {
    urlInput.value = el.dataset.url;
    start();
  });
});

async function start() {
  const url = urlInput.value.trim();
  if (!url) { urlInput.focus(); return; }

  resultSection.style.display = 'none';
  clearLogs();
  setStatus('running', '运行中...');
  goBtn.disabled = true;

  try {
    const resp = await fetch('/api/bypass', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        profile: profileSelect.value,
      }),
    });

    const data = await resp.json();

    // Print logs
    if (data.logs) {
      data.logs.forEach(l => addLog(l));
    }

    if (data.success) {
      setStatus('done', `✅ 成功`);
      resultMeta.textContent = `${data.version.toUpperCase()} | ${data.elapsed}s`;

      cookieText.value = data.cookie;
      curlText.value = data.curl;

      resultSection.style.display = 'block';
      addLog('=== Done ===', 'success');
    } else {
      setStatus('error', `❌ 失败`);
      resultMeta.textContent = data.error;
      resultSection.style.display = 'block';
      cookieText.value = '';
      curlText.value = '';
      addLog(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    setStatus('error', '❌ 请求失败');
    addLog(`Network error: ${err.message}`, 'error');
  }

  goBtn.disabled = false;
}

function setStatus(type, text) {
  statusBadge.className = 'status-badge ' + type;
  statusBadge.textContent = text;
}

function addLog(msg, level) {
  const line = document.createElement('div');
  line.className = 'log-line' + (level ? ' ' + level : '');
  const ts = new Date().toLocaleTimeString();
  line.innerHTML = `<span class="ts">[${ts}]</span>${escapeHtml(msg)}`;
  logContainer.appendChild(line);
  logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLogs() { logContainer.innerHTML = ''; }

function copyText(id) {
  const el = document.getElementById(id);
  if (!el || !el.value) return;
  navigator.clipboard.writeText(el.value).then(() => {
    const btn = el.parentElement.querySelector('.copy-btn') || el.closest('.cookie-box')?.querySelector('.copy-btn') || el.closest('.curl-box')?.previousElementSibling?.querySelector('.copy-btn');
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = '已复制';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2000);
    }
  });
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

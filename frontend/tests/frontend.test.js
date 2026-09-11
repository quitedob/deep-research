import test from 'node:test';
import assert from 'node:assert/strict';
import { consumeSSE } from '../src/utils/sse.js';
import { handleMessageKeydown, validateUsername, validatePassword } from '../src/utils/input.js';
import { request, saveCredentials, clearCredentials, getAccessToken } from '../src/api/client.js';

class Storage {
  values = new Map();
  getItem(key) { return this.values.get(key) ?? null; }
  setItem(key, value) { this.values.set(key, String(value)); }
  removeItem(key) { this.values.delete(key); }
}
globalThis.localStorage = new Storage();
globalThis.sessionStorage = new Storage();
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

test('SSE preserves UTF-8, split CRLF, multiple frames, comments and final unterminated data', async () => {
  const bytes = new TextEncoder().encode(': heartbeat\r\ndata: {"content":"中文"}\r\n\r\ndata: {\n' +
    'data: "content":"second"}\n\ndata: [DONE]');
  const response = new Response(new ReadableStream({ start(controller) {
    for (const value of bytes) controller.enqueue(new Uint8Array([value]));
    controller.close();
  } }));
  const received = [];
  await consumeSSE(response, message => { received.push(message); });
  assert.deepEqual(received, [{ content: '中文' }, { content: 'second' }, { type: 'done' }]);
});

test('SSE cancels the body at a terminal event and surfaces malformed JSON', async () => {
  let cancelled = false;
  const response = new Response(new ReadableStream({ start(controller) {
    controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'));
  }, cancel() { cancelled = true; } }));
  await consumeSSE(response, () => false);
  assert.equal(cancelled, true);
  await assert.rejects(() => consumeSSE(new Response('data: invalid\n\n'), () => {}), SyntaxError);
});

test('IME commit and Shift+Enter do not send or prevent native composition/newlines', () => {
  let sent = 0;
  let prevented = 0;
  const key = { key: 'Enter', preventDefault() { prevented++; } };
  handleMessageKeydown({ ...key, isComposing: true }, () => sent++);
  handleMessageKeydown({ ...key, keyCode: 229 }, () => sent++);
  handleMessageKeydown({ ...key, shiftKey: true }, () => sent++);
  assert.equal(sent, 0);
  assert.equal(prevented, 0);
  handleMessageKeydown(key, () => sent++);
  assert.equal(sent, 1);
  assert.equal(prevented, 1);
});

test('registration accepts the server username/password contract', () => {
  assert.equal(validateUsername('john_doe'), '');
  assert.equal(validateUsername('用户名字-123'), '');
  assert.notEqual(validateUsername('--_'), '');
  assert.notEqual(validateUsername('ab'), '');
  assert.equal(validatePassword('Passw0rd!'), '');
  assert.notEqual(validatePassword('abc'), '');
});

test('JSON calls and streams share one refresh and retry with session-storage credentials', async () => {
  saveCredentials({ access_token: 'expired', refresh_token: 'refresh' }, false);
  let refreshes = 0;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    if (url === '/api/users/refresh') {
      refreshes++;
      assert.deepEqual(JSON.parse(options.body), { refresh_token: 'refresh' });
      await new Promise(resolve => setTimeout(resolve, 5));
      return json({ access_token: 'new-access', refresh_token: 'new-refresh' });
    }
    return options.headers.get('Authorization') === 'Bearer expired' ? json({ detail: 'expired' }, 401) : json({ ok: true });
  };
  const result = await Promise.all([request('/api/chat/sessions'), request('/api/research/sessions')]);
  assert.deepEqual(result, [{ ok: true }, { ok: true }]);
  assert.equal(refreshes, 1);
  assert.equal(sessionStorage.getItem('refresh_token'), 'new-refresh');
  assert.equal(localStorage.getItem('auth_token'), null);
  assert.equal(calls.at(-1).options.headers.get('Authorization'), 'Bearer new-access');
});

test('logout clears both stores and cannot be reversed by an in-flight refresh', async () => {
  saveCredentials({ access_token: 'expired', refresh_token: 'refresh' });
  let release;
  let started;
  const start = new Promise(resolve => { started = resolve; });
  globalThis.fetch = async url => {
    if (url === '/api/users/refresh') {
      started();
      return new Promise(resolve => { release = () => resolve(json({ access_token: 'late' })); });
    }
    return json({ detail: 'expired' }, 401);
  };
  const pending = request('/api/chat/sessions');
  await start;
  clearCredentials();
  release();
  await assert.rejects(pending, /登录状态已改变/);
  assert.equal(getAccessToken(), null);
  assert.equal(localStorage.getItem('refresh_token'), null);
});

test('multipart upload gets a bearer header without overriding its browser boundary', async () => {
  saveCredentials({ access_token: 'access', refresh_token: 'refresh' });
  const form = new FormData();
  form.append('file', new Blob(['document content']), 'test.txt');
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/rag/upload-document');
    assert.equal(options.headers.has('Content-Type'), false);
    assert.equal(options.headers.get('Authorization'), 'Bearer access');
    assert.equal(await options.body.get('file').text(), 'document content');
    return json({ success: true });
  };
  assert.deepEqual(await request('/api/rag/upload-document', { method: 'POST', body: form }), { success: true });
});

test('validation errors remain readable and auth requests do not start refresh loops', async () => {
  let count = 0;
  globalThis.fetch = async () => { count++; return json({ detail: [{ msg: 'Invalid username' }] }, 422); };
  await assert.rejects(() => request('/api/users/register', { auth: false }), /Invalid username/);
  assert.equal(count, 1);
});

test('notifications queued before mount render after registration and dismissed confirm resolves', async () => {
  const { notificationManager } = await import('../src/composables/useNotifications.js');
  const shown = [];
  notificationManager.error('Visible failure');
  notificationManager.registerToast({ addToast: toast => shown.push(toast) });
  assert.equal(shown[0].message, 'Visible failure');
  const choice = notificationManager.confirm('Delete history?');
  shown.at(-1).onClose();
  assert.equal(await choice, false);
  const confirmed = notificationManager.confirm('Confirm?');
  shown.at(-1).actions[0].handler();
  shown.at(-1).onClose();
  assert.equal(await confirmed, true);
  const staleConfirmation = notificationManager.confirm('Old account confirmation');
  clearCredentials();
  saveCredentials({ access_token: 'different-user' });
  shown.at(-1).actions[0].handler();
  assert.equal(await staleConfirmation, false);
});

test('Pinia discards history loaded after logout and resets pending reply/model state', async () => {
  const { createServer } = await import('vite');
  const { createPinia } = await import('pinia');
  const server = await createServer({ server: { middlewareMode: true }, appType: 'custom', optimizeDeps: { noDiscovery: true, include: [] } });
  try {
    const { useChatStore } = await server.ssrLoadModule('/src/store/index.js');
    const client = await server.ssrLoadModule('/src/api/client.js');
    const store = useChatStore(createPinia());
    client.saveCredentials({ access_token: 'old-user' });
    let release;
    globalThis.fetch = () => new Promise(resolve => { release = () => resolve(json([{ id: 'old-session', title: 'Private history' }])); });
    const pending = store.fetchHistoryList();
    client.clearCredentials();
    store.$reset();
    release();
    await pending;
    assert.deepEqual(store.historyList, []);
    store.addMessage({ role: 'assistant', content: null });
    store.setCurrentRequestController(new AbortController());
    store.abortCurrentRequest();
    assert.equal(store.messages[0].content, '已停止生成');
    assert.equal(store.isTyping, false);
    store.$reset();
    assert.equal(store.currentModel, 'deepseek-flash');
    assert.equal(store.messages.length, 0);
    assert.equal(store.currentRequestController, null);
  } finally {
    await server.close();
  }
});

test('clear-all cannot cross accounts, including a delayed confirmation', async () => {
  const { createServer } = await import('vite');
  const { createPinia } = await import('pinia');
  const server = await createServer({ server: { middlewareMode: true }, appType: 'custom', optimizeDeps: { noDiscovery: true, include: [] } });
  try {
    const { useChatStore } = await server.ssrLoadModule('/src/store/index.js');
    const client = await server.ssrLoadModule('/src/api/client.js');
    const store = useChatStore(createPinia());
    client.saveCredentials({ access_token: 'A' });
    const originalGeneration = client.getAuthGeneration();
    const calls = [];
    let release, started;
    const deleting = new Promise(resolve => { started = resolve; });
    globalThis.fetch = (url, options) => {
      const auth = options.headers.get('Authorization');
      calls.push({ url, auth });
      if (options.method === 'DELETE') {
        started();
        return new Promise(resolve => { release = () => resolve(json({ success: true })); });
      }
      return Promise.resolve(json([{ id: auth === 'Bearer A' ? 'A-session' : 'B-session' }]));
    };
    const pending = store.deleteAllHistories();
    await deleting;
    client.clearCredentials();
    store.$reset();
    client.saveCredentials({ access_token: 'B' });
    store.messages = [{ role: 'user', content: 'B private chat' }];
    release();
    assert.equal(await pending, false);
    assert.equal(await store.deleteAllHistories(originalGeneration), false);
    assert.equal(calls.length, 2);
    assert.ok(calls.every(call => call.auth === 'Bearer A'));
    assert.equal(store.messages[0].content, 'B private chat');
  } finally { await server.close(); }
});

test('new chat and subsequent selection invalidate older history responses', async () => {
  const { createServer } = await import('vite');
  const { createPinia } = await import('pinia');
  const server = await createServer({ server: { middlewareMode: true }, appType: 'custom', optimizeDeps: { noDiscovery: true, include: [] } });
  try {
    const { useChatStore } = await server.ssrLoadModule('/src/store/index.js');
    const store = useChatStore(createPinia());
    const responses = new Map();
    globalThis.fetch = url => new Promise(resolve => { responses.set(url, resolve); });
    const old = store.loadHistory('old');
    store.clearChat();
    store.addMessage({ role: 'user', content: 'New chat' });
    responses.get('/api/chat/sessions/old/messages')(json([{ id: 1, role: 'user', content: 'Old chat' }]));
    await old;
    assert.equal(store.messages[0].content, 'New chat');
    assert.equal(store.activeSessionId, null);
    const first = store.loadHistory('first');
    const second = store.loadHistory('second');
    responses.get('/api/chat/sessions/first/messages')(json([]));
    await first;
    assert.equal(store.isTyping, true);
    responses.get('/api/chat/sessions/second/messages')(json([{ id: 2, role: 'user', content: 'Second' }]));
    await second;
    assert.equal(store.activeSessionId, 'second');
    assert.equal(store.messages[0].content, 'Second');
    assert.equal(store.isTyping, false);
    const stopped = store.loadHistory('stopped');
    store.abortCurrentRequest();
    store.addMessage({ role: 'user', content: 'After stop' });
    responses.get('/api/chat/sessions/stopped/messages')(json([{ id: 3, role: 'user', content: 'Stale stopped load' }]));
    await stopped;
    assert.equal(store.messages.at(-1).content, 'After stop');
  } finally { await server.close(); }
});

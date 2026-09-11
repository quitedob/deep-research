// Disposable browser-only backend fixture; never imported by the application.
(() => {
  const originalFetch = window.fetch.bind(window);
  const json = value => new Response(JSON.stringify(value), { headers: { 'Content-Type': 'application/json' } });
  const state = { requests: [], messages: [], sessions: [], logoutCalls: 0 };
  window.frontendFixture = state;
  const user = { id: 'fixture-user', username: 'fixture_user' };
  window.fetch = async (url, options = {}) => {
    if (!String(url).startsWith('/api/') && url !== '/health') return originalFetch(url, options);
    const path = String(url).split('?')[0];
    const body = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
    state.requests.push({ path, method: options.method || 'GET', authenticated: new Headers(options.headers).has('Authorization') });
    if (path === '/api/users/login' || path === '/api/users/register') return json({ access_token: 'fixture-access', refresh_token: 'fixture-refresh', user });
    if (path === '/api/users/logout') { state.logoutCalls++; return json({ success: true }); }
    if (path === '/api/chat/models') return json({ models: [{ model_name: 'deepseek-flash', display_name: 'DeepSeek Flash', capabilities: ['vision'], is_available: true }], default_model: 'deepseek-flash' });
    if (path === '/api/chat/sessions') {
      if (options.method === 'POST') state.sessions = [{ id: 'fixture-chat', title: body.title }];
      return json(options.method === 'POST' ? state.sessions[0] : state.sessions);
    }
    if (path === '/api/chat/sessions/fixture-chat' && options.method === 'DELETE') { state.sessions = []; state.messages = []; return json({ success: true }); }
    if (path === '/api/chat/sessions/fixture-chat/messages') return json(state.messages);
    if (path === '/api/chat/sessions/fixture-chat') return json({ success: true });
    if (path.startsWith('/api/chat/chat')) {
      const assistant = { id: 2, role: 'assistant', content: '中文回复，传输完整。' };
      state.messages = [{ id: 1, role: 'user', content: body.message }, assistant];
      if (path.endsWith('/stream')) {
        const bytes = new TextEncoder().encode(`data: ${JSON.stringify({ content: assistant.content })}\r\n\r\ndata: ${JSON.stringify({ type: 'message', message: assistant })}\n\ndata: {"type":"done"}\n\n`);
        return new Response(new ReadableStream({ start(controller) {
          for (const byte of bytes) controller.enqueue(Uint8Array.of(byte));
          controller.close();
        } }), { headers: { 'Content-Type': 'text/event-stream' } });
      }
      return json({ session_id: 'fixture-chat', message: assistant });
    }
    if (path === '/api/research/start') return json({ success: true, session_id: 'fixture-research' });
    if (path === '/api/research/stream/fixture-research') {
      const metadata = { type: 'research', session_id: 'fixture-research', evidence: [{ id: 5, content: '证据正文', source_type: 'web', relevance_score: null, confidence_score: null }] };
      state.messages = [{ id: 1, role: 'user', content: '研究主题' }, { id: 2, role: 'assistant', content: '# 研究报告\n已完成。', metadata }];
      return new Response(`data: ${JSON.stringify({ type: 'completed', data: { report_text: '# 研究报告\n已完成。', chat_session_id: 'fixture-chat', metadata } })}\n\n`, { headers: { 'Content-Type': 'text/event-stream' } });
    }
    if (path === '/api/share/conversation') return json({ public_url: '/share/fixture-share', title: body.title });
    if (path === '/api/public/conversation/fixture-share') return json({ title: '共享测试', messages: [{ role: 'assistant', content: '<img src=x onerror="window.fixtureXss=true">\n```html\n<script>alert(1)</script>\n```' }] });
    if (path.startsWith('/api/feedback/message')) return json({ feedbacks: [] });
    if (path.startsWith('/api/evidence/')) return json({ evidence_list: [{ id: 5, snippet: '证据正文', source_type: 'web', relevance_score: null, confidence_score: null }], total_evidence: 1, avg_relevance_score: null });
    return json({ success: true, status: 'healthy' });
  };
})();

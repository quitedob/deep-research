// Preserve partial lines, UTF-8 characters, CRLF boundaries and multiline data fields.
export async function consumeSSE(response, onMessage) {
  if (!response.body) throw new Error('服务器未返回数据流');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let data = [];
  let event = 'message';
  const dispatch = async () => {
    if (!data.length) return false;
    const value = data.join('\n');
    data = [];
    const payload = value === '[DONE]' ? { type: 'done' } : JSON.parse(value);
    const result = await onMessage(payload, event);
    event = 'message';
    return result === false;
  };
  const line = async (value) => {
    if (!value) return dispatch();
    if (value.startsWith(':')) return false;
    const separator = value.indexOf(':');
    const field = separator === -1 ? value : value.slice(0, separator);
    const text = separator === -1 ? '' : value.slice(separator + 1).replace(/^ /, '');
    if (field === 'data') data.push(text);
    if (field === 'event') event = text;
    return false;
  };
  try {
    let finished = false;
    while (!finished) {
      const { done, value } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      let end;
      while ((end = buffer.search(/[\r\n]/)) !== -1) {
        if (!done && buffer[end] === '\r' && end === buffer.length - 1) break;
        const text = buffer.slice(0, end);
        const width = buffer[end] === '\r' && buffer[end + 1] === '\n' ? 2 : 1;
        buffer = buffer.slice(end + width);
        if (await line(text)) return;
      }
      if (done) {
        finished = true;
        if (buffer && await line(buffer)) return;
        await dispatch();
        return;
      }
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

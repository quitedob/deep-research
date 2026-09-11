export function handleMessageKeydown(event, send) {
  if (event.key !== 'Enter' || event.isComposing || event.keyCode === 229) return;
  if (event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) return;
  event.preventDefault();
  send();
}

export function validateUsername(value) {
  if (!value) return '请输入账号';
  if ([...value].length < 3 || [...value].length > 50 || !/^[\p{L}\p{N}_-]+$/u.test(value) || !/[\p{L}\p{N}]/u.test(value)) {
    return '账号需为3-50个字符，仅限字母、数字、下划线和连字符';
  }
  return '';
}

export function validatePassword(value) {
  return [...value].length < 6 || [...value].length > 100 ? '密码长度需为6-100个字符' : '';
}

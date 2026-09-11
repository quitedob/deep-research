const openDialogs = [];
const focusable = (element) => [...element.querySelectorAll('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex="0"]')]
  .filter(item => item.getClientRects().length > 0);

export const dialog = {
  mounted(element, binding) {
    if (typeof binding.value !== 'function') return;
    const previousFocus = document.activeElement;
    element.setAttribute('role', 'dialog');
    element.setAttribute('aria-modal', 'true');
    element.setAttribute('tabindex', '-1');
    if (!element.hasAttribute('aria-label')) element.setAttribute('aria-label', element.querySelector('h2, h3')?.textContent || '对话框');
    const state = { element, close: binding.value, previousFocus };
    const onKey = event => {
      if (openDialogs.at(-1) !== state) return;
      if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); state.close?.(); }
      if (event.key === 'Tab') {
        const items = focusable(element);
        const first = items[0] || element;
        const last = items.at(-1) || element;
        if (event.shiftKey && (document.activeElement === first || !items.includes(document.activeElement))) {
          event.preventDefault(); last.focus();
        } else if (!event.shiftKey && (document.activeElement === last || !items.includes(document.activeElement))) {
          event.preventDefault(); first.focus();
        }
      }
    };
    state.cleanup = () => document.removeEventListener('keydown', onKey, true);
    element.__dialogState = state;
    openDialogs.push(state);
    document.addEventListener('keydown', onKey, true);
    queueMicrotask(() => {
      if (openDialogs.at(-1) === state && element.isConnected) (focusable(element)[0] || element).focus();
    });
  },
  updated(element, binding) { if (element.__dialogState) element.__dialogState.close = binding.value; },
  unmounted(element) {
    const state = element.__dialogState;
    if (!state) return;
    state.cleanup();
    openDialogs.splice(openDialogs.indexOf(state), 1);
    if (state.previousFocus?.isConnected) state.previousFocus.focus();
  }
};

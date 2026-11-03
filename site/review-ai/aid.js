/* Local clipboard enhancement. No uploads, analytics, storage, or AI service. */
'use strict';
for (const button of document.querySelectorAll('[data-copy]')) {
  const area = document.getElementById(button.dataset.copy);
  const status = document.getElementById(button.dataset.status);
  const details = area.closest('details');
  button.hidden = false;
  button.addEventListener('click', async () => {
    button.disabled = true;
    status.textContent = '';
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(area.value);
      status.textContent = 'Text copied. Read it before pasting it into an AI tool you are permitted to use.';
    } catch {
      details.open = true;
      area.focus();
      area.select();
      status.textContent = 'Automatic copying is unavailable. Copy the selected text manually, or download it.';
    } finally {
      button.disabled = false;
    }
  });
}

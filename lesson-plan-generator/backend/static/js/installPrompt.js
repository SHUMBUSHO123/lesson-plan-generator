let deferredPrompt;

window.addEventListener('DOMContentLoaded', () => {
  const installBtn = document.getElementById('installBtn');

  if (!installBtn) return;

  // Fallback: show button after interaction
  const showInstallButton = () => {
    installBtn.style.display = 'block';
  };

  window.addEventListener('click', showInstallButton, { once: true });

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    installBtn.style.display = 'block';
  });

  installBtn.addEventListener('click', async () => {
    installBtn.style.display = 'none';

    if (deferredPrompt) {
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
    } else {
      alert(
        'Install this app:\n\n' +
        '1. Tap the browser menu (⋮)\n' +
        '2. Select "Add to Home screen"\n' +
        '3. Confirm installation'
      );
    }
  });
});

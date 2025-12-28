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
        'To install:\n\n' +
        '• Open browser menu (⋮)\n' +
        '• Tap "Add to Home screen"'
      );
    }
  });
});

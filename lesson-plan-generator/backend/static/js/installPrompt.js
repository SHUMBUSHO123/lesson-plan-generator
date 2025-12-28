let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault(); // prevent automatic prompt
  deferredPrompt = e;

  const installBtn = document.getElementById('installBtn');
  if (installBtn) installBtn.style.display = 'block';

  installBtn.addEventListener('click', async () => {
    installBtn.style.display = 'none';
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log('User choice:', outcome);
    deferredPrompt = null;
  });
});

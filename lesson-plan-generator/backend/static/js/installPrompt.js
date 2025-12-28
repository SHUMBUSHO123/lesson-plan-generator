let deferredPrompt;
const installBtn = document.getElementById('installBtn');

// Show button after first user interaction if prompt not yet fired
function showInstallButton() {
  if (installBtn && installBtn.style.display === 'none') {
    installBtn.style.display = 'block';
  }
}

// Listen for beforeinstallprompt (Chrome auto prompt)
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault(); // Prevent automatic prompt
  deferredPrompt = e;

  if (installBtn) installBtn.style.display = 'block';
});

// Fallback: show install button after first click/tap anywhere
window.addEventListener('click', showInstallButton, { once: true });

// Install button click
if (installBtn) {
  installBtn.addEventListener('click', async () => {
    installBtn.style.display = 'none';
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log('User choice:', outcome);
      deferredPrompt = null;
    } else {
      // Fallback message if auto prompt never fired
      alert('To install this app, open your browser menu and select "Add to Home screen".');
    }
  });
}

(() => {
  function refreshStatsLinks() {
    const currentUserId = window.ugcIdentity.getUserId();
    document.querySelectorAll('.stats-link').forEach((statsLink) => {
      const isAuthor = statsLink.dataset.author === currentUserId;
      statsLink.classList.toggle('d-none', !isAuthor);
    });
  }

  refreshStatsLinks();

  const userIdInput = document.getElementById('user-id-input');
  if (userIdInput) {
    userIdInput.addEventListener('change', refreshStatsLinks);
    userIdInput.addEventListener('input', refreshStatsLinks);
  }

  window.addEventListener('ugc:user-changed', refreshStatsLinks);
})();

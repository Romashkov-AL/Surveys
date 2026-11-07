(() => {
  const STORAGE_KEY = 'ugc_user_id';
  const userIdInput = document.getElementById('user-id-input');

  function syncIdentityCookie(userId) {
    document.cookie = `${STORAGE_KEY}=${encodeURIComponent(userId)}; path=/; SameSite=Lax`;
  }

  function currentUserId() {
    let userId = localStorage.getItem(STORAGE_KEY);
    if (!userId) {
      userId = `anon-${crypto.randomUUID().slice(0, 8)}`;
      localStorage.setItem(STORAGE_KEY, userId);
    }
    syncIdentityCookie(userId);
    return userId;
  }

  if (userIdInput) {
    userIdInput.value = currentUserId();
    userIdInput.addEventListener('change', () => {
      const trimmedUserId = userIdInput.value.trim();
      if (trimmedUserId) {
        localStorage.setItem(STORAGE_KEY, trimmedUserId);
        syncIdentityCookie(trimmedUserId);
        window.dispatchEvent(new Event('ugc:user-changed'));
      }
    });
  } else {
    currentUserId();
  }

  window.ugcIdentity = {
    getUserId: currentUserId,
    async api(url, options = {}) {
      const headers = new Headers(options.headers || {});
      headers.set('X-User-Id', encodeURIComponent(currentUserId()));
      if (options.body && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
      }
      const response = await fetch(url, { ...options, headers });
      const responseText = await response.text();
      let responseData = null;
      try {
        responseData = responseText ? JSON.parse(responseText) : null;
      } catch {
        responseData = { detail: responseText };
      }
      if (!response.ok) {
        const requestError = new Error(
          (responseData && responseData.detail) || response.statusText
        );
        requestError.status = response.status;
        requestError.data = responseData;
        throw requestError;
      }
      return responseData;
    },
  };
})();

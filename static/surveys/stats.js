(() => {
  const statsRoot = document.getElementById('stats-root');
  if (!statsRoot) return;
  const statsBox = document.getElementById('stats-box');
  const surveyId = statsRoot.dataset.surveyId;

  window.ugcIdentity
    .api(`/api/surveys/${surveyId}/stats/`)
    .then((statsData) => {
      const averageDuration =
        statsData.avg_duration_seconds == null
          ? 'нет данных'
          : `${statsData.avg_duration_seconds.toFixed(1)} сек`;
      const questionBlocks = statsData.by_question
        .map((questionStats) => {
          const choiceRows = questionStats.choices
            .map(
              (choiceStats) =>
                `<li class="list-group-item d-flex justify-content-between">
                  <span>${escapeHtml(choiceStats.text)}</span>
                  <span class="badge text-bg-secondary">${choiceStats.count}</span>
                </li>`
            )
            .join('');
          return `<div class="mb-3">
            <h2 class="h6">${questionStats.position}. ${escapeHtml(questionStats.question_text)}</h2>
            <ul class="list-group list-group-flush">${choiceRows}</ul>
          </div>`;
        })
        .join('');
      statsBox.innerHTML = `
        <p>Завершенных прохождений: <strong>${statsData.finished_attempts}</strong></p>
        <p>Среднее время: <strong>${averageDuration}</strong></p>
        ${questionBlocks}`;
    })
    .catch((error) => {
      statsBox.innerHTML = `<p class="text-danger mb-0">${escapeHtml(error.message)}</p>`;
    });

  function escapeHtml(rawText) {
    return String(rawText)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;');
  }
})();

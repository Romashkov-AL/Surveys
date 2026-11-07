(() => {
  const takeRoot = document.getElementById('take-root');
  if (!takeRoot) return;

  const surveyId = takeRoot.dataset.surveyId;
  const questionBox = document.getElementById('question-box');

  async function loadNext() {
    questionBox.innerHTML = `<p class="text-muted mb-0">Загрузка вопроса…</p>`;
    const nextQuestionData = await window.ugcIdentity.api(
      `/api/surveys/${surveyId}/next-question/`
    );
    if (nextQuestionData.done) {
      questionBox.innerHTML = `<h2 class="h4">Готово</h2><p class="mb-0">Опрос пройден.</p>`;
      return;
    }
    renderQuestion(nextQuestionData.question);
  }

  function renderQuestion(question) {
    const choicesMarkup = question.choices
      .map(
        (choice) => `
      <div class="form-check">
        <input class="form-check-input" type="radio" name="choice" id="choice-${choice.id}"
               value="${choice.id}" data-free="${choice.allows_free_text}">
        <label class="form-check-label" for="choice-${choice.id}">${escapeHtml(choice.text)}</label>
      </div>`
      )
      .join('');

    questionBox.innerHTML = `
      <div data-question-id="${question.id}">
        <p class="text-muted small mb-1">вопрос ${question.position}</p>
        <h2 class="h4">${escapeHtml(question.text)}</h2>
        <div class="d-grid gap-2 my-3">${choicesMarkup}</div>
        <textarea id="free-text" class="form-control mb-3 d-none" rows="2" placeholder="Свой ответ"></textarea>
        <button type="button" id="send-answer" class="btn btn-primary">Ответить</button>
      </div>`;

    const freeTextInput = document.getElementById('free-text');
    questionBox.querySelectorAll('input[name="choice"]').forEach((choiceInput) => {
      choiceInput.addEventListener('change', () => {
        freeTextInput.classList.toggle('d-none', choiceInput.dataset.free !== 'true');
      });
    });

    document.getElementById('send-answer').addEventListener('click', submitAnswer);
  }

  async function submitAnswer() {
    const questionCard = questionBox.querySelector('[data-question-id]');
    const selectedChoice = questionBox.querySelector('input[name="choice"]:checked');
    if (!selectedChoice) {
      alert('Выбери вариант');
      return;
    }
    const payload = {
      question_id: Number(questionCard.dataset.questionId),
      choice_id: Number(selectedChoice.value),
      free_text: document.getElementById('free-text').value || '',
    };
    try {
      await window.ugcIdentity.api(`/api/surveys/${surveyId}/answers/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      await loadNext();
    } catch (error) {
      alert(error.message || 'Ошибка');
    }
  }

  function escapeHtml(rawText) {
    return String(rawText)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;');
  }

  loadNext().catch((error) => {
    questionBox.innerHTML = `<p class="text-danger mb-0">Не удалось загрузить: ${escapeHtml(error.message)}</p>`;
  });
})();

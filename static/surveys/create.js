(() => {
  const form = document.getElementById('create-form');
  const questionsContainer = document.getElementById('questions');
  const resultOutput = document.getElementById('create-result');
  let questionSeq = 0;

  function moveElementUp(element) {
    const previous = element.previousElementSibling;
    if (previous) {
      element.parentElement.insertBefore(element, previous);
    }
  }

  function moveElementDown(element) {
    const next = element.nextElementSibling;
    if (next) {
      element.parentElement.insertBefore(next, element);
    }
  }

  function refreshQuestionLabels() {
    [...questionsContainer.querySelectorAll('.q-block')].forEach(
      (questionBlock, questionIndex) => {
        const label = questionBlock.querySelector('.question-label');
        if (label) {
          label.textContent = `Вопрос ${questionIndex + 1}`;
        }
      }
    );
  }

  function addChoice(questionBlock) {
    const choicesContainer = questionBlock.querySelector('.choices-edit');
    const choiceRow = document.createElement('div');
    choiceRow.className = 'row g-2 align-items-center choice-row';
    const freeTextId = `free-${questionBlock.dataset.uid}-${choicesContainer.children.length}-${Date.now()}`;
    choiceRow.innerHTML = `
      <div class="col">
        <input name="ctext" class="form-control" required placeholder="Ответ">
      </div>
      <div class="col-auto">
        <div class="form-check mb-0">
          <input class="form-check-input" type="checkbox" name="free" id="${freeTextId}">
          <label class="form-check-label" for="${freeTextId}">свой вариант</label>
        </div>
      </div>
      <div class="col-auto btn-group btn-group-sm">
        <button type="button" class="btn btn-outline-secondary move-choice-up" title="Выше">↑</button>
        <button type="button" class="btn btn-outline-secondary move-choice-down" title="Ниже">↓</button>
        <button type="button" class="btn btn-outline-danger remove-choice" title="Удалить">×</button>
      </div>`;
    choiceRow
      .querySelector('.move-choice-up')
      .addEventListener('click', () => moveElementUp(choiceRow));
    choiceRow
      .querySelector('.move-choice-down')
      .addEventListener('click', () => moveElementDown(choiceRow));
    choiceRow.querySelector('.remove-choice').addEventListener('click', () => {
      const choices = choicesContainer.querySelectorAll('.choice-row');
      if (choices.length <= 1) return;
      choiceRow.remove();
    });
    choicesContainer.appendChild(choiceRow);
  }

  function addQuestion() {
    questionSeq += 1;
    const questionBlock = document.createElement('div');
    questionBlock.className = 'card card-body bg-white border q-block';
    questionBlock.dataset.uid = String(questionSeq);
    questionBlock.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-2 gap-2">
        <label class="form-label question-label mb-0">Вопрос</label>
        <div class="btn-group btn-group-sm">
          <button type="button" class="btn btn-outline-secondary move-question-up" title="Выше">↑</button>
          <button type="button" class="btn btn-outline-secondary move-question-down" title="Ниже">↓</button>
          <button type="button" class="btn btn-outline-danger remove-question" title="Удалить">×</button>
        </div>
      </div>
      <div class="mb-2">
        <input name="qtext" class="form-control" required placeholder="Что думаешь?">
      </div>
      <div class="choices-edit d-grid gap-2 mb-2"></div>
      <button type="button" class="btn btn-sm btn-outline-secondary add-choice">+ вариант ответа</button>`;
    questionsContainer.appendChild(questionBlock);

    questionBlock
      .querySelector('.add-choice')
      .addEventListener('click', () => addChoice(questionBlock));
    questionBlock.querySelector('.move-question-up').addEventListener('click', () => {
      moveElementUp(questionBlock);
      refreshQuestionLabels();
    });
    questionBlock.querySelector('.move-question-down').addEventListener('click', () => {
      moveElementDown(questionBlock);
      refreshQuestionLabels();
    });
    questionBlock.querySelector('.remove-question').addEventListener('click', () => {
      if (questionsContainer.querySelectorAll('.q-block').length <= 1) return;
      questionBlock.remove();
      refreshQuestionLabels();
    });

    addChoice(questionBlock);
    addChoice(questionBlock);
    refreshQuestionLabels();
  }

  document.getElementById('add-question').addEventListener('click', addQuestion);
  addQuestion();

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const title = form.querySelector('[name="title"]').value.trim();
    const questions = [...questionsContainer.querySelectorAll('.q-block')].map(
      (questionBlock, questionIndex) => {
        const choices = [...questionBlock.querySelectorAll('.choice-row')].map(
          (choiceRow, choiceIndex) => ({
            text: choiceRow.querySelector('[name="ctext"]').value.trim(),
            position: choiceIndex + 1,
            allows_free_text: choiceRow.querySelector('[name="free"]').checked,
          })
        );
        return {
          text: questionBlock.querySelector('[name="qtext"]').value.trim(),
          position: questionIndex + 1,
          choices,
        };
      }
    );

    try {
      const createdSurvey = await window.ugcIdentity.api('/api/surveys/create/', {
        method: 'POST',
        body: JSON.stringify({ title, questions }),
      });
      resultOutput.hidden = false;
      resultOutput.textContent = JSON.stringify(createdSurvey, null, 2);
      window.location.href = `/surveys/${createdSurvey.id}/`;
    } catch (error) {
      resultOutput.hidden = false;
      resultOutput.textContent = error.message;
    }
  });
})();

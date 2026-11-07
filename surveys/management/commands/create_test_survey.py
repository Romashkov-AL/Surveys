from django.core.management.base import BaseCommand

from surveys.models import Choice, Question, Survey, User

TEST_QUESTIONS = [
    (
        'Ты любишь буррату с помидорами?',
        ['Да', 'Нет', 'У меня непереносимость лактозы'],
    ),
    ('Ты любишь огурцы?', ['Да', 'Нет', 'Только в коктейлях']),
    ('Ты любишь помидоры?', ['Да', 'Нет', 'Только если гаспаччо']),
    ('Ты любишь огуречный салат?', ['Да', 'Нет', 'Только с уксусом']),
    ('Ты любишь овощи в целом?', ['Люблю', 'Терплю', 'Свой ответ']),
]


class Command(BaseCommand):
    help = 'Создание тестового опроса'

    def handle(self, *args, **options):
        author, _ = User.objects.get_or_create(username='test-author')
        survey, created = Survey.objects.get_or_create(title='Тестовый опрос', author=author)
        if not created and survey.questions.exists():
            self.stdout.write(self.style.WARNING('Тестовый опрос уже создан.'))
            return

        for question_pos, (question_text, choices) in enumerate(TEST_QUESTIONS, start=1):
            question = Question.objects.create(
                survey=survey,
                text=question_text,
                position=question_pos,
            )
            for choice_pos, choice_text in enumerate(choices, start=1):
                Choice.objects.create(
                    question=question,
                    text=choice_text,
                    position=choice_pos,
                    allows_free_text=choice_text == 'Свой ответ',
                )
        self.stdout.write(self.style.SUCCESS(f'Тестовый опрос id={survey.id} создан.'))

from django.db import models
from django.db.models import Q


class User(models.Model):
    username = models.CharField(max_length=150, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self) -> str:
        return self.username


class Survey(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_surveys',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['author', '-created_at'])]

    def __str__(self) -> str:
        return self.title


class Question(models.Model):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    text = models.CharField(max_length=500)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['survey', 'position'],
                name='uniq_question_position_per_survey',
            )
        ]
        indexes = [models.Index(fields=['survey', 'position'])]

    def __str__(self) -> str:
        return f'{self.position}. {self.text}'


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
    )
    text = models.CharField(max_length=500)
    position = models.PositiveIntegerField(default=0)
    allows_free_text = models.BooleanField(
        default=False,
        help_text='При выборе данного варианта, пользователь может ввести свой ответ.',
    )

    class Meta:
        ordering = ['position', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'position'],
                name='uniq_choice_position_per_question',
            )
        ]
        indexes = [models.Index(fields=['question', 'position'])]

    def __str__(self) -> str:
        return self.text


class Attempt(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'survey', '-started_at']),
            models.Index(fields=['survey', 'finished_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'survey'],
                condition=Q(finished_at__isnull=True),
                name='uniq_open_attempt_per_user_survey',
            )
        ]

    @property
    def is_finished(self) -> bool:
        return self.finished_at is not None

    def __str__(self) -> str:
        state = 'done' if self.is_finished else 'open'
        return f'{self.user} - {self.survey} ({state})'


class Answer(models.Model):
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.PROTECT,
        related_name='answers',
    )
    free_text = models.CharField(max_length=1000, blank=True, default='')
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'question'],
                name='uniq_answer_per_attempt_question',
            )
        ]
        indexes = [
            models.Index(fields=['attempt', 'question']),
            models.Index(fields=['choice']),
        ]

    def __str__(self) -> str:
        return f'{self.question_id} - {self.choice_id}'

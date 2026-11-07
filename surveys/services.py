from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef, QuerySet
from django.utils import timezone

from surveys.models import Answer, Attempt, Choice, Question, Survey, User


def surveys_for_api() -> QuerySet[Survey]:
    return Survey.objects.select_related('author').annotate(
        questions_count=Count('questions'),
    )


def create_survey_with_questions(
    *,
    title: str,
    author: User,
    questions: list[dict[str, Any]],
) -> Survey:
    with transaction.atomic():
        survey = Survey.objects.create(title=title, author=author)
        sorted_questions = sorted(questions, key=lambda item: item['position'])
        created_questions = Question.objects.bulk_create(
            [
                Question(
                    survey=survey,
                    text=question_data['text'],
                    position=question_data['position'],
                )
                for question_data in sorted_questions
            ],
        )
        choices = [
            Choice(
                question=question,
                text=choice_data['text'],
                position=choice_data['position'],
                allows_free_text=choice_data.get('allows_free_text', False),
            )
            for question, question_data in zip(
                created_questions,
                sorted_questions,
                strict=True,
            )
            for choice_data in sorted(
                question_data['choices'],
                key=lambda item: item['position'],
            )
        ]
        if choices:
            Choice.objects.bulk_create(choices)

        return survey


def delete_survey(survey: Survey) -> None:
    with transaction.atomic():
        Attempt.objects.filter(survey=survey).delete()
        survey.delete()


async def get_or_open_attempt(*, user, survey: Survey) -> Attempt:
    current_attempt = await Attempt.objects.filter(
        user=user,
        survey=survey,
        finished_at__isnull=True,
    ).order_by('-started_at').afirst()
    if current_attempt is not None:
        return current_attempt

    latest = await Attempt.objects.filter(
        user=user,
        survey=survey,
    ).order_by('-started_at').afirst()
    if latest is not None:
        return latest

    try:
        return await Attempt.objects.acreate(user=user, survey=survey)
    except IntegrityError:
        current_attempt = await Attempt.objects.filter(
            user=user,
            survey=survey,
            finished_at__isnull=True,
        ).order_by('-started_at').afirst()
        if current_attempt is not None:
            return current_attempt

        latest = await Attempt.objects.filter(
            user=user,
            survey=survey,
        ).order_by('-started_at').afirst()
        if latest is not None:
            return latest

        raise


async def next_unanswered_question(attempt: Attempt) -> Question | None:
    answered = Answer.objects.filter(
        attempt=attempt,
        question_id=OuterRef('pk'),
    )
    return await Question.objects.filter(
        survey_id=attempt.survey_id,
    ).annotate(already=Exists(answered)).filter(
        already=False,
    ).prefetch_related('choices').order_by('position', 'id').afirst()


async def mark_finished_if_complete(attempt: Attempt) -> Attempt:
    remaining = await next_unanswered_question(attempt)
    if remaining is None and attempt.finished_at is None:
        attempt.finished_at = timezone.now()
        await attempt.asave(update_fields=['finished_at'])
    return attempt

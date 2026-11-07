from asgiref.sync import sync_to_async
from django.db import IntegrityError
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from rest_framework import status
from rest_framework.response import Response

from adrf.views import APIView
from surveys.models import Answer, Attempt, Choice, Survey
from surveys.api.serializers import (
    AnswerWriteSerializer,
    QuestionSerializer,
    SurveyCreateSerializer,
    SurveyPatchSerializer,
    SurveySerializer,
)
from surveys.api.utils import survey_response_data
from surveys.services import (
    create_survey_with_questions,
    delete_survey,
    get_or_open_attempt,
    mark_finished_if_complete,
    next_unanswered_question,
    surveys_for_api,
)


class SurveyListView(APIView):
    async def get(self, request):
        surveys = [survey async for survey in surveys_for_api()[:50]]
        response_data = await sync_to_async(
            lambda: SurveySerializer(surveys, many=True).data,
        )()
        return Response(response_data)


class SurveyCreateView(APIView):
    async def post(self, request):
        serializer = SurveyCreateSerializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        payload = serializer.validated_data
        survey = await sync_to_async(create_survey_with_questions)(
            title=payload['title'],
            author=request.survey_user,
            questions=payload['questions'],
        )
        return Response(
            await survey_response_data(survey.id),
            status=status.HTTP_201_CREATED,
        )


class SurveyDetailView(APIView):
    async def get(self, request, survey_id: int):
        try:
            return Response(await survey_response_data(survey_id))
        except Survey.DoesNotExist:
            return Response(
                {'detail': 'Опрос не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    async def patch(self, request, survey_id: int):
        try:
            survey = await Survey.objects.aget(pk=survey_id)
        except Survey.DoesNotExist:
            return Response(
                {'detail': 'Опрос не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if survey.author_id != request.survey_user.id:
            return Response(
                {'detail': 'Только автор может редактировать свой опрос.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SurveyPatchSerializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        survey.title = serializer.validated_data['title']
        await survey.asave(update_fields=['title'])
        return Response(await survey_response_data(survey.id))

    async def delete(self, request, survey_id: int):
        try:
            survey = await Survey.objects.aget(pk=survey_id)
        except Survey.DoesNotExist:
            return Response(
                {'detail': 'Опрос не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if survey.author_id != request.survey_user.id:
            return Response(
                {'detail': 'Только автор может удалить свой опрос.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        await sync_to_async(delete_survey)(survey)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NextQuestionView(APIView):
    async def get(self, request, survey_id: int):
        try:
            survey = await Survey.objects.aget(pk=survey_id)
        except Survey.DoesNotExist:
            return Response(
                {'detail': 'Опрос не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        attempt = await get_or_open_attempt(user=request.survey_user, survey=survey)
        if attempt.finished_at is not None:
            return Response(
                {
                    'done': True,
                    'attempt_id': attempt.id,
                    'finished_at': attempt.finished_at,
                    'question': None,
                }
            )

        question = await next_unanswered_question(attempt)
        if question is None:
            attempt = await mark_finished_if_complete(attempt)
            return Response(
                {
                    'done': True,
                    'attempt_id': attempt.id,
                    'finished_at': attempt.finished_at,
                    'question': None,
                }
            )

        response_data = await sync_to_async(lambda: QuestionSerializer(question).data)()
        return Response(
            {
                'done': False,
                'attempt_id': attempt.id,
                'finished_at': None,
                'question': response_data,
            }
        )


class AnswerCreateView(APIView):
    async def post(self, request, survey_id: int):
        serializer = AnswerWriteSerializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        data = serializer.validated_data
        try:
            survey = await Survey.objects.aget(pk=survey_id)
        except Survey.DoesNotExist:
            return Response(
                {'detail': 'Опрос не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        attempt = await get_or_open_attempt(user=request.survey_user, survey=survey)
        if attempt.finished_at is not None:
            return Response(
                {'detail': 'Попытка уже завершена.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        next_question = await next_unanswered_question(attempt)
        if next_question is None:
            return Response(
                {'detail': 'Нет следующего вопроса для ответа.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if next_question.id != data['question_id']:
            return Response(
                {
                    'detail': 'Ответить можно только на текущий вопрос.',
                    'expected_question_id': next_question.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            question = next_question
            choice = await Choice.objects.aget(pk=data['choice_id'], question=question)
        except Choice.DoesNotExist:
            return Response(
                {'detail': 'Ошибка в вопросе/ответе для этого опроса.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        free_text = (data.get('free_text') or '').strip()
        if choice.allows_free_text and (not free_text):
            return Response(
                {'detail': 'Пользовательский ответ не может быть пустым.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not choice.allows_free_text:
            free_text = ''

        existing_answer = await Answer.objects.filter(
            attempt=attempt,
            question=question,
        ).afirst()
        if existing_answer is not None:
            return Response(
                {'detail': 'Ответ уже существует.'},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            answer = await Answer.objects.acreate(
                attempt=attempt,
                question=question,
                choice=choice,
                free_text=free_text,
            )
        except IntegrityError:
            return Response(
                {'detail': 'Ответ уже существует.'},
                status=status.HTTP_409_CONFLICT,
            )

        attempt = await mark_finished_if_complete(attempt)
        return Response(
            {
                'id': answer.id,
                'attempt_id': attempt.id,
                'done': attempt.finished_at is not None,
                'finished_at': attempt.finished_at,
            },
            status=status.HTTP_201_CREATED,
        )


# TODO: добавить кэширование
class SurveyStatsView(APIView):
    async def get(self, request, survey_id: int):
        try:
            survey = await Survey.objects.aget(pk=survey_id)
        except Survey.DoesNotExist:
            return Response(
                {'detail': 'Опрос не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if survey.author_id != request.survey_user.id:
            return Response(
                {'detail': 'Статистика доступна только автору опроса.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        finished = Attempt.objects.filter(
            survey=survey,
            finished_at__isnull=False,
        )
        finished_count = await finished.acount()
        duration = ExpressionWrapper(
            F('finished_at') - F('started_at'),
            output_field=DurationField(),
        )
        aggregate = await finished.annotate(duration=duration).aaggregate(
            avg_duration=Avg('duration'),
        )
        avg_duration = aggregate['avg_duration']
        avg_seconds = avg_duration.total_seconds() if avg_duration else None
        choice_rows = [
            row
            async for row in Choice.objects.filter(
                question__survey=survey,
            ).annotate(
                picks=Count(
                    'answers',
                    filter=Q(answers__attempt__finished_at__isnull=False),
                ),
            ).order_by(
                'question__position',
                'position',
            ).values(
                'id',
                'text',
                'question_id',
                'question__text',
                'question__position',
                'picks',
            )
        ]

        by_question: dict[int, dict] = {}
        for row in choice_rows:
            question_id = row['question_id']
            bucket = by_question.setdefault(
                question_id,
                {
                    'question_id': question_id,
                    'question_text': row['question__text'],
                    'position': row['question__position'],
                    'choices': [],
                },
            )
            bucket['choices'].append({
                'choice_id': row['id'],
                'text': row['text'],
                'count': row['picks'],
            })

        popular = sorted(by_question.values(), key=lambda item: item['position'])
        return Response({
            'survey_id': survey.id,
            'title': survey.title,
            'finished_attempts': finished_count,
            'avg_duration_seconds': avg_seconds,
            'by_question': popular,
        })

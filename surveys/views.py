from django.core.exceptions import PermissionDenied
from django.shortcuts import aget_object_or_404
from django.template.response import TemplateResponse
from django.views import View

from surveys.models import Survey


class IndexView(View):
    async def get(self, request):
        surveys = [
            survey
            async for survey in Survey.objects.select_related('author').all()[:50]
        ]
        return TemplateResponse(
            request,
            'surveys/index.html',
            {'surveys': surveys},
        )


class TakeSurveyView(View):
    async def get(self, request, survey_id: int):
        survey = await aget_object_or_404(
            Survey.objects.select_related('author'),
            pk=survey_id,
        )
        return TemplateResponse(
            request,
            'surveys/take.html',
            {'survey': survey},
        )


class SurveyStatsPageView(View):
    async def get(self, request, survey_id: int):
        survey = await aget_object_or_404(
            Survey.objects.select_related('author'),
            pk=survey_id,
        )
        user = getattr(request, 'survey_user', None)
        if user is None or survey.author_id != user.id:
            raise PermissionDenied('Статистика доступна только автору опроса.')

        return TemplateResponse(
            request,
            'surveys/stats.html',
            {'survey': survey},
        )


class CreateSurveyPageView(View):
    async def get(self, request):
        return TemplateResponse(request, 'surveys/create.html')

from django.urls import path

from surveys import views
from surveys.api.api import (
    AnswerCreateView,
    NextQuestionView,
    SurveyCreateView,
    SurveyDetailView,
    SurveyListView,
    SurveyStatsView,
)

app_name = 'surveys'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('create/', views.CreateSurveyPageView.as_view(), name='create'),
    path(
        'surveys/<int:survey_id>/',
        views.TakeSurveyView.as_view(),
        name='take',
    ),
    path(
        'surveys/<int:survey_id>/stats/',
        views.SurveyStatsPageView.as_view(),
        name='stats',
    ),
    path('api/surveys/', SurveyListView.as_view(), name='api-survey-list'),
    path(
        'api/surveys/create/',
        SurveyCreateView.as_view(),
        name='api-survey-create',
    ),
    path(
        'api/surveys/<int:survey_id>/',
        SurveyDetailView.as_view(),
        name='api-survey-detail',
    ),
    path(
        'api/surveys/<int:survey_id>/next-question/',
        NextQuestionView.as_view(),
        name='api-next-question',
    ),
    path(
        'api/surveys/<int:survey_id>/answers/',
        AnswerCreateView.as_view(),
        name='api-answer',
    ),
    path(
        'api/surveys/<int:survey_id>/stats/',
        SurveyStatsView.as_view(),
        name='api-stats',
    ),
]

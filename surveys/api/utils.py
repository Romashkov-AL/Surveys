from asgiref.sync import sync_to_async

from surveys.api.serializers import SurveySerializer
from surveys.services import surveys_for_api


async def survey_response_data(survey_id: int) -> dict:
    survey = await surveys_for_api().aget(pk=survey_id)
    return await sync_to_async(lambda: SurveySerializer(survey).data)()

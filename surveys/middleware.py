from urllib.parse import unquote

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import JsonResponse
from rest_framework import status

from surveys.models import User

HEADER = 'X-User-Id'


class IdentifyUserMiddleware:
    """Async-capable: sync ORM только на sync-пути, на ASGI — aget_or_create."""

    async_capable = True
    sync_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def __call__(self, request):
        if iscoroutinefunction(self.get_response):
            return self.__acall__(request)

        self._attach_user_sync(request)
        denied = self._deny_if_needed(request)
        if denied is not None:
            return denied
        return self.get_response(request)

    async def __acall__(self, request):
        await self._attach_user_async(request)
        denied = self._deny_if_needed(request)
        if denied is not None:
            return denied
        return await self.get_response(request)

    def _username_from_request(self, request) -> str:
        raw = (request.headers.get(HEADER) or '').strip()
        if not raw:
            raw = (request.COOKIES.get('ugc_user_id') or '').strip()
        return unquote(raw)

    def _attach_user_sync(self, request) -> None:
        request.survey_user = None
        username = self._username_from_request(request)
        if username:
            request.survey_user, _ = User.objects.get_or_create(username=username)

    async def _attach_user_async(self, request) -> None:
        request.survey_user = None
        username = self._username_from_request(request)
        if username:
            request.survey_user, _ = await User.objects.aget_or_create(
                username=username,
            )

    def _deny_if_needed(self, request):
        if request.path.startswith('/api/') and request.survey_user is None:
            return JsonResponse(
                {'detail': f'Заголовок {HEADER} обязателен для вызовов API.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return None

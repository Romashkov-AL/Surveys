from asgiref.sync import sync_to_async
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from config.utils import ping_database


async def health(_request):
    try:
        await sync_to_async(ping_database)()
        database_status = 'ok'
        status = 200
    except Exception:
        database_status = 'unavailable'
        status = 503

    return JsonResponse(
        {
            'app_status': 'ok',
            'database_status': database_status,
        },
        status=status,
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    path('', include('surveys.urls')),
]

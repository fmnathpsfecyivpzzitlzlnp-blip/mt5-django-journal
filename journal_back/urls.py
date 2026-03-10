from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Ссылки на API (они передаются во второй файл)
    path('api/', include('trades.urls')),
    path('api-auth/', include('rest_framework.urls')),

    # Твои HTML-страницы
    path('', TemplateView.as_view(template_name='inbox.html'), name='inbox'),
    path('journal/', TemplateView.as_view(template_name='journal.html'), name='journal'),
    path('analytics/', TemplateView.as_view(template_name='analytics.html'), name='analytics'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('risk-audit/', TemplateView.as_view(template_name='risk_audit.html'), name='risk_audit'),

    # 👇 НОВОЕ: Страница Playbook
    path('playbook/', TemplateView.as_view(template_name='playbook.html'), name='playbook'),
]

# Раздача картинок для разработчика
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""
URL configuration for openmoxie project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,path
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from hive.views import public_markup_api

urlpatterns = [
    path('', RedirectView.as_view(url='/hive/', permanent=False), name='root'),
    path('hive/', include("hive.urls")),
    path('public/markup/', public_markup_api, name='public_markup_api'),
    path('admin/', admin.site.urls),
] + debug_toolbar_urls()

# WhiteNoise handles static files serving in production
# In development, Django's staticfiles app handles it when DEBUG=True
if settings.DEBUG:
    # Only add media files handling in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""
URL configuration for input_processor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # Django Admin Panel
    path('admin/', admin.site.urls),

    # Home page (Landing Page)
    path('', include('home.urls')),

    # Static Template Pages (no backend logic)
    path('SplunkRRN/', TemplateView.as_view(template_name='SplunkRRN.html'), name='SplunkRRN'),
    path('json2yaml/', TemplateView.as_view(template_name='json2yaml.html'), name='json2yaml'),
    path('compare/', TemplateView.as_view(template_name='compare.html'), name='compare'),
    path('reader/', TemplateView.as_view(template_name='reader.html'), name='reader'),

    # Django Apps with dynamic URLs
    path('splunkparser/', include('splunkparser.urls')),
    path('binblock/', include('binblock.urls')),
    path('pdf_merger/', include('pdf_merger.urls')),
    path('slot_booking/', include('slot_booking.urls')),
]

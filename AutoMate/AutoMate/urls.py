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
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('first_page.urls')),
    path('splunk2sender/', include('first_page.urls')), 
    path('mclogsfilter/', include('mclogsfilter.urls')),
    path('SplunkRRN/', include('first_page.urls')),
    path('sender/', include('sender.urls')),
    path('certifications/', include('certifications.urls')),
    path('bookings/', include('bookings.urls')),
    path('binblocking/', include('binblocking.urls')),

]

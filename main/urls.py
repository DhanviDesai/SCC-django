"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('features.users.urls')),
    path('api/company/', include('features.company.urls')),
    path('api/city/', include('features.city.urls')),
    path('api/tournament/', include('features.tournament.urls')),
    path('api/season/', include('features.season.urls')),
    path('api/type/', include('features.sport_type.urls')),
    path('api/sport/', include('features.sport.urls')),
    path('api/notifications/', include('features.notifications.urls')),
    path('api/team/', include('features.team.urls')),
    path('api/news/', include('features.news.urls')),
    path('api/news', include('features.news.urls')),
    path('api/strava/', include('features.strava.urls')),
    path('api/metric/', include('features.metric.urls')),
    path('api/icons', include('features.icon.urls')),
    path('api/leaderboard/', include('features.leaderboard.urls')),
]

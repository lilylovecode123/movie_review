"""movie_review URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path
from django.views.generic import TemplateView

from movie_review_app import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
                  path('api/<str:module>/', views.SystemView.as_view()),
                  path('api/upload/<str:module>/', views.AvatarView.as_view()),
                  path('api/users/<str:module>/', views.UsersView.as_view()),
                  path('api/admins/<str:module>/', views.AdminsView.as_view()),
                  path('api/movies/<str:module>/', views.MoviesView.as_view()),
                  path('api/reviewlogs/<str:module>/', views.ReviewLogsView.as_view()),
                  path('',TemplateView.as_view(template_name="index.html"))
                  # path('favoriatelists/<str:module>/', views.FavoriateListsView.as_view()),

                  # path('favoriatelists/<str:module>/', views.FavoriateListsView.as_view()),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




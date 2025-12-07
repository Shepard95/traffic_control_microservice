from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/checkpoints/', views.api_checkpoints, name='checkpoints'),
    path('api/checkpoint/<str:filename>/', views.api_checkpoint, name='checkpoint'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),                   
    path('chatbot_api/', views.chatbot_api, name='chatbot_api'),
    path('search/', views.search, name='search'),      
]

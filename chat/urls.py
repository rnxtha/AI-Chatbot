from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('api/chat/', views.api_chat, name='api_chat'),
    path('api/run_code/', views.api_run_code, name='api_run_code'),
]

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login', auth_views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', auth_views.logout, {'next_page': '/'}, name='logout'),
]

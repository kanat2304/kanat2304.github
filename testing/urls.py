from django.urls import path
from . import views

urlpatterns = [
    # Панели
    path('', views.dashboard, name='dashboard'),
    path('create/', views.upload_file, name='create'),
    path('history/', views.history, name='history'),
    path('profile/', views.profile, name='profile'),

    # Функции
    path('delete/<int:test_id>/', views.delete_test, name='delete_test'), # <-- НОВОЕ: Удаление
    
    # Авторизация и Тесты
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('test/<int:test_id>/', views.take_test, name='take_test'),
]
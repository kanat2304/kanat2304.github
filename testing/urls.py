from django.urls import path
from . import views

urlpatterns = [
    # Басты бет (Панель)
    path('', views.dashboard, name='dashboard'),
    
    # Тест жасау және басқару
    path('create/', views.upload_file, name='create'),
    path('history/', views.history, name='history'),
    path('delete/<int:test_id>/', views.delete_test, name='delete_test'),
    
    # Профиль және Авторизация
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    
    # Тест тапсыру процесі
    path('test/<int:test_id>/', views.take_test, name='take_test'),
    
    # --- ЖАҢА ЖОЛ: Нәтиже және қатемен жұмыс ---
    path('result/<int:result_id>/', views.test_result, name='test_result'),
]
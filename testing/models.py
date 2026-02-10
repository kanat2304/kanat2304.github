from django.db import models
from django.contrib.auth.models import User

class Test(models.Model):
    MODE_CHOICES = [
        ('lite', 'Лайт (Ескерту ғана)'),
        ('hard', 'Қатаң (Тесттен шықса бітеді)'),
    ]

    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Настройки теста
    time_limit = models.IntegerField(default=20, verbose_name="Уақыт (минут)")
    # Сколько вопросов показывать ученику (из общего пула)
    questions_to_show = models.IntegerField(default=10, verbose_name="Көрсетілетін сұрақ саны")
    # Режим сложности
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='lite', verbose_name="Режим")
    
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    test = models.ForeignKey(Test, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.IntegerField()

class StudentResult(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=100)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)
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
    
    # --- БАПТАУЛАР ---
    
    # 1. Уақыт шектеуі (минутпен)
    time_limit = models.IntegerField(default=20, verbose_name="Уақыт (минут)")
    
    # 2. Оқушы санына лимит (Мысалы: тек 20 оқушы кіре алады)
    max_students = models.IntegerField(default=100, verbose_name="Максималды оқушы саны")
    
    # 3. Әр оқушыға қанша сұрақ көрсету керек? (Мысалы: 100 сұрақтың ішінен 20-сы)
    questions_to_show = models.IntegerField(default=20, verbose_name="Сұрақ саны (Студентке)")
    
    # 4. Қауіпсіздік режимі
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
    # Дұрыс жауап индексі (1, 2, 3 немесе 4)
    correct_option = models.IntegerField()

    def __str__(self):
        return self.text[:50]

class StudentResult(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=100)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)
    
    # Оқушының жауаптарын сақтайтын өріс (JSON)
    # Мысалы: {"105": 2, "106": 1} -> 105-сұраққа B, 106-сұраққа A таңдады
    student_answers = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.student_name} - {self.test.title}"
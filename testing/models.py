from django.db import models
from django.contrib.auth.models import User

class Test(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # Жаңа өріс: Уақыт шектеуі (минутпен), егер белгілемесе 20 минут тұрады
    time_limit = models.IntegerField(default=20, verbose_name="Уақыт (минут)")
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
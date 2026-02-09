from django.contrib import admin
from .models import Test, Question, StudentResult

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class TestAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]

admin.site.register(Test, TestAdmin)
admin.site.register(StudentResult)
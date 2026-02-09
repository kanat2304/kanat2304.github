import google.generativeai as genai
import PyPDF2
import docx
import json
import random
import csv
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from .models import Test, Question, StudentResult

# --- GEMINI API БАПТАУ ---
def get_configured_genai():
    keys = getattr(settings, 'GEMINI_KEYS', [])
    if not keys: return None
    genai.configure(api_key=random.choice(keys))
    return genai

def extract_text(file):
    try:
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            return "".join([page.extract_text() for page in reader.pages])
        elif file.name.endswith('.docx'):
            doc = docx.Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
    except: return None
    return ""

# --- 1. DASHBOARD ---
@login_required(login_url='user_login')
def dashboard(request):
    tests = Test.objects.filter(teacher=request.user)
    
    # График деректері
    test_titles = []
    student_counts = []
    for test in tests:
        count = StudentResult.objects.filter(test=test).count()
        if count > 0:
            test_titles.append(test.title)
            student_counts.append(count)
    
    # РЕЙТИНГ
    leaderboard = StudentResult.objects.filter(test__teacher=request.user) \
        .values('student_name') \
        .annotate(total_score=Sum('score')) \
        .order_by('-total_score')[:3]

    context = {
        'total_tests': tests.count(),
        'total_students': StudentResult.objects.filter(test__teacher=request.user).count(),
        'chart_labels': json.dumps(test_titles),
        'chart_data': json.dumps(student_counts),
        'leaderboard': leaderboard
    }
    return render(request, 'dashboard.html', context)

# --- 2. CREATE (ТЕСТ ЖАСАУ) ---
@login_required(login_url='user_login')
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            title = request.POST.get('title')
            q_count = request.POST.get('question_count', 5)
            time = request.POST.get('time_limit', 20)
            text = extract_text(request.FILES['document'])
            
            if not text: return render(request, 'upload.html', {'error': "Файл бос!"})

            ai = get_configured_genai()
            model = ai.GenerativeModel('gemini-flash-latest')
            prompt = f"Create {q_count} multiple choice questions. Return JSON: [{{'question':'Q','options':['A','B'],'correct':0}}]. Text: {text[:4000]}"
            
            data = json.loads(model.generate_content(prompt).text.replace("```json","").replace("```","").strip())
            new_test = Test.objects.create(teacher=request.user, title=title, time_limit=time)
            for q in data:
                Question.objects.create(test=new_test, text=q['question'], option1=q['options'][0], option2=q['options'][1], option3=q['options'][2], option4=q['options'][3], correct_option=q['correct']+1)
            return redirect('history')
        except Exception as e: return render(request, 'upload.html', {'error': f"Қате: {e}"})
    return render(request, 'upload.html')

# --- 3. HISTORY & TOOLS ---
@login_required(login_url='user_login')
def history(request):
    my_tests = Test.objects.filter(teacher=request.user).order_by('-id')
    results = StudentResult.objects.filter(test__teacher=request.user).order_by('-date_taken')
    return render(request, 'history.html', {'my_tests': my_tests, 'results': results})

@login_required(login_url='user_login')
def delete_test(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    test.delete()
    return redirect('history')

@login_required(login_url='user_login')
def export_results(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{test.title}_results.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['Оқушы аты', 'Балл', 'Сұрақ саны', 'Уақыты'])
    for r in StudentResult.objects.filter(test=test).order_by('-score'):
        writer.writerow([r.student_name, r.score, r.total_questions, r.date_taken.strftime("%d.%m.%Y %H:%M")])
    return response

def generate_qr(request, test_id):
    link = request.build_absolute_uri(f'/test/{test_id}/')
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response

@login_required(login_url='user_login')
def print_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    return render(request, 'print_test.html', {'test': test})

# --- 4. AUTH ---
@login_required(login_url='user_login')
def profile(request): return render(request, 'profile.html', {'user': request.user})

def register(request):
    if request.method == 'POST':
        u, p, pc = request.POST.get('username'), request.POST.get('password'), request.POST.get('password_confirm')
        if p!=pc: messages.error(request, "Парольдер сәйкес емес!"); return redirect('register')
        if User.objects.filter(username=u).exists(): messages.error(request, "Логин бос емес!"); return redirect('register')
        user = User.objects.create_user(u, p); login(request, user); return redirect('dashboard')
    return render(request, 'register.html')

def user_login(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user: login(request, user); return redirect('dashboard')
        else: messages.error(request, "Қате логин/пароль!")
    return render(request, 'login.html')

def user_logout(request): logout(request); return redirect('user_login')

# --- 5. TEST TAKING (SMART SHUFFLE) ---
def take_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        score = 0
        questions = test.questions.all()
        for question in questions:
            # HTML-де сұрақ ID-мен келеді (question_5), реті маңызды емес
            selected = request.POST.get(f'question_{question.id}')
            if selected and int(selected) == question.correct_option:
                score += 1
        
        StudentResult.objects.create(test=test, student_name=student_name, score=score, total_questions=questions.count())
        return render(request, 'result.html', {'score': score, 'total': questions.count(), 'student': student_name, 'test': test})
    
    # GET СҰРАНЫС: АРАЛАСТЫРУ (SHUFFLE)
    questions_list = list(test.questions.all())
    random.shuffle(questions_list) # 🔥 Сұрақтарды араластырамыз
    
    return render(request, 'test.html', {'test': test, 'questions': questions_list})
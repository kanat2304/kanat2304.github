import google.generativeai as genai
import PyPDF2
import docx
import json
import random
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from .models import Test, Question, StudentResult
from dotenv import load_dotenv

load_dotenv()

# --- GEMINI БАПТАУЫ ---
def get_configured_genai():
    keys = getattr(settings, 'GEMINI_KEYS', [])
    if not keys:
        env_key = os.getenv("GEMINI_API_KEYS")
        if env_key: keys = [k.strip() for k in env_key.split(',') if k.strip()]
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
    # (Бұл бөлік өзгеріссіз қалады)
    tests = Test.objects.filter(teacher=request.user)
    student_counts = [StudentResult.objects.filter(test=t).count() for t in tests]
    test_titles = [t.title for t in tests]
    
    context = {
        'total_tests': tests.count(),
        'total_students': StudentResult.objects.filter(test__teacher=request.user).count(),
        'chart_labels': json.dumps(test_titles),
        'chart_data': json.dumps(student_counts),
    }
    return render(request, 'dashboard.html', context)

# --- 2. CREATE (ТЕСТ ЖҮКТЕУ - AI ПАРСЕР) ---
@login_required(login_url='user_login')
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            title = request.POST.get('title')
            
            # Енді "AI қанша сұрақ жасасын" деген жоқ, себебі файлда қанша бар - соның бәрін аламыз
            questions_to_show = int(request.POST.get('questions_to_show', 20)) 
            max_students = int(request.POST.get('max_students', 100))
            time = int(request.POST.get('time_limit', 20))
            mode = request.POST.get('mode', 'lite')
            
            text = extract_text(request.FILES['document'])
            if not text: return render(request, 'upload.html', {'error': "Файл оқылмады!"})

            ai = get_configured_genai()
            if not ai: return render(request, 'upload.html', {'error': "API Key қате!"})

            model = ai.GenerativeModel('gemini-flash-latest')
            
            # --- ЖАҢА PROMPT (БҰЙРЫҚ) ---
            # Біз AI-ға сұрақ құрастыр демейміз, файлдағы дайын сұрақтарды ал дейміз.
            prompt = f"""
            Analyze the following text which contains a list of multiple choice questions created by a teacher.
            Task: Extract all questions, options, and the correct answer.
            
            Rules:
            1. Return strictly a JSON Array of objects.
            2. Format: [{{"question": "Text", "options": ["A", "B", "C", "D"], "correct": 0}}]
            3. "correct" is the index (0 for A, 1 for B, 2 for C, 3 for D).
            4. If the correct answer is marked in the text (e.g. bold, *, +), use it.
            5. If not marked, try to solve it yourself and set the correct index.
            
            Text to process:
            {text[:15000]}
            """
            
            response = model.generate_content(prompt)
            json_text = response.text.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(json_text)
            except:
                # Егер JSON бұзылса, тазалап көреміз
                start = json_text.find('[')
                end = json_text.rfind(']') + 1
                data = json.loads(json_text[start:end])
            
            # Тестті сақтау
            new_test = Test.objects.create(
                teacher=request.user, 
                title=title, 
                time_limit=time,
                questions_to_show=questions_to_show,
                max_students=max_students,
                mode=mode
            )
            
            # Сұрақтарды базаға енгізу
            count = 0
            for q in data:
                opts = q.get('options', [])
                # Вариант жетіспесе, "-" қоямыз
                while len(opts) < 4: opts.append("-")
                
                Question.objects.create(
                    test=new_test, 
                    text=q['question'], 
                    option1=opts[0], 
                    option2=opts[1], 
                    option3=opts[2], 
                    option4=opts[3], 
                    correct_option=q['correct'] + 1
                )
                count += 1
            
            return redirect('history')
        except Exception as e: 
            return render(request, 'upload.html', {'error': f"Қате: {e}. Файлды тексеріңіз."})
            
    return render(request, 'upload.html')

# --- 3. TEST TAKING (ТАПСЫРУ + РАНДОМ) ---
def take_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    # ЛИМИТТІ ТЕКСЕРУ
    current_students = StudentResult.objects.filter(test=test).count()
    if current_students >= test.max_students:
        return HttpResponse("<h1 style='text-align:center; margin-top:50px;'>⛔ Бұл тестке орын қалмады!</h1>")

    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        score = 0
        user_answers = {}
        question_ids = request.POST.getlist('q_ids')
        
        for q_id in question_ids:
            try:
                question = Question.objects.get(id=q_id)
                selected = request.POST.get(f'question_{q_id}')
                if selected:
                    user_answers[str(q_id)] = int(selected)
                    if int(selected) == question.correct_option: score += 1
                else:
                    user_answers[str(q_id)] = None
            except: continue
        
        result = StudentResult.objects.create(
            test=test, student_name=student_name, score=score, 
            total_questions=len(question_ids), student_answers=user_answers
        )
        return redirect('test_result', result_id=result.id)
    
    # --- GET: СҰРАҚТАРДЫ АРАЛАСТЫРУ ---
    all_questions = list(test.questions.all()) # Файлдан алынған барлық сұрақтар
    
    if not all_questions:
        return HttpResponse("Сұрақтар жүктелмеген.")

    random.shuffle(all_questions) # <--- Араластыру (Shuffle)
    
    limit = min(test.questions_to_show, len(all_questions))
    selected_questions = all_questions[:limit]
    
    return render(request, 'test.html', {'test': test, 'questions': selected_questions})

# ... (Басқа функциялар: test_result, history, auth өзгеріссіз қалады) ...
# (Оларды алдыңғы жауаптардан көшіріп алсаңыз болады немесе сұрасаңыз толық жіберемін)
# Төменде маңыздыларын қысқаша қостым:

def test_result(request, result_id):
    result = get_object_or_404(StudentResult, id=result_id)
    analysis = []
    for q_id, selected_opt in result.student_answers.items():
        try:
            question = Question.objects.get(id=int(q_id))
            analysis.append({
                'question': question, 'selected': selected_opt,
                'is_correct': (selected_opt == question.correct_option),
                'correct_opt': question.correct_option
            })
        except: continue
    return render(request, 'result.html', {'result': result, 'analysis': analysis})

def history(request):
    my_tests = Test.objects.filter(teacher=request.user).order_by('-id')
    results = StudentResult.objects.filter(test__teacher=request.user).order_by('-date_taken')
    return render(request, 'history.html', {'my_tests': my_tests, 'results': results})

@login_required
def delete_test(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    test.delete()
    return redirect('history')

# (Auth функцияларын қысқарттым, олар өзгерген жоқ)
def user_login(request): return render(request, 'login.html') # Login логикасын қосыңыз
def profile(request): return render(request, 'profile.html', {'user': request.user})
def register(request): return render(request, 'register.html') # Register логикасын қосыңыз
def user_logout(request): return redirect('user_login')
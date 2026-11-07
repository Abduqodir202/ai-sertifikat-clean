import json, urllib.request, urllib.error
from datetime import timedelta
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import ExamQuestion, ExamAttempt

COUNT=45
MINUTES=150
def owned(request, public_id):
    qs=ExamAttempt.objects.filter(public_id=public_id)
    if request.user.is_authenticated: qs=qs.filter(user=request.user)
    else:
        if not request.session.session_key: request.session.create()
        qs=qs.filter(session_key=request.session.session_key,user__isnull=True)
    return get_object_or_404(qs)
def finish(attempt):
    if attempt.status=="submitted": return
    bank={str(q.id):q for q in ExamQuestion.objects.filter(id__in=attempt.question_ids)}
    c=w=u=0
    for qid in attempt.question_ids:
        q=bank.get(str(qid)); ans=attempt.answers.get(str(qid))
        if not ans: u+=1
        elif q and ans==q.correct_option: c+=1
        else: w+=1
    attempt.correct_count=c; attempt.wrong_count=w; attempt.unanswered_count=u
    attempt.percent=round(c*100/max(len(attempt.question_ids),1),2)
    attempt.status="submitted"; attempt.submitted_at=timezone.now()
    attempt.save(update_fields=["correct_count","wrong_count","unanswered_count","percent","status","submitted_at"])
@ensure_csrf_cookie
def exam_page(request):
    if not request.session.session_key: request.session.create()
    return render(request,"mathexam/exam.html")
@require_POST
def start_exam(request):
    if not request.session.session_key: request.session.create()
    qs=ExamAttempt.objects.filter(status="in_progress")
    qs=qs.filter(user=request.user) if request.user.is_authenticated else qs.filter(session_key=request.session.session_key,user__isnull=True)
    active=qs.order_by("-started_at").first()
    if active:
        if timezone.now()>=active.deadline: finish(active)
        else: return JsonResponse({"attempt_id":str(active.public_id),"resumed":True})
    questions=list(ExamQuestion.objects.filter(is_active=True).order_by("?")[:COUNT])
    if len(questions)<COUNT: return JsonResponse({"error":f"Imtihon uchun 45 ta faol savol kerak. Hozir {len(questions)} ta."},status=400)
    a=ExamAttempt.objects.create(user=request.user if request.user.is_authenticated else None,session_key=request.session.session_key,question_ids=[q.id for q in questions],deadline=timezone.now()+timedelta(minutes=MINUTES))
    return JsonResponse({"attempt_id":str(a.public_id),"resumed":False})
@require_GET
def exam_state(request):
    a=owned(request,request.GET.get("attempt_id"))
    if a.status=="in_progress" and timezone.now()>=a.deadline: finish(a)
    bank={q.id:q for q in ExamQuestion.objects.filter(id__in=a.question_ids)}
    ordered=[bank[i] for i in a.question_ids if i in bank]
    qs=[{"id":q.id,"number":n+1,"text":q.text,"options":{"A":q.option_a,"B":q.option_b,"C":q.option_c,"D":q.option_d},"topic":q.topic,"difficulty":q.difficulty,"answer":a.answers.get(str(q.id))} for n,q in enumerate(ordered)]
    out={"attempt_id":str(a.public_id),"status":a.status,"remaining_seconds":max(0,int((a.deadline-timezone.now()).total_seconds())) if a.status=="in_progress" else 0,"questions":qs}
    if a.status=="submitted":
        out["summary"]={"correct":a.correct_count,"wrong":a.wrong_count,"unanswered":a.unanswered_count,"percent":float(a.percent)}
        out["review"]=[{"number":n+1,"id":q.id,"text":q.text,"options":{"A":q.option_a,"B":q.option_b,"C":q.option_c,"D":q.option_d},"selected":a.answers.get(str(q.id)),"correct":q.correct_option,"explanation":q.explanation,"topic":q.topic} for n,q in enumerate(ordered)]
    return JsonResponse(out)
@require_POST
def save_answer(request):
    try:
        d=json.loads(request.body or "{}"); a=owned(request,d.get("attempt_id"))
        qid=str(d.get("question_id")); choice=d.get("answer")
        if a.status!="in_progress" or timezone.now()>=a.deadline:
            finish(a); return JsonResponse({"error":"Imtihon yakunlangan"},status=409)
        if not qid.isdigit() or int(qid) not in a.question_ids: return JsonResponse({"error":"Savol ushbu imtihonga tegishli emas"},status=400)
        if choice not in ("A","B","C","D",None,""): return JsonResponse({"error":"Javob formati noto‘g‘ri"},status=400)
        if choice: a.answers[qid]=choice
        else: a.answers.pop(qid,None)
        a.save(update_fields=["answers"])
        return JsonResponse({"saved":True})
    except (ValueError,TypeError,json.JSONDecodeError): return JsonResponse({"error":"Noto‘g‘ri so‘rov"},status=400)
@require_POST
def submit_exam(request):
    try:
        d=json.loads(request.body or "{}"); a=owned(request,d.get("attempt_id")); finish(a)
        return JsonResponse({"submitted":True,"correct":a.correct_count,"wrong":a.wrong_count,"unanswered":a.unanswered_count,"percent":float(a.percent)})
    except (ValueError,TypeError,json.JSONDecodeError): return JsonResponse({"error":"Noto‘g‘ri so‘rov"},status=400)
@require_GET
def exam_history(request):
    if request.user.is_authenticated: qs=ExamAttempt.objects.filter(user=request.user)
    else:
        if not request.session.session_key: request.session.create()
        qs=ExamAttempt.objects.filter(session_key=request.session.session_key,user__isnull=True)
    return JsonResponse({"history":[{"id":str(a.public_id),"date":a.started_at.strftime("%d.%m.%Y %H:%M"),"status":a.status,"correct":a.correct_count,"wrong":a.wrong_count,"unanswered":a.unanswered_count,"percent":float(a.percent)} for a in qs[:30]]})
@require_POST
def ai_explain(request):
    try:
        d=json.loads(request.body or "{}"); a=owned(request,d.get("attempt_id")); qid=int(d.get("question_id"))
        if qid not in a.question_ids: return JsonResponse({"error":"Savol topilmadi"},status=404)
        q=get_object_or_404(ExamQuestion,pk=qid); key=getattr(settings,"OPENAI_API_KEY","")
        if not key: return JsonResponse({"explanation":q.explanation or "Administrator ushbu savolga yechim izohini kiritmagan.","source":"database"})
        prompt=f"O‘zbek tilida bosqichma-bosqich tushuntir. Savol: {q.text}\nA: {q.option_a}\nB: {q.option_b}\nC: {q.option_c}\nD: {q.option_d}\nTo‘g‘ri javob: {q.correct_option}\nIzoh: {q.explanation}"
        body=json.dumps({"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"temperature":0.2}).encode()
        req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=25) as r: answer=json.loads(r.read().decode())["choices"][0]["message"]["content"]
        return JsonResponse({"explanation":answer,"source":"ai"})
    except urllib.error.HTTPError as e: return JsonResponse({"error":f"AI API xatosi: {e.code}"},status=502)
    except Exception: return JsonResponse({"error":"AI tushuntirish xizmatida xatolik"},status=502)

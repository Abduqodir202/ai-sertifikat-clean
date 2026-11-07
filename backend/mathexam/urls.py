from django.urls import path
from . import views
app_name="mathexam"
urlpatterns=[
 path("",views.exam_page,name="home"),
 path("api/start/",views.start_exam,name="start"),
 path("api/state/",views.exam_state,name="state"),
 path("api/answer/",views.save_answer,name="answer"),
 path("api/submit/",views.submit_exam,name="submit"),
 path("api/history/",views.exam_history,name="history"),
 path("api/explain/",views.ai_explain,name="explain"),
]

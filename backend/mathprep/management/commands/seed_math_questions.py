from django.core.management.base import BaseCommand
from mathprep.models import Question

# Savollar mustaqil tuzilgan mashq savollari. Ular rasmiy imtihon savollari emas.
DATA = [
("numbers","easy","Hisoblang: 3/4 + 1/2",["1","5/4","4/6","3/8"],1,"1/2 = 2/4, demak 3/4 + 2/4 = 5/4."),
("numbers","easy","0,25 sonini oddiy kasr ko‘rinishida yozing.",["1/2","1/4","1/5","3/4"],1,"0,25 = 25/100 = 1/4."),
("numbers","medium","240 sonining 15 foizini toping.",["24","30","36","40"],2,"240 × 0,15 = 36."),
("numbers","medium","|−7| + |3−8| ni hisoblang.",["2","10","12","−12"],2,"|−7|=7 va |−5|=5. Yig‘indi 12. To‘g‘ri variant C bo‘lishi kerak."),
("numbers","hard","Agar a:b=3:5 va a+b=64 bo‘lsa, b ni toping.",["24","32","40","48"],2,"Jami 8 ulush 64 ga teng, 1 ulush 8. b=5×8=40."),
("algebra","easy","Soddalashtiring: 4x + 3x − 2x.",["5x","9x","x","6x"],0,"Bir xil hadlar: (4+3−2)x=5x."),
("algebra","easy","(a+2)(a−2) ifodani oching.",["a²+4","a²−4","a²−2","a²+2"],1,"Kvadratlar ayirmasi: (a+2)(a−2)=a²−4."),
("algebra","medium","(x²−16)/(x−4), x≠4 ifodani soddalashtiring.",["x−4","x+4","x²+4","4"],1,"x²−16=(x−4)(x+4), qisqartirganda x+4."),
("algebra","medium","Agar 2a−3b=7 va a=5 bo‘lsa, b ni toping.",["1","2","3","4"],0,"10−3b=7, 3b=3, b=1. To‘g‘ri variant A."),
("algebra","hard","x+y=7 va xy=10 bo‘lsa, x²+y² ni toping.",["19","29","39","49"],1,"x²+y²=(x+y)²−2xy=49−20=29."),
("equations","easy","2x+5=17 tenglamani yeching.",["5","6","7","11"],1,"2x=12, x=6."),
("equations","easy","5x=−25 bo‘lsa, x ni toping.",["−5","5","−20","20"],0,"x=−25/5=−5."),
("equations","medium","x²−7x+12=0 tenglamaning katta ildizini toping.",["2","3","4","6"],2,"(x−3)(x−4)=0. Katta ildiz 4."),
("equations","medium","3x−4>11 tengsizlikni yeching.",["x>5","x<5","x>7","x<7"],0,"3x>15, demak x>5."),
("equations","hard","x²−4x−5=0 tenglamaning ildizlari ko‘paytmasini toping.",["−5","−4","4","5"],0,"Viyet teoremasiga ko‘ra c/a=−5."),
("functions","easy","f(x)=3x−2 bo‘lsa, f(4) ni toping.",["8","10","12","14"],1,"f(4)=12−2=10."),
("functions","medium","f(x)=x²−3x bo‘lsa, f(−2) ni toping.",["−2","2","10","14"],2,"4+6=10. To‘g‘ri variant C."),
("functions","medium","y=2x+6 chiziqning Oy o‘qi bilan kesishish nuqtasini toping.",["(0;2)","(0;6)","(6;0)","(−3;0)"],1,"x=0 bo‘lganda y=6."),
("functions","hard","f(x)=x²−4x+1 funksiyaning eng kichik qiymatini toping.",["−4","−3","−2","1"],1,"f(x)=(x−2)²−3, minimum −3."),
("analysis","easy","f(x)=x² bo‘lsa, f′(x) ni toping.",["x","2x","x²","2"],1,"Daraja qoidasiga ko‘ra (x²)'=2x."),
("analysis","medium","f(x)=x³−2x bo‘lsa, f′(2) ni toping.",["8","10","12","14"],1,"f′=3x²−2; f′(2)=12−2=10. To‘g‘ri variant B."),
("analysis","medium","∫ 2x dx ni toping.",["x²+C","2x²+C","x+C","2+C"],0,"∫2x dx=x²+C."),
("analysis","hard","f(x)=x³−6x²+9x funksiyaning kritik nuqtalarini toping.",["1 va 3","−1 va −3","0 va 3","2 va 4"],0,"f′=3x²−12x+9=3(x−1)(x−3)."),
("probability","easy","Qutida 3 qizil, 2 ko‘k shar bor. Qizil shar olish ehtimoli?",["1/5","2/5","3/5","1/2"],2,"3 ta qulay holat, jami 5 ta: 3/5."),
("probability","medium","Tanga ikki marta tashlandi. Aynan bir marta gerb tushish ehtimoli?",["1/4","1/2","3/4","1"],1,"Natijalar GG, GR, RG, RR. Ikki holat mos: 2/4=1/2."),
("probability","medium","4, 6, 8, 10 sonlarining arifmetik o‘rtachasini toping.",["6","7","8","9"],1,"(4+6+8+10)/4=7."),
("probability","hard","Ikki kubik tashlanganda yig‘indi 7 bo‘lish ehtimoli?",["1/12","1/9","1/6","1/3"],2,"36 teng imkoniyatli natijadan 6 tasi yig‘indi 7 beradi: 6/36=1/6."),
("geometry","easy","Uchburchak burchaklari 50° va 60°. Uchinchi burchak?",["60°","70°","80°","90°"],1,"180°−50°−60°=70°."),
("geometry","easy","Tomonlari 5 va 12 bo‘lgan to‘g‘ri to‘rtburchak perimetri?",["17","30","34","60"],2,"P=2(5+12)=34."),
("geometry","medium","Katetlari 6 va 8 bo‘lgan to‘g‘ri burchakli uchburchak gipotenuzasi?",["9","10","12","14"],1,"√(6²+8²)=√100=10."),
("geometry","medium","Radiusi 4 bo‘lgan doira yuzi?",["4π","8π","16π","32π"],2,"S=πr²=16π."),
("geometry","hard","Tomoni 6 bo‘lgan kvadratga ichki chizilgan aylana radiusini toping.",["2","3","4","6"],1,"Ichki aylana diametri kvadrat tomoniga teng: r=6/2=3."),
# 13 savol qolgan mavzularda qo'shimcha imtihon zaxirasi
("numbers","hard","1/(1/3+1/6) qiymatini toping.",["1","2","3","6"],1,"1/3+1/6=1/2; uning teskarisi 2. To‘g‘ri javob B."),
("algebra","hard","x−1/x=3 bo‘lsa, x²+1/x² ni toping.",["7","9","11","13"],2,"(x−1/x)²=x²−2+1/x²=9, demak 11."),
("equations","hard","|2x−6|=8 tenglamaning ildizlari yig‘indisini toping.",["3","6","8","12"],1,"2x−6=8 yoki −8; ildizlar 7 va −1, yig‘indi 6."),
("functions","hard","y=−x²+4x+1 parabolaning cho‘qqi ordinatasini toping.",["1","4","5","6"],2,"Cho‘qqi x=−b/2a=2; y=−4+8+1=5."),
("analysis","hard","f(x)=5x⁴−3x²+1 bo‘lsa, f′(1) ni toping.",["8","10","14","17"],2,"f′=20x³−6x; f′(1)=14. To‘g‘ri javob C."),
("probability","hard","5 ta turli kitobdan 2 tasini tanlash usullari soni?",["5","10","20","25"],1,"C(5,2)=5·4/2=10."),
("geometry","hard","Uchburchak tomonlari 13, 14, 15. Geron formulasi bo‘yicha yuzini toping.",["72","84","90","96"],1,"p=21; S=√(21·8·7·6)=√7056=84."),
("numbers","medium","√144 + 2³ ni hisoblang.",["16","18","20","24"],2,"12+8=20. To‘g‘ri javob C."),
("algebra","medium","3(x−2)=2x+5 tenglamani yeching.",["7","9","11","13"],2,"3x−6=2x+5, x=11."),
("equations","medium","x²=49 tenglamaning manfiy ildizini toping.",["−7","−1","1","7"],0,"x=±7; manfiy ildiz −7."),
("functions","easy","y=−2x+1 funksiyada x=0 bo‘lsa, y nechaga teng?",["−2","−1","0","1"],3,"y=−2·0+1=1."),
("analysis","easy","Doimiy 7 funksiyaning hosilasi nechaga teng?",["0","1","7","−7"],0,"Doimiy funksiyaning hosilasi 0."),
("probability","easy","Qopda 1 dan 5 gacha raqamlangan 5 shar bor. Juft raqam olish ehtimoli?",["1/5","2/5","3/5","4/5"],1,"Juft raqamlar 2 va 4: 2/5."),
("geometry","easy","Kvadrat tomoni 7. Uning yuzi?",["14","28","49","56"],2,"S=7²=49."),
("geometry","medium","Asosi 10, balandligi 6 bo‘lgan uchburchak yuzi?",["16","30","60","40"],1,"S=(10·6)/2=30."),
]

class Command(BaseCommand):
    help = "Matematika uchun boshlang'ich savollar bankini yuklaydi"

    def handle(self, *args, **options):
        created = 0
        for topic, level, text, choices, correct, explanation in DATA:
            # Matndagi tekshiruv izohlarini variant indeksiga moslab tozalash.
            if "To‘g‘ri variant" in explanation:
                explanation = explanation.split(" To‘g‘ri variant")[0]
            obj, was_created = Question.objects.get_or_create(
                text=text,
                defaults={
                    "topic": topic, "level": level, "options": choices,
                    "correct_index": correct, "explanation": explanation,
                    "source": "curated", "is_active": True,
                }
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"{created} ta savol qo‘shildi. Jami faol savollar: {Question.objects.filter(is_active=True).count()}."
        ))

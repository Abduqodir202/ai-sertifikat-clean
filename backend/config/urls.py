from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

from userprofile.views import (
    profile_page,
    register_view,
    essay_detail_page,
)


# Bosh sahifa
def home(request):
    return render(request, "html/index.html")


# Rus tili esse sahifasi
def rus_esse_page(request):
    return render(request, "html/rus-esse.html")


# Ona tili sahifasi
def ona_tili_page(request):
    return render(request, "html/ona-tili.html")


# Matematika sahifasi
def matematika_page(request):
    return render(request, "html/matematika.html")


def narxlar_page(request):
    return render(request, "html/narxlar.html")


def aloqa_page(request):
    return render(request, "html/aloqa.html")


urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # Bosh sahifa
    path("", home, name="home"),

    # Rus tili esse tekshirish sahifasi
    path("rus-esse/", rus_esse_page, name="rus_esse"),

    # Google orqali kirish va boshqa autentifikatsiya URL'lari
    path("accounts/", include("allauth.urls")),

    # Esse API
    path("api/", include("essays.urls")),

    # Foydalanuvchi API
    path("api/", include("userprofile.urls")),

    # Ro‘yxatdan o‘tish
    path("register/", register_view, name="register"),

    # Shaxsiy kabinet
    path("profile/", profile_page, name="profile"),

    # Esse natijasi
    path(
        "profile/essays/<int:essay_id>/",
        essay_detail_page,
        name="essay_detail",
    ),

    # Ona tili
    path("ona-tili/", ona_tili_page, name="ona_tili"),

    # Matematika
    path("matematika/", matematika_page, name="matematika"),
    path("narxlar/", narxlar_page, name="narxlar"),
    path("aloqa/", aloqa_page, name="aloqa"),
]


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


# Narxlar
def narxlar_page(request):
    return render(request, "html/narxlar.html")


# Aloqa
def aloqa_page(request):
    return render(request, "html/aloqa.html")


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", home, name="home"),

    path("rus-esse/", rus_esse_page, name="rus_esse"),

    path("accounts/", include("allauth.urls")),

    path("api/", include("essays.urls")),
    path("api/", include("userprofile.urls")),

    path("register/", register_view, name="register"),
    path("profile/", profile_page, name="profile"),

    path(
        "profile/essays/<int:essay_id>/",
        essay_detail_page,
        name="essay_detail",
    ),

    path("ona-tili/", ona_tili_page, name="ona_tili"),

    # YANGI MATEMATIKA TIZIMI
    path("matematika/", include("mathprep.urls")),

    path("narxlar/", narxlar_page, name="narxlar"),
    path("aloqa/", aloqa_page, name="aloqa"),
]

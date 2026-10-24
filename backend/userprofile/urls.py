
from django.urls import path
from .views import (
    my_profile,
    my_essays,
    register_view,
    profile_page,
    essay_detail_page,
)

urlpatterns = [
    # API: foydalanuvchi ma'lumotlari
    path("me/", my_profile, name="my-profile"),
    path("my-essays/", my_essays, name="my-essays"),

    # Ro'yxatdan o'tish
    path("register/", register_view, name="register"),

    # Profil sahifasi
    path("profile/", profile_page, name="profile"),

    # Esse batafsil natijasi
    path(
        "essay/<int:essay_id>/",
        essay_detail_page,
        name="essay-detail",
    ),
]

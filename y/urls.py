from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("user/<str:username>/", views.userView, name="user"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register")
]

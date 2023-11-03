from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:page>", views.index, name="indexPagination"),
    path("login", views.login_view, name="login"),
    path("user/<str:username>", views.userView, name="user"),
    path("user/<str:username>/<int:page>", views.userView, name="userPagination"),
    path("following", views.followingView, name="following"),
    path("following/<int:page>", views.followingView, name="followingPagination"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
]

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .forms import PostForm
from .models import User, Post


def index(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("index"))
        
        if "newPost" in request.POST:
            postFormInstance = PostForm(request.POST)
            if not postFormInstance.is_valid():
                return HttpResponseRedirect(reverse("index"))
            
            postData = postFormInstance.cleaned_data
            post = Post(
                poster=request.user,
                content=postData["content"]
            )
            post.save()
            return HttpResponseRedirect(reverse("index"))

    postForm = PostForm
    # awooga = Post(content="fjdskla", poster=request.user, date=timezone.now())
    # awooga = Post(content="fjdskla", poster=request.user)
    # awooga.save()
    # print(awooga, awooga.id)

    # testing = Post.objects.filter(poster=request.user)[0]
    # print(testing)
    # print(testing, testing.id, testing.poster, testing.date, testing.content)
    return render(request, "y/index.html", {"postForm": postForm})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "y/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "y/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "y/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "y/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "y/register.html")

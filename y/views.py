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
    # posts = Post.objects.all()
    posts = Post.objects.order_by("-date")

    return render(request, "y/index.html", {
        "postForm": postForm,
        # "posts": sorted(posts, key=lambda post: post.date, reverse=True),
        "posts": posts,
    })


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


def userView(request, username):
    userData = User.objects.get(username=username)

    if request.user.is_authenticated:
        if request.method == "POST":
            if "follow" in request.POST:
                try:
                    request.user.followUser(userData)
                except ValueError:
                    pass
                return HttpResponseRedirect(reverse("user", args=[username]))

            if "unfollow" in request.POST:
                request.user.following.remove(userData)
                return HttpResponseRedirect(reverse("user", args=[username]))

    posts = userData.user_posts.order_by("-date")
    selfPage = username == request.user.username
    isFollowed = bool(request.user.following.filter(username=username).count())
    return render(request, "y/user.html", {
        "userData": userData,
        "posts": posts,
        "followerAmount": userData.followerAmount(),
        "followingAmount": userData.followingAmount(),
        "selfPage": selfPage,
        "isFollowed": isFollowed,
    })

def followingView(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    posts = Post.objects.filter(poster__in=request.user.following.all()).order_by("-date")

    return render(request,  "y/following.html", {
        "posts": sorted(posts, key=lambda post: post.date, reverse=True),
    })
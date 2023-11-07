from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage

from .forms import PostForm
from .models import User, Post
import json


postsByPage = 10

# TODO: change the site structure so i render post list dynamically.
# create a new view and return the post list, receive it on the frontend and append.
# delete post lists from following, index and user templates and create a new template for posts.

def index(request, page="1"):
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

    return render(request, "y/index.html", {
        "postForm": postForm,
        "page": page,
    })

def pageNumberTooBigResponse(routeName, maxNumPage):
    return JsonResponse({
        "error": "Page number too big.", 
        "redirectTo": reverse(routeName, args=[maxNumPage]),
    }, status=400)

def userMustBeAuthenticatedResponse():
    return JsonResponse({
        "error": "User must be authenticated.", 
        "redirectTo": reverse("login"),
    }, status=400)

def userNotProvided():
    return JsonResponse({
        "error": "User not provided.", 
        "redirectTo": reverse("index"),
    }, status=400)

def userNotFound():
    return JsonResponse({
        "error": "User not found.", 
        "redirectTo": reverse("index"),
    }, status=400)

def feed(request):
    # TODO: fix likes in user page.
    user = None
    feed = request.GET.get("feed", "index")
    page = request.GET.get("page", "1")
    if feed == "index":
        pageUrl =  "indexPagination"
        result = fetchIndexFeed(request, page)
        if "error" in result:
            return pageNumberTooBigResponse("indexPagination", result["paginator"].num_pages)

    elif feed == "following":
        # if not request.user.is_authenticated:
        #     return userMustBeAuthenticatedResponse()
        pageUrl =  "followingPagination"
        result = fetchFollowingFeed(request, page)
        if "error" in result:
            if result["error"] == "User must be authenticated.":
                return userMustBeAuthenticatedResponse()
            elif result["error"] == "Empty page.":
                return pageNumberTooBigResponse("followingPagination", result["paginator"].num_pages)

    elif feed == "user":
        # user = User.objects.
        pageUrl =  "userPagination"
        username = request.GET.get("username", None)
        if username == None:
            return userNotProvided()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return userNotFound()

        result = fetchUserFeed(request, user, page)
        if "error" in result:
            return pageNumberTooBigResponse("userPagination", result["paginator"].num_pages)

        # redirect if not authenticated
        # if request.user.is_authenticated:
        #     return HttpResponseRedirect(reverse("index"))
    
    # return html response
    # print(result["nextPageNumber"], result["previousPageNumber"])
    print(f"previous: {result['previousPageNumber']}")
    print(f"next: {result['nextPageNumber']}")
    return render(request, "y/feed.html", {
        "isUserPage": True if feed == "user" else None,
        "pageUser": user,
        "pageUrl": pageUrl,
        "posts": result["posts"],
        "nextPageNumber": result["nextPageNumber"],
        "previousPageNumber": result["previousPageNumber"],
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


def userView(request, username, page="1"):
    # add try catch to handle no matching user
    userData = User.objects.get(username=username)

    pageInt = int(page)
    if pageInt < 1:
        return HttpResponseRedirect(reverse("index"))

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

    query = userData.user_posts.order_by("-date")

    paginator = Paginator(query, postsByPage)
    paginator.allow_empty_first_page = True

    try:
        pageObj = paginator.page(pageInt)
    except EmptyPage:
        return HttpResponseRedirect(reverse("userPagination", args=[request.user.username, paginator.num_pages]))

    previousPageNumber = pageInt - 1 if pageInt - 1 >= 1 else None

    nextPageExists = pageObj.has_next()

    nextPageNumber = pageObj.next_page_number() if nextPageExists else None

    posts = pageObj.object_list

    selfPage = username == request.user.username
    isFollowed = bool(request.user.following.filter(username=username).count())
    print(f"page num: {page}")
    return render(request, "y/user.html", {
        "page": page,
        "username": username,
        "userData": userData,
        "posts": posts,
        "followerAmount": userData.followerAmount(),
        "followingAmount": userData.followingAmount(),
        "selfPage": selfPage,
        "isFollowed": isFollowed,
        "previousPageNumber": previousPageNumber,
        "nextPageNumber": nextPageNumber,
    })

def followingView(request, page="1"):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    pageInt = int(page)
    if pageInt < 1:
        return HttpResponseRedirect(reverse("index"))

    query = Post.objects.filter(poster__in=request.user.following.all()).order_by("-date")
    paginator = Paginator(query, postsByPage)
    paginator.allow_empty_first_page = True

    try:
        pageObj = paginator.page(pageInt)
    except EmptyPage:
        return HttpResponseRedirect(reverse("followingPagination", args=[paginator.num_pages]))

    previousPageNumber = pageInt - 1 if pageInt - 1 >= 1 else None

    nextPageExists = pageObj.has_next()

    nextPageNumber = pageObj.next_page_number() if nextPageExists else None

    posts = pageObj.object_list

    return render(request, "y/following.html", {
        "page": page,
        "posts": posts,
        "previousPageNumber": previousPageNumber,
        "nextPageNumber": nextPageNumber,
    })

def editPost(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "You must be authenticated."}, status=400)

    try:
        post = Post.objects.get(id=id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post doesn't exist."}, status=400)

    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)

    if post.poster != request.user:
        return JsonResponse({"error": "You cannot edit someone elses post."}, status=400)

    data = json.loads(request.body)
    post.content = data["content"]
    post.save()
    return JsonResponse({"message": "Edit request sent successfully."}, status=201)

def likePost(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "You must be authenticated."}, status=400)

    try:
        post = Post.objects.get(id=id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post doesn't exist."}, status=400)

    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)

    post.toggleLikeBy(request.user)
    return JsonResponse({"message": "Like request sent successfully.", "likes": post.likes}, status=201)


def fetchIndexFeed(request, page="1"):
    query = Post.objects.order_by("-date")
    return paginate(request, query, page)

def fetchUserFeed(request, user, page="1"):
    # try:
    #     user = User.objects.get(username=username)
    # except User.DoesNotExist:
    #     return {
    #         "error": "User not found.",
    #     }

    # if request.user == user:
    #     return {
    #         "error": ""
    #     }
    query = user.user_posts.order_by("-date")
    return paginate(request, query, page)

def fetchFollowingFeed(request, page="1",):
    if not request.user.is_authenticated:
        return {
            "error": "User must be authenticated.",
        }
    query = Post.objects.filter(poster__in=request.user.following.all()).order_by("-date")
    return paginate(request, query, page)

    # make query based on feed
    # if feed == "index":
    #     query = Post.objects.order_by("-date")
    #     ...
    # elif feed == "following" or feed == "user":
    #     # redirect if not authenticated
    #     if request.user.is_authenticated:
    #         raise UserNotSignedIn
    #         # return HttpResponseRedirect(reverse("index"))
    #     ...
    #     if feed == "user":
    #         if otherUser == None:
    #             raise NoUserGiven
    #         otherUser.user_posts.order_by("-date")



def paginate(request, query, page="1"):
    pageInt = int(page)
    if pageInt < 1:
        return HttpResponseRedirect(reverse("index"))

    paginator = Paginator(query, postsByPage)
    paginator.allow_empty_first_page = True

    try:
        pageObj = paginator.page(pageInt)
    except EmptyPage:
        return {
            "error": "Empty page.",
            "paginator": paginator,
        }
        # raise PageNumberTooBig
        # return HttpResponseRedirect(reverse("indexPagination", args=[paginator.num_pages]))

    previousPageNumber = pageInt - 1 if pageInt - 1 >= 1 else None

    nextPageExists = pageObj.has_next()

    nextPageNumber = pageObj.next_page_number() if nextPageExists else None

    posts = pageObj.object_list
    if request.user.is_authenticated:
        for post in posts:
            if post in request.user.likedPosts.all():
                post.isLiked = True

    return {
        "posts": posts,
        "nextPageNumber": nextPageNumber,
        "previousPageNumber": previousPageNumber,
        "paginator": paginator,
    }


class PageNumberTooBig(BaseException):
    pass

class NoUserGiven(BaseException):
    pass

class UserNotSignedIn(BaseException):
    pass
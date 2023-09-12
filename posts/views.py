from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.http import HttpResponse
from django.core.paginator import Paginator
import datetime as dt
from .forms import PostForm, CommentForm
from .models import Post, Group, Follow
import subprocess
from django.shortcuts import render, get_object_or_404, redirect, reverse

User = get_user_model()


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post\
        .objects\
        .all()\
        .select_related("author")\
        .select_related("group")
    paginator = Paginator(post_list, 10)  # показывать по 10 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)  # получить записи с нужным смещением
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_post(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author")
    paginator = Paginator(posts, 10)  # показывать по 10 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number) # получить записи с нужным смещением
    return render(request, "group.html", {"group": group, "posts": posts, "page": page, "paginator": paginator})


@login_required
def new_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
        return render(request, "new.html", {"form": form})
    form = PostForm()
    return render(request, "new.html", {"form": form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        user=request.user.id, author=author)
    paginator = Paginator(author.posts.all(), 5)  # показывать по 5 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)  # получить записи с нужным смещением
    return render(
        request,
        'profile.html',
        {"users": author, 'page': page, 'paginator': paginator, 'following': following}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    items = post.comments.select_related("author")
    for item in items:
        print(item)
    form = CommentForm()
    # тут тело функции
    return render(request,
        'post.html',
        {"post": post, "form": form, "items": items, "author": post.author})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("post", post.author, post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", post.author, post_id)
    # Тут тело функции. Не забудьте проверить,
    # что текущий пользователь — это автор записи.
    # В качестве шаблона страницы редактирования укажите шаблон создания новой записи
    # который вы создали раньше (вы могли назвать шаблон иначе)
    return render(request, 'new.html', {"form": form, "post": post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("post", post.author, post_id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related("author", "group").filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)  # показывать по 5 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)  # получить записи с нужным смещением
    return render(request, "follow.html", {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    following = get_object_or_404(User, username=username)
    follower = request.user
    if follower != following and follower != following.follower:
        Follow.objects.get_or_create(user=follower, author=following)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    Follow.objects.filter(
        user=request.user,
        author=author
    ).delete()
    return redirect('profile', username)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
import django

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


NUMBER_TEN = 10


def get_paginator(posts, request):
    paginator = Paginator(posts, NUMBER_TEN)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request: django.http.HttpRequest) -> django.http.HttpResponse:
    """Return a HttpResponse whose content is filled with the result of calling
    django.template.loader.render_to_string() with the passed arguments.
    """
    template = 'posts/index.html'
    context = get_paginator(Post.objects.all(), request)
    return render(request, template, context)


def group_posts(request: django.http.HttpRequest,
                slug: str) -> django.http.HttpResponse:
    """Return a HttpResponse whose content is filled with the result of calling
    django.template.loader.render_to_string() with the passed arguments.
    """
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(get_paginator(group.posts.all(), request))
    return render(request, template, context)


def profile(request: django.http.HttpRequest,
            username: str) -> django.http.HttpResponse:
    """This view render profile page by its username."""
    author = get_object_or_404(User, username=username)
    context = {
        'author': author,
    }
    context.update(get_paginator(author.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request: django.http.HttpRequest,
                post_id: int) -> django.http.HttpResponse:
    """This view render profile page by its username."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    count_post = post.author.posts.count()
    comments = post.comments.all()
    context = {
        'author': post.author,
        'post': post,
        'count_post': count_post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author.username)
    context = {
        'form': form
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if post.author != request.user:
        return redirect('post:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {'form': form,
               'post': post,
               'is_edit': True
               }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@cache_page(60 * 15)
def my_view(request):
    return render(request, 'posts/index.html')


@login_required
def follow_index(request):
    """Информация о текущем пользователе доступа."""
    post = Post.objects.filter(Post, author=request.user)
    context = {
        'title': "Посты в подписке",
        'post': post,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", author)


@login_required
def profile_unfollow(request, username):
    """Дизлайк,отписка."""
    Follow.objects.filter(
        user=request.user, author__username=username
    ).delete()
    return redirect("posts:profile", username)

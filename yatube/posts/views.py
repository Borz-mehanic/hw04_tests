from django.core.paginator import Paginator
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import django

from .models import Post, Group, User
from .forms import PostForm


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
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(
    request: django.http.HttpRequest
) -> django.http.HttpResponseRedirect:
    """This view create new post in database."""
    if request.method != 'POST':
        form = PostForm()
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm(request.POST)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    form = PostForm(
        request.POST or None,
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

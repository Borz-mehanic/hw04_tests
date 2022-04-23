from django.core.paginator import Paginator
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import django

from .models import Post, Group, User
from .forms import PostForm


NUMBER_TEN = 10


def index(request: django.http.HttpRequest) -> django.http.HttpResponse:
    """Return a HttpResponse whose content is filled with the result of calling
    django.template.loader.render_to_string() with the passed arguments.
    """
    posts = Post.objects.all()
    paginator = Paginator(posts, NUMBER_TEN)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/index.html'
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request: django.http.HttpRequest,
                slug: str) -> django.http.HttpResponse:
    """Return a HttpResponse whose content is filled with the result of calling
    django.template.loader.render_to_string() with the passed arguments.
    """
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, NUMBER_TEN)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    context = {
        'title': f'Записи сообщества {slug}',
        'page_obj': page_obj,
        'posts': posts,
        'group': group,
    }
    return render(request, template, context)


def only_user_view(
    request: django.http.HttpRequest
) -> django.http.HttpResponseRedirect:
    """Для пользовательского просмотра"""
    if not request.user.is_authenticated:
        return redirect(reverse('django.contrib.auth.views.login'))


def profile(request: django.http.HttpRequest,
            username: str) -> django.http.HttpResponse:
    """This view render profile page by its username."""
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author.id)
    paginator = Paginator(posts, NUMBER_TEN)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts_count = Post.objects.filter(author=author).count()
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'post_count': posts_count,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: django.http.HttpRequest,
                post_id: int) -> django.http.HttpResponse:
    """This view render profile page by its username."""
    post = Post.objects.filter(id=post_id)
    context = {
        'post': post[0]
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
def post_edit(request: django.http.HttpRequest,
              post_id: int) -> django.http.HttpResponse:
    """This view edits the post by its id and saves changes in database."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)

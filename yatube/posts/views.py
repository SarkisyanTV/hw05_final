from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.db.models import Subquery

from .models import Post, Group, Comment, Follow, User
from .forms import PostForm, CommentForm
# Open Index

POSTS_LIMIT = 10


def get_paginator(request, posts):
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(2)
def index(request):
    post_list = Post.objects.all()
    title = 'Yatube'
    main_header = 'Последние обновления на сайте'
    context = {
        'title': title,
        'main_header': main_header,
        'page_obj': get_paginator(request, post_list),
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    main_header = group.description
    group_name = group
    context = {
        'main_header': main_header,
        'group_name': group_name,
        'group': group,
        'page_obj': get_paginator(request, post_list),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    title = username
    user_obj = get_object_or_404(User, username=username)
    post_list = user_obj.posts.all()
    post_count = post_list.count()
    following = user_obj.following.filter(user_id=request.user.id).exists()
    context = {
        'following': following,
        'author': user_obj,
        'title': title,
        'post_count': post_count,
        'page_obj': get_paginator(request, post_list),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_unit = get_object_or_404(Post, id=post_id)
    posts = post_unit.author.posts.all()
    count = posts.count()
    title = post_unit.text
    form = CommentForm()
    comments = Comment.objects.all().filter(post_id=post_id)
    context = {
        'title': title,
        'post_unit': post_unit,
        'count': count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request, post=None):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'post': post}
        )
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    elif form.is_valid() and request.POST:
        post.text = form.cleaned_data['text']
        post.group = form.cleaned_data['group']
        post.image = form.cleaned_data['image']
        post = form.save(commit=False)
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(
        request, 'posts/create_post.html',
        {'form': form, 'is_edit': is_edit, 'post': post})


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


@login_required
def follow_index(request):
    follow_ob = Follow.objects.all().filter(user=request.user)
    post_list = Post.objects.filter(
        author__in=Subquery(follow_ob.values('author'))
    )
    title = f'Избранные авторы {request.user.username}.'
    main_header = 'Подписки на сайте'
    context = {
        'title': title,
        'main_header': main_header,
        'page_obj': get_paginator(request, post_list),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    title = username
    user_obj = get_object_or_404(User, username=username)
    post_list = user_obj.posts.all()
    post_count = post_list.count()
    following = True
    context = {
        'following': following,
        'author': user_obj,
        'title': title,
        'post_count': post_count,
        'page_obj': get_paginator(request, post_list),
    }

    follow_author = user_obj.following.filter(
        user_id=request.user.id,
        author_id=user_obj.id
    ).exists()
    if request.user.username != user_obj.username and not follow_author:
        Follow.objects.create(user=request.user, author=user_obj).save()
        return render(request, 'posts/profile.html', context)
    return render(request, 'posts/profile.html', context)


@login_required
def profile_unfollow(request, username):
    title = username
    user_obj = get_object_or_404(User, username=username)
    post_list = user_obj.posts.all()
    post_count = post_list.count()
    following = False
    Follow.objects.filter(user=request.user, author=user_obj).delete()
    context = {
        'following': following,
        'author': user_obj,
        'title': title,
        'post_count': post_count,
        'page_obj': get_paginator(request, post_list),
    }
    return render(request, 'posts/profile.html', context)

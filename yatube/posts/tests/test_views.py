import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import User
from ..utils import *

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=image,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user('Sonny')
        cls.group = create_group('group', 'group', 'text')
        cls.post = create_post(
            'text', 'date', cls.user, cls.group, uploaded
        )
        cache.clear()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def url(url, **kwargs) -> str:
        """Возвращает функцию reverse с аргументами"""

        return reverse(url, kwargs=kwargs)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_tamplates(self):
        """View используют нужный шаблон."""

        def url(url, **kwargs) -> str:
            """Возвращает функцию reverse с аргументами"""

            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=self.group.slug),
            url('posts:profile', username=self.post.author),
            url('posts:post_detail', post_id=self.post.id),
            url('posts:post_edit', post_id=self.post.id),
            url('posts:post_create'),
        ]

        templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
        ]

        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'{url} должен использовать шаблон {template}'
                )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ContextViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=image,
            content_type='image/gif'
        )

        cls.guest_client = Client()
        cls.user = User.objects.create_user('Sonny')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = create_group('group', 'group', 'text')

        for x in range(0, 13):
            x += 1
            cls.post = create_post(
                'text', 'date', cls.user, cls.group, uploaded
            )
        cls.comment = create_comment(cls.post, cls.user, 'Comment', 'date')
        cls.followers = create_follow(cls.user, cls.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        cache.clear()

    def test_pages_show_paginator(self):
        """/index/, /group_list/, /profile/<username> содержит паджинатор."""

        templates_context = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                args=[self.post.group.slug]
            ): 'page_obj',
            reverse(
                'posts:profile',
                args=[self.post.author]
            ): 'page_obj',
        }
        for address, context_unit in templates_context.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                cache.clear()
                self.assertEqual(len(
                    response.context[context_unit]), 10,
                    'Постов на странице "1" != 10 , добавьте паджинатор'
                ),
                response = self.client.get(address + '?page=2')
                cache.clear()
                self.assertEqual(
                    len(response.context[context_unit]), 3,
                    'Постов на странице "2" != 3'
                )

                response = self.client.get(address)
                obj_on_page = response.context.get(context_unit).object_list
                cache.clear()
                x = len(obj_on_page)
                for i in range(0, x):
                    i = + 1
                    self.assertIsInstance(
                        obj_on_page[i], Post,
                        'На странице /index/ должны быть объекты типа Post.'
                    )

    def test_post_detail_sorted_by_id(self):
        """На /post_detail/ пост отсортирован по id."""

        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    )
        )
        self.assertEqual(
            response.context.get('post_unit').id,
            self.post.id,
            f'На странице /post_detail/{self.post.id}/ '
            f'post.id != {self.post.id}.'
        )

    def test_posts_on_profile_sorted_by_author(self):
        """Посты на /profile/ отсортированы по автору"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                args=[self.post.author]
            )
        )
        post_in_profile = response.context.get('page_obj').object_list
        for i in post_in_profile:
            self.assertEqual(i.author, self.post.author)

    def test_post_on_group_list_sorted_by_group(self):
        """Посты на /group_list/ отсортированны по группе"""

        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                args=[self.group.slug]
            )
        )
        post_in_group_list = response.context.get('page_obj').object_list
        for i in post_in_group_list:
            self.assertEqual(i.group.slug, self.group.slug)

    def test_pages_contains_images(self):
        """На страницах присутствуют картинки."""

        def url(url, **kwargs) -> str:
            """Возвращает функцию reverse с аргументами"""

            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=self.group.slug),
            url('posts:profile', username=self.post.author),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_with_img = response.context.get('page_obj').object_list
                for i in range(0, len(page_with_img)):
                    self.assertIsNotNone(page_with_img[i].image)

    def test_post_detail_contains_image(self):
        """/post_detail/ содержит картинку."""

        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                args=[self.post.id]
            )
        )
        one_post = response.context['post_unit'].image
        self.assertIsNotNone(one_post)

    def test_authorized_can_comment(self):
        """Авторизированный может комментировать."""

        response = self.authorized_client.get(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        comment_new = response.context.get('comments')
        self.assertIsNotNone(comment_new)

    def test_comments_contains_on_post_detail(self):
        """Комментарий появился на /post_detail/."""

        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        comment = response.context.get('comments')
        self.assertEqual(
            comment[0].text, 'Comment',
            'Комментарий не появился на странице'
        )

    def test_index_page_cache(self):
        """Страница /index/ кешируется"""

        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        create_post('text', 'date', self.user, self.group)
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_authorized_can_sign_on_authors(self):
        """Авторизированный может подписаться."""

        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_subcriptions_contain_on_follow_index(self):
        """Подписки на странице /follow_index/."""

        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        subscription = response.context.get('page_obj').object_list
        self.assertIsNotNone(subscription)

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

User = get_user_model()

from ..models import Post, Group, User

User = get_user_model()


class PostsUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user('auth')
        cls.group = Group.objects.create(
            title='group-title',
            slug='group-slug',
            description='group-text'

        )

        cls.post = Post.objects.create(
            text='post-text',
            pub_date='post-date',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user('HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_url_exists_at_desired_location(self):
        """Доступ к общим страницам."""

        url_names = {
            '': HTTPStatus.OK.value,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
        }

        for url_name, respons_cod in url_names.items():
            with self.subTest(respons_cod=respons_cod):
                response = self.guest_client.get(url_name)
                self.assertEqual(response.status_code, respons_cod)
                response = self.authorized_client.get(url_name)
                self.assertEqual(response.status_code, respons_cod)

    def test_url_exists_at_page_with_authorization(self):
        """Доступ к страницам с авторизацией."""

        url_names = {
            '/': HTTPStatus.OK.value,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
        }
        for url_name, respons_cod in url_names.items():
            with self.subTest(respons_cod=respons_cod):
                response = self.authorized_client.get(url_name)
                self.assertEqual(response.status_code, respons_cod)

    def test_url_for_404(self):
        """Не существующая страница не доступна."""

        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_to_edit_with_author(self):
        """/posts/<post_id/edit/ доступен автору."""

        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_templates_is_valid_addresses(cls):
        """Шаблоны находятся по заданным Url."""

        templates_list = {
            '/': 'posts/index.html',
            f'/group/{cls.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/post_detail.html',
        }

        for address, template in templates_list.items():
            with cls.subTest(address=address):
                response = cls.authorized_client.get(address, follow=True)
                cls.assertTemplateUsed(
                    response, template,
                    f'Статус: {response.status_code} по адресу:'
                    f' "/posts/{cls.post.id}/edit/"'
                )

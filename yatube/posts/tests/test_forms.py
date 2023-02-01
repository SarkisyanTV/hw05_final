from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache

from ..forms import PostForm
from ..models import Post, Group, User

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='no_name')
        cls.group = Group.objects.create(
            title='group-title',
            slug='group-slug',
            description='group-description'
        )
        cls.post = Post.objects.create(
            text='post-text',
            pub_date='post-date',
            author=cls.user,
            group=cls.group
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_label(self):
        '''Тестируем label "text", "group".'''
        text_lable = PostFormTests.form.fields['text'].label
        group_lable = PostFormTests.form.fields['group'].label
        self.assertEqual(text_lable, PostForm.Meta.labels['text'])
        self.assertEqual(group_lable, PostForm.Meta.labels['group'])

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create_post_create_new_post(self):
        """Форма создаёт новый пост"""

        post_count = Post.objects.count()
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
        form_data = {
            'text': 'make in post text',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.post.author})
        )
        self.assertTrue(
            Post.objects.filter(
                text='make in post text',
                group=self.group.id,
                image='posts/image.gif'
            ).exists()
        )

        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_edit_post(self):
        """Форма редактирует пост."""

        post_data = {
            'text': 'Текст для редактирования',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=post_data,
            follow=True
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Страница не доступна автору'
        )
        new_post_data = {
            'text': 'Новый текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=new_post_data,
            follow=True
        )
        # Отредактированный пост содержит новые значения
        self.assertContains(response, 'Новый текст')
        # после редактирования идет редирект на /post_detail/
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )

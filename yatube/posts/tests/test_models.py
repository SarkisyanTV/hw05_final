from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='group-title',
            slug='group-slug',
            description='group-text',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='post-text',
        )

    def test_group_str_give_correct_name(self):
        """В модели группы __str__== group.slug."""
        self.group = PostModelTest.group
        verbose_name = self.group.title
        self.assertEqual(
            verbose_name,
            str(self.group),
            f'group __str__ должен быть "{self.group.title}"!'
        )

    def test_post_str_give_correct_name(self):
        """В модели поста __str__ == post.text[:15]."""
        self.long_post = Post.objects.create(
            author=self.user,
            text='Пост из пятнадцати символов'
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Пост'
        )
        self.assertEqual(str(self.long_post), 'Пост из пятнадц')
        self.assertEqual(str(self.post), 'Пост')

from django import forms
from django.forms import ModelForm
from posts.models import Post, Comment


class PostForm(ModelForm):
    class Meta(ModelForm):
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка',
        }


class CommentForm(ModelForm):
    class Meta(ModelForm):
        model = Comment
        fields = ('text',)
        help_text = {
            'text': 'Ваш комментарий',
        }
        placeholders = {
            'text': 'Текст комментария',
        }


from django.contrib.auth import get_user_model
from django import forms

from .models import Post, Group, Comment


User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta():
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Название группы',
            'image': 'Картинка поста',
        }
        help_texts = {
            'text': 'Напишите пост здесь',
            'group': 'Выберите свою группу',
        }
    text = forms.CharField(widget=forms.Textarea)
    group = forms.ModelChoiceField(Group.objects.all(), required=False)


class CommentForm(forms.ModelForm):
    class Meta():
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст комментария',
        }

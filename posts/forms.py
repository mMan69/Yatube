from django.forms import ModelForm
from posts.models import Post, Comment


class PostForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = '- Группа -'
        self.fields['text'].widget.attrs.update({'placeholder': 'Введите текст'})

    class Meta:
        model = Post
        fields = ['group', 'text', 'image']


class CommentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update({'placeholder': 'Введите текст'})

    class Meta:
        model = Comment
        fields = ['text']
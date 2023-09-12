from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(max_length=300)

    def __str__(self):
        return f"{self.title}"


class Post(models.Model):
    class Meta:
        ordering = ["-pub_date"]

    text = models.TextField(verbose_name="Введите текст")
    pub_date = models.DateTimeField("дата публикации", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL,
                              related_name="posts", verbose_name="Выберите группу для поста(необязательно)")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return f"{self.text}"


class Comment(models.Model):
    post = models.ForeignKey(Post,on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField(verbose_name="Введите текст")
    created = models.DateTimeField("дата публикации", auto_now_add=True)

    def __str__(self):
        return f"{self.text}"


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")

    def __str__(self):
        return f'{self.user}, {self.author}'


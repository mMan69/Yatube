import os
from urllib.parse import urljoin
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import User, Post, Group, Follow, Comment


class TestProfilePage(TestCase):
    def setUp(self):
        # Создаем клиент
        self.client = Client()
        # Регистрируем тестового пользователя
        self.user = User.objects.create_user(
            username="testname",
            email="test@mail.ru",
            password="12345"
        )
        self.user_2 = User.objects.create_user(
            username="testname_2",
            email="test_2@mail.ru",
            password="12345"
        )

        # Создаем тестовый пост
        self.post = Post.objects.create(
            text="Тестовый пост",
            author=self.user
        )
        self.group = Group.objects.create(
            title='test group',
            slug='test_group',
            description='Тестовое описание 2',
        )

        self.url = [
            reverse("index"),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse("post", kwargs={"username": self.user.username, "post_id": self.post.id})
        ]

        cache.clear()

    def tearDown(self):
        # Удаляем пользователя(так же удаляться все посты, потому что в модели прописано on_delete=models.CASCADE)
        User.objects.filter(username="testname").delete()
        User.objects.filter(username="testname_2").delete()
        Group.objects.filter(title='test group').delete()

    def test_profile_page(self):
        # После регистрации пользователя создается его персональная страница (profile)
        # Заходим на страницу пользователя после его создания
        response = self.client.get(reverse("profile", kwargs={"username": "testname"}))
        # Проверяем что такая страница существует и она доступна
        self.assertEqual(response.status_code, 200)
        # проверяем, что при отрисовке страницы был получен список из 1 записи(поста)
        self.assertEqual(len(response.context["paginator"].object_list), 1)
        # проверяем, что объект пользователя, переданный в шаблон, соответствует пользователю, которого мы создали
        self.assertIsInstance(response.context["users"], User)
        self.assertEqual(response.context["users"].username, self.user.username)

    def test_auth_user_new_post(self):
        # Авторизованный пользователь может опубликовать пост (new)
        # Логинимся на сайт
        self.client.login(username="testname", password="12345")
        # Делаем пост запрос на создание поста
        response = self.client.post(reverse("new_post"), {"text": "туда сюда обратно"})
        # Проверяем была ли переадресация
        self.assertRedirects(response, reverse("index"), status_code=302, target_status_code=200)
        # Проверяем что такой пост появился в базе
        post = Post.objects.filter(author=self.user, text="туда сюда обратно").exists()
        self.assertTrue(post)
        # Создаем переменные для проверки поста на страницах index, profile и post
        post_2 = Post.objects.get(author=self.user, text="туда сюда обратно")
        urls = [
            reverse("index"),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse("post", kwargs={"username": self.user.username, "post_id": post_2.id})
        ]
        # Проверяем что этот пост появился на страницах index, profile и post
        for url in urls:
            response_2 = self.client.get(url)
            self.assertContains(response_2, post_2)

    def test_noauth_user_new_post(self):
        # Неавторизованный посетитель не может опубликовать пост (его редиректит на страницу входа)
        # Делаем пост запрос на создание поста
        response = self.client.post(reverse("new_post"), {"text": "туда сюда обратно и снова туда"})
        # переменная ссылки редиректа
        url = urljoin(reverse("login"), "?next=/new")
        # Проверяем была ли переадресация
        self.assertRedirects(response, url, status_code=302, target_status_code=200)
        # Проверим что пост в базе НЕ появился
        self.assertFalse(Post.objects.filter(author=self.user, text="туда сюда обратно и снова туда").exists())

    def test_auth_user_edit_post(self):
        # Проверяем что авторизованный пользователь может изменить пост и он измениться на всех страницах self.url
        self.client.login(username="testname", password="12345")
        response = self.client.post(
            reverse("post_edit", kwargs={"username": self.user.username,"post_id": self.post.id}),
            {"text": "Измененный текст"})

        url_redirect = reverse("post", kwargs={"username": self.user.username,"post_id": self.post.id})
        self.assertRedirects(response, url_redirect, status_code=302, target_status_code=200)
        post = Post.objects.get(author=self.user, text="Измененный текст")
        for url in self.url:
            response_2 = self.client.get(url)
            self.assertContains(response_2, post)

    def test_404_page(self):
        # Проверяем возвращает ли сервер код 404, если страница не найдена.
        response = self.client.get(reverse("post", kwargs={"username": self.user.username,"post_id": 404}))
        self.assertEqual(response.status_code, 404)

    def test_img_post_page(self):
        # Проверяем что пользователь может добавить пост с картинкой
        # и он будет отображаться на всех страницах списка url
        # Логинимся
        self.client.login(username="testname", password="12345")
        # Создаем пост с картинкой
        with open('posts/test.jpg', 'rb') as img:
            self.client.post(reverse('new_post'), {'group': self.group.id,'text': 'post with image', 'image': img})
        # проверяем что пост добавился в базу
        self.assertEqual(Post.objects.filter(author=self.user).count(), 2)
        post = Post.objects.get(text='post with image')
        self.assertTrue(post)
        # Проверяем пост на всех страницах URL
        url = [
            reverse("index"),
            reverse("post", kwargs={"username": self.user.username, "post_id": post.id}),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse("group", kwargs={"slug": self.group.slug})
        ]

        for u in url:
            response = self.client.get(u)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<img')
            self.assertContains(response, post)

    def test_no_img_post_page(self):
        # Проверяем, что срабатывает защита от загрузки файлов не-графических форматов
        # Логинимся
        self.client.login(username="testname", password="12345")
        # создаем пост с не графическим файлом
        with open('posts/test_no_img.docx', 'rb') as img:
            self.client.post(reverse('new_post'), {'group': self.group.id, 'text': 'post with image', 'image': img})
        # проверяем что в базе только 1 пост, созданный перед тестом
        post = Post.objects.filter(author=self.user).count()
        self.assertEqual(post, 1)

    def test_cache_index_page(self):
        # Проверяем что страница сохраняется в КЭШ
        # Логинимся и создаем пост
        self.client.login(username="testname", password="12345")
        self.client.post(reverse('new_post'), {'text': 'post with cache'})

        post = Post.objects.get(text='post with cache')
        # Проверяем что пост есть в базе
        self.assertTrue(post)
        response = self.client.get(reverse('index'))
        # Проверяем что пост появляется на странице
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, post)
        # Создаем новый пост
        self.client.post(reverse('new_post'), {'text': 'post with cache_2'})

        post_2 = Post.objects.get(text='post with cache_2')
        # Проверяем что пост есть в базе
        self.assertTrue(post_2)
        response_2 = self.client.get(reverse('index'))
        # Проверяем что страница сохранилась в КЕШ и новый пост не появился на странице
        self.assertEqual(response_2.status_code, 200)
        self.assertNotContains(response_2, post_2)

    def test_follow_and_unfollow_page(self):
        # Проверяем что Авторизованный пользователь может подписываться
        # на других пользователей и удалять их из подписок.
        self.client.login(username="testname", password="12345")

        url_redirect = reverse("profile", kwargs={"username": self.user_2.username})
        response = self.client.get(reverse('profile_follow', kwargs={"username": self.user_2.username}))
        self.assertRedirects(response, url_redirect, status_code=302, target_status_code=200)

        author = User.objects.get(username=self.user_2.username)
        user = User.objects.get(username=self.user.username)
        self.assertTrue(Follow.objects.filter(author=author, user=user).exists())

        response_2 = self.client.get(reverse('profile_unfollow', kwargs={"username": self.user_2.username}))
        self.assertRedirects(response_2, url_redirect, status_code=302, target_status_code=200)

        self.assertFalse(Follow.objects.filter(author=author, user=user).exists())


    def test_follow_index_page(self):
        # Проверяем что новая запись пользователя появляется в ленте тех,
        # кто на него подписан и не появляется в ленте тех, кто не подписан на него.
        self.client.login(username="testname_2", password="12345")
        self.client.post(reverse('new_post'), {'text': 'post for follower'})
        post = Post.objects.get(text='post for follower')
        self.assertTrue(post)
        self.client.logout()

        self.client.login(username="testname", password="12345")
        self.client.get(reverse('profile_follow', kwargs={"username": self.user_2.username}))
        response = self.client.get(reverse('follow_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, post)

        self.client.get(reverse('profile_unfollow', kwargs={"username": self.user_2.username}))
        response_2 = self.client.get(reverse('follow_index'))
        self.assertEqual(response_2.status_code, 200)
        self.assertNotContains(response_2, post)

    def test_noauth_comment_page(self):
        # Проверяем что Только авторизированный пользователь может комментировать посты.
        self.client.post(reverse('add_comment', kwargs={"username": self.user.username, "post_id": self.post.id}),
                        {'text': 'comment'})
        self.assertFalse(Comment.objects.filter(text='comment', post=self.post.id).exists())

        self.client.login(username="testname_2", password="12345")
        self.client.post(reverse('add_comment', kwargs={"username": self.user.username, "post_id": self.post.id}),
                        {'text': 'comment_2'})
        self.assertTrue(Comment.objects.filter(text='comment_2', post=self.post.id).exists())

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Bashka')
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTest.user)

    def test_urls_uses_correct_template(self):
        """URL -адрес использует соствествующий шаблон"""
        post_author = self.user.username
        post_id = self.post.pk
        post_group = self.group.slug
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{post_group}/': 'posts/group_list.html',
            f'/profile/{post_author}/': 'posts/profile.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def group_test(self):
        """Страница Group доступна любому пользователю"""
        post_group = self.group.slug
        response = self.guest_client.get(f'/group/{post_group}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def profile_test(self):
        """Страница profile доступна любому пользователю"""
        post_author = self.user.username
        response = self.guest_client.get(f'/profile/{post_author}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def post_detail_self(self):
        """Страница post_detail доступна любому пользователю"""
        post_id = self.post.pk
        response = self.guest_client.get(f'/posts/{post_id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def create_test(self):
        """Create  доступна авторизованному пользователю"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_for_author(self):
        post_id = self.post.pk
        response = self.authorized_client.get(
            f'/posts/{post_id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_error_page(self):
        response = self.guest_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)

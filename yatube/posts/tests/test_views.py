from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создает объект тестируемого класса."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='тестовое описание',
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text='Тестовый текст поста',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        """Creates a user"""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        urls_names = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        }
        for test_url in urls_names:
            response = self.authorized_client.get(test_url)
            self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_second_page_contains_ten_records(self):
        urls_names = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        }
        for test_url in urls_names:
            response = self.authorized_client.get(test_url + '?page=2')
            self.assertEqual(len(response.context.get('page_obj')), 3)

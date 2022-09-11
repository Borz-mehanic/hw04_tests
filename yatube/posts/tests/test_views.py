from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, Group

User = get_user_model()
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст',
            pub_date='29.08.2022',)
        GROUP_SLUG = cls.group.slug
        USER_NAME = cls.user.username
        POST_ID = cls.post.id
        cls.GROUP_URL = reverse(
            'posts:group_list', kwargs={'slug': GROUP_SLUG}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': USER_NAME}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': POST_ID}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': POST_ID}
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соотвествующий шаблон"""
        templates_pages_name = {
            INDEX_URL: 'posts/index.html',
            self.GROUP_URL: 'posts/group_list.html',
            self.PROFILE_URL: 'posts/profile.html',
            CREATE_URL: 'posts/create_post.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        def test_index_page_show_correct_context(self):
            """Шаблон index сформирован с правильным контекстом"""
            response = self.authorized_client.get(INDEX_URL)
            form_fields = {
                'text': forms.fields.TextField,
                'pub_date': forms.fields.DateTimeField,
                'author': forms.fields.ForeignKey,
                'group': forms.fields.ForeignKey,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

        def test_group_list_show_coerrect_context(self):
            """Шаблон group_list сформирован с правильным контекстом"""
            response = self.authorized_client.get(reverse('posts:group_list'))
            group_list_object = response.context['page_obj'][0]
            task_text_0 = group_list_object.text
            task_slug_0 = group_list_object.slug
            self.assertEqual(task_text_0, 'Тестовый текст')
            self.assertEqual(task_slug_0, 'test-slug')

        def test_profile_show_correct_context(self):
            """Шаблон profile сформирован с правильным контекстом."""
            post_author = self.post.author
            response = self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': f'{post_author}'})
            )
            context_profile_author = response.context.get('page_obj')[0].author
            context_profile_text = response.context.get('page_obj')[0].text
            expected_author = self.post.author
            expected_text = self.post.text
            self.assertEqual(context_profile_author, expected_author)
            self.assertEqual(context_profile_text, expected_text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
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

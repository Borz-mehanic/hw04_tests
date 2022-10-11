import shutil
import tempfile

from django import forms
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, User
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

NEW_POST = reverse('posts:post_create')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TasCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Test',
            slug='Tests',
            description='Testss'
        )
        cls.group2 = Group.objects.create(
            title='Test2',
            slug='Tests2',
            description='Testss2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test text',
            group=cls.group
        )
        cls.form = PostForm()

        cls.POST_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id])
        cls.PROFILE_URL = reverse(
            'posts:profile',
            args=[cls.user.username]
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма создает пост в БД"""
        posts = Post.objects.all()
        posts.delete()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        data = {
            'group': self.group.pk,
            'text': self.post.text,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            NEW_POST,
            data=data,
            follow=True
        )
        post = response.context['page_obj'][0]
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(post.text, data['text'])
        self.assertEqual(data['group'], post.group.id)
        self.assertEqual(post.author, self.user)
        self.assertRedirects(response, self.PROFILE_URL)
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text='test text',
                group=self.group.pk,
                image='posts/small.gif',
            ).exists()
        )

    def test_new_post_show_correct_context(self):
        """URL-адрес использует соотвествующий шаблон"""
        urls = [
            NEW_POST,
            self.POST_EDIT_URL
        ]
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.Field
                       }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_edit_post(self):
        """Валидная форма редактирует Пост в БД."""
        form_data = {
            'text': 'text_test357',
            'group': f'{self.post.group.id}',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, (self.POST_DETAIL_URL))
        # Проверяем, что пост отредактирован
        self.assertTrue(
            Post.objects.filter(
                text='text_test357',
                group=self.group.id
            ).exists()
        )

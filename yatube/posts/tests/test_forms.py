import shutil
import tempfile

from django import forms
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

NEW_POST = reverse('posts:create')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTests(TestCase):

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
        cls.POST_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id])
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[cls.post.id])
        cls.PROFILE_URL = reverse(
            'posts:profile',
            args=[cls.user.username]
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        posts = Post.objects.all()
        posts.delete()
        data = {
            'text': 'Текст формы',
            'group': self.group.id,
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

    def test_new_post_show_correct_context(self):
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
        form_data = {
            'text': 'hi!',
            'group': self.group2.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data, follow=True
        )
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(post.author, self.post.author)
        self.assertRedirects(response, self.POST_URL)

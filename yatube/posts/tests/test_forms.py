import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostCreateFormTest(TestCase):
    """Класс тестирования постов."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='smeo')
        cls.group = Group.objects.create(title='test_group',
                                         slug='test_slug',
                                         description='test_descripton')
        cls.post = Post.objects.create(author=cls.user,
                                       group=cls.group,
                                       text='Text_3'
                                       )
        cls.post_edit = Post.objects.create(author=cls.user,
                                            group=cls.group,
                                            text='Edit Text',
                                            )
        cls.form = PostForm()

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(
            TEMP_MEDIA_ROOT,
            ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_create_form_post(self):
        """Проверка создания нового поста с добавлением img."""
        post_count = Post.objects.count()
        form = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text='Текст',
                image='posts/small.gif',
                group=self.group.pk,
            ).exists()
        )
        print(Post.objects.filter(
            text='Текст', group=self.group.pk
        ).first().image)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username}))

        last_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(last_post.text, form['text'])
        self.assertEqual(last_post.group.pk, form['group'])
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.image.name, 'posts/small.gif')

    def test_eddit_post_success(self):
        """Проверка редактирования поста."""
        post_count = Post.objects.count()
        form = {
            'text': self.post_edit.text,
            'group': self.post_edit.group.pk,
        }
        response = self.authorized_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}), data=form)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.post.refresh_from_db()
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        last_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(last_post.text, form['text'])
        self.assertEqual(last_post.group.pk, form['group'])
        self.assertEqual(last_post.author, self.user)

    def test_form_create_post_unauthorized_user(self):
        """
        Проверяем, что неавторизованный пользователь не может
        отправить запрос на создание поста
        """
        post_count = Post.objects.count()
        form = {
            'text': 'Text_3',
            'group': self.group.id,
        }
        response = self.guest_client.post(reverse('posts:post_create'),
                                          data=form,
                                          follow=True)
        self.assertRedirects(response,
                             reverse('users:login') + '?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)

    def test_add_comment(self):
        """Авторизованный пользователь может комментировать посты."""
        com_count = Comment.objects.count()
        print(com_count)
        form = {
            'post': self.post_edit,
            'author': self.post_edit.author,
            'text': self.post_edit.text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        comment = Comment.objects.first()
        print(comment)
        self.assertEqual(Comment.objects.count(), com_count + 1)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.text, form['text'])
        self.assertEqual(comment.author, self.post.author)

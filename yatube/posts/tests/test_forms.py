import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных для проверки сушествующего slug
        cls.user = User.objects.create_user(username='bashka')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый текст',
            group=cls.group,
        )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='тестовый текст другого поста',
            group=cls.group
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form_data = {
            'text': self.post_2.text,
            'group': self.group.id
        }

    def form_field(self, last_post):
        # Проверка полей формы
        last_post = Post.objects.order_by("id").last()
        form_list = {
            'text': last_post.text,
            'group': last_post.group.id,
        }
        self.assertEqual(form_list['text'], last_post.text)
        self.assertEqual(form_list['group'], last_post.group.id)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        response_auth = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        # Проверка переадресации после создания поста
        self.assertRedirects(
            response_auth,
            reverse('posts:profile', kwargs={
                    'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным слагом
        self.assertTrue(
            Post.objects.filter(
                author=self.post.author,
                text=self.post.text,
                group=self.post.group
            ).exists()
        )
        self.form_field(response_auth)

    def test_blank_image(self):
        """Если пользователь загрузит не картинку, возвращаем ошибку"""
        blank_gif = ('')

        empty_image = SimpleUploadedFile(
            name='blank_gif.gif',
            content=blank_gif,
            content_type='image/gif')
        form_data = {
            'text': self.post_2.text,
            'group': self.group.id,
            'image': empty_image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertFormError(
            response,
            'form',
            'image',
            'Отправленный файл пуст.')

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        response_auth = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}),
            data=self.form_data,
            follow=True
        )
        # Проверка переадресации после создания поста
        self.assertRedirects(
            response_auth,
            reverse('posts:post_detail', kwargs={
                    'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверка полей формы
        for value, expected in self.form_data.items():
            with self.subTest(value=value):
                response_auth = self.authorized_client.get(value)
                self.assertEqual(self.form_data[value], expected)
        self.form_field(response_auth)

    def test_title_help_text(self):
        """Проверяем help_text"""
        title_help_text = PostCreateFormTests.form.fields['text'].help_text
        title_help_group = PostCreateFormTests.form.fields['group'].help_text
        self.assertEqual(title_help_text, 'Тут должен быть текст поста')
        self.assertEqual(title_help_group, 'Укажите группу')

    def test_image_coun_post(self):
        """Проверяем, что при отправке поста с картинкой через форму PostForm
           создаётся запись в базе данных. """
        posts_count_before = Post.objects.count()
        self.post_image = Post.objects.create(
            author=self.user,
            text='тестовый текст другого поста',
            group=self.group,
            image=self.uploaded)
        posts_count_after = Post.objects.count()
        self.assertEqual(posts_count_before + 1, posts_count_after)
        Post.objects.get(id=self.post_image.id).delete()
        self.form_field(self.post_image)

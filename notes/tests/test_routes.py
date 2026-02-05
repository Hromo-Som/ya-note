from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты доступности страниц."""

    @classmethod
    def setUpTestData(cls):
        """Подготовка данных, используемых в тестах."""
        cls.author = User.objects.create(username='Лев Толстой')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_user = User.objects.create(username='Пользователь простой')
        cls.another_user_client = Client()
        cls.another_user_client.force_login(cls.another_user)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='test',
            author=cls.author,
        )

    def test_pages_availability(self):
        """Тест доступности общедоступных страниц."""
        urls = (
            ('notes:home'),
            ('users:login'),
            ('users:signup'),
            ('users:logout'),
        )

        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                if name == 'users:logout':
                    response = self.client.post(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                else:
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """Тест доступности страниц для авторизованных пользователей."""
        urls = (
            ('notes:list'),
            ('notes:add'),
            ('notes:success'),
        )

        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.another_user_client.get(url)
                assert response.status_code == HTTPStatus.OK

    def test_pages_availability_for_different_users(self):
        """Тест доступности страниц конкретных заметок."""
        urls = (
            ('notes:detail'),
            ('notes:edit'),
            ('notes:delete'),
        )
        client_status = (
            (self.author_client, HTTPStatus.OK),
            (self.another_user_client, HTTPStatus.NOT_FOUND),
        )

        for name in urls:
            for client, expected_status in client_status:
                with self.subTest(name=name, client=client):
                    url = reverse(name, args=(self.note.slug,))
                    response = client.get(url)
                    assert response.status_code == expected_status

    def test_redirect_for_anonymous_client(self):
        """
        Тест проверки перенаправления на страницу авторизации
        для анонимного пользователя.
        """
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )

        login_url = reverse('users:login')
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

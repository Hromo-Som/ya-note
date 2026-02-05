from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestNotesListPage(TestCase):
    """Тесты проверки содержимого страниц с заметками."""

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

    def test_notes_list_for_different_users(self):
        """Тест проверки отображения заметок пользователям."""
        client_has_note = (
            (self.author_client, True),
            (self.another_user_client, False),
        )

        for client, has_note in client_has_note:
            with self.subTest(client=client):
                url = reverse('notes:list')
                response = client.get(url)
                object_list = response.context['object_list']
                assert (self.note in object_list) is has_note

    def test_pages_contains_form(self):
        """Тест проверки наличия формы для заметок."""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )

        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                assert 'form' in response.context
                assert isinstance(response.context['form'], NoteForm)

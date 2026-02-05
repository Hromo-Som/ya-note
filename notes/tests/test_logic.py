from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    """Тесты создания заметок."""

    FORM_DATA = {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug'
    }

    @classmethod
    def setUpTestData(cls):
        """Подготовка данных, используемых в тестах."""
        cls.url = reverse('notes:add')
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

    def test_anonymous_user_cant_create_note(self):
        """
        Тест отсутствия возможности создания
        заметки анонимным пользователем.
        """
        response = self.client.post(self.url, data=self.FORM_DATA)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.url}'
        self.assertRedirects(response, expected_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_user_can_create_note(self):
        """Тест возможности создания заметки авторизованным пользователем."""
        response = self.author_client.post(self.url, data=self.FORM_DATA)
        self.assertRedirects(response, '/done/')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        note = Note.objects.get(title=self.FORM_DATA['title'])
        self.assertEqual(note.title, self.FORM_DATA['title'])
        self.assertEqual(note.text, self.FORM_DATA['text'])
        self.assertEqual(note.author, self.author)

    def test_not_unique_slug(self):
        """Тест уникальности slug."""
        form_data = self.FORM_DATA.copy()
        form_data['slug'] = self.note.slug
        response = self.author_client.post(self.url, data=form_data)
        form = response.context['form']
        self.assertFormError(
            form=form,
            field='slug',
            errors=self.note.slug + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_empty_slug(self):
        """
        Тест автоматического создания slug,
        если соответствующее поле в форме не заполнено.
        """
        form_data = self.FORM_DATA.copy()
        form_data.pop('slug')
        response = self.author_client.post(self.url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        assert Note.objects.count() == 2
        new_note = Note.objects.get(title=form_data['title'])
        expected_slug = slugify(form_data['title'])
        assert new_note.slug == expected_slug


class TestNoteEditDelete(TestCase):
    """Тесты редактирования и удаления заметок."""

    NOTE_DATA = {
        'title': 'Заголовок заметки',
        'text': 'Текст заметки',
        'slug': 'note-slug',
    }

    FORM_DATA = {
        'title': 'Обновлённый заголовок',
        'text': 'Обновлённый текст',
        'slug': 'new-note-slug',
    }

    @classmethod
    def setUpTestData(cls):
        """Подготовка данных, используемых в тестах."""
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another = User.objects.create(username='Другой пользователь')
        cls.another_client = Client()
        cls.another_client.force_login(cls.another)
        cls.note = Note.objects.create(
            title=cls.NOTE_DATA['title'],
            text=cls.NOTE_DATA['text'],
            slug=cls.NOTE_DATA['slug'],
            author=cls.author,
        )
        cls.url_to_done = reverse('notes:success')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_author_can_delete_note(self):
        """Тест возможности удаления заметки автором."""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_to_done)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_other_cant_delete_note(self):
        """Тест отсутствия возможности удаления заметки не автором."""
        response = self.another_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Тест возможности редактирования заметки автором."""
        response = self.author_client.post(self.edit_url, data=self.FORM_DATA)
        self.assertRedirects(response, self.url_to_done)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.FORM_DATA['title'])
        self.assertEqual(self.note.text, self.FORM_DATA['text'])
        self.assertEqual(self.note.slug, self.FORM_DATA['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        """Тест отсутствия возможности редактирования заметки не автором."""
        response = self.another_client.post(self.edit_url, data=self.FORM_DATA)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NOTE_DATA['title'])
        self.assertEqual(self.note.text, self.NOTE_DATA['text'])
        self.assertEqual(self.note.slug, self.NOTE_DATA['slug'])

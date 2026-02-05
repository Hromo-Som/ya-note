import pytest

from django.test.client import Client

from notes.models import Note


@pytest.fixture
def author(django_user_model):
    """Создание модели пользователя 'Автор'."""
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    """Создание модели пользователя 'Не автор'."""
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author):
    """Авторизация 'Автора' в клиенте."""
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    """Авторизация 'Не автора' в клиенте."""
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def note(author):
    """Создание объекта заметки."""
    note = Note.objects.create(
        title='Заголовок',
        text='Текст заметки',
        slug='note-slug',
        author=author,
    )
    return note


@pytest.fixture
def slug_for_args(note):
    """Получение slug конкретной заметки."""
    return (note.slug,)


@pytest.fixture
def form_data():
    """Возвращает данные для создания объекта заметки."""
    return {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug'
    }

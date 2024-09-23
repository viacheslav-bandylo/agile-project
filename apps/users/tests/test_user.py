from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User
from apps.projects.models import Project
from apps.users.serializers.user_serializers import UserListSerializer, RegisterUserSerializer
from unittest.mock import patch
from apps.users.choices.positions import Positions  # Предполагаем, что Positions находится в apps.users.enums


class UserAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Используем допустимые значения для поля position
        self.position1 = Positions.PROGRAMMER.value
        self.position2 = Positions.DESIGNER.value

        # Создаем пользователей с допустимыми значениями для поля position
        self.user1 = User.objects.create_user(
            username='user1',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            password='pass1234',
            position=self.position1,
            phone='123456789'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            password='pass1234',
            position=self.position2,
            phone='987654321'
        )

        # Создаем проект и связываем с user1
        self.project = Project.objects.create(name='Project1')
        self.project.users.add(self.user1)

    def get_api_url(self, endpoint):
        return f'/api/v1/users/{endpoint}'

    # Проверка получения списка всех пользователей
    def test_get_all_users(self):
        url = self.get_api_url('')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # Проверка получения списка пользователей по имени проекта
    def test_get_users_by_project_name(self):
        url = self.get_api_url('')
        response = self.client.get(url, {'project_name': 'Project1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], 'John')

    # Проверка получения пустого списка пользователей
    def test_get_empty_user_list(self):
        with patch('apps.users.views.user_views.UserListGenericView.get_queryset') as mocked_get_queryset:
            mocked_get_queryset.return_value = User.objects.none()
            url = self.get_api_url('')
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertEqual(response.data, [])

    # Проверка работы сериализатора на правильное отображение данных списка пользователей
    def test_user_list_serializer(self):
        users = User.objects.all()
        serializer = UserListSerializer(users, many=True)
        expected_data = [
            {
                'first_name': self.user1.first_name,
                'last_name': self.user1.last_name,
                'position': self.user1.position,
                'email': self.user1.email,
                'phone': self.user1.phone,
                'last_login': self.user1.last_login,
            },
            {
                'first_name': self.user2.first_name,
                'last_name': self.user2.last_name,
                'position': self.user2.position,
                'email': self.user2.email,
                'phone': self.user2.phone,
                'last_login': self.user2.last_login,
            },
        ]
        self.assertEqual(serializer.data, expected_data)

    # Проверка создания нового пользователя с корректными данными
    def test_create_user_with_valid_data(self):
        url = self.get_api_url('register/')
        data = {
            'username': 'user3',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice@example.com',
            'position': Positions.QA.value,  # Используем допустимое значение
            'password': 'StrongPassword1!',
            're_password': 'StrongPassword1!',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='user3').exists())

    # Проверка создания нового пользователя с некорректными данными
    def test_create_user_with_invalid_data(self):
        url = self.get_api_url('register/')
        data = {
            'username': 'user4',
            'first_name': 'Bob',
            'last_name': 'Williams',
            'email': 'bob@example.com',
            'position': Positions.CEO.value,  # Используем допустимое значение
            'password': 'Password1!',
            're_password': 'Password2!',  # Пароли не совпадают
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='user4').exists())
        self.assertIn("Passwords don't match", str(response.data))

    # Проверка создания нового пользователя с пропуском обязательных данных
    def test_create_user_with_missing_required_data(self):
        url = self.get_api_url('register/')
        data = {
            'username': 'user5',
            # 'first_name' отсутствует
            'last_name': 'Brown',
            'email': 'user5@example.com',
            'position': Positions.DESIGNER.value,  # Используем допустимое значение
            'password': 'Password1!',
            're_password': 'Password1!',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='user5').exists())
        self.assertIn('first_name', response.data)

    # Проверка работы сериализатора для создания нового пользователя с корректными данными
    def test_register_user_serializer_with_valid_data(self):
        data = {
            'username': 'user6',
            'first_name': 'Diana',
            'last_name': 'Prince',
            'email': 'diana@example.com',
            'position': Positions.CEO.value,  # Используем допустимое значение
            'password': 'WonderWoman1!',
            're_password': 'WonderWoman1!',
        }
        serializer = RegisterUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'user6')
        self.assertTrue(user.check_password('WonderWoman1!'))

    # Проверка работы сериализатора для создания нового пользователя с некорректными данными
    def test_register_user_serializer_with_invalid_data(self):
        data = {
            'username': 'user7',
            'first_name': 'Clark',
            'last_name': 'Kent',
            'email': 'clark@example.com',
            'position': Positions.CTO.value,  # Используем допустимое значение
            'password': 'Superman1!',
            're_password': 'Superman2!',  # Пароли не совпадают
        }
        serializer = RegisterUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

from unittest.mock import Mock
import base64
import os


def generate_id():
    return base64.urlsafe_b64encode(os.urandom(6)).decode('utf-8')


# Создаем mock-объект с side_effect
def custom_side_effect():
    return "mocked_id_with_side_effect"


mock_generate_id = Mock(side_effect=custom_side_effect)

print(generate_id())
print(mock_generate_id())

mock_generate_id = Mock(side_effect=[1, 2, 'hello', 3])
print(mock_generate_id())
print(mock_generate_id())
print(mock_generate_id())
print(mock_generate_id())

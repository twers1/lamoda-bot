import requests

from src.config import email, password

# URL для аутентификации и получения токена
auth_url = 'https://backend.gm.lamoda.ru/api/v1/login'

# URL для запроса календаря
calendar_url = 'https://backend.gm.lamoda.ru/api/v1/calendar'

# Учетные данные пользователя
credentials = {
    'username': "sales@mamour-enfants.com",
    'password': password
}


# Функция для получения токена аутентификации
def get_auth_token():
    """Функция для аутентификации и получения токена."""
    # Создаем сессию
    session = requests.Session()

    # Отправляем POST-запрос для аутентификации и получения токена
    response = session.post(auth_url, json=credentials)
    response.raise_for_status()  # Проверяем успешность запроса

    # Получаем сессионную куку PHPSESSID из сессии
    php_session_cookie = session.cookies.get('PHPSESSID')

    # Получаем токен из JSON-ответа
    token = response.json()['data']['token']

    # Возвращаем токен и сессионную куку PHPSESSID как строки
    return token, php_session_cookie


# Функция для запроса календаря с использованием токена аутентификации и сессионной куки PHPSESSID
def get_calendar(headers):
    """Функция для выполнения запроса к API календаря с использованием токена аутентификации и сессионной куки."""
    params = {
        'month': '2023-12',
        'partnerId': '4823',
        'directionId': '1'
    }
    response = requests.get(calendar_url, headers=headers, params=params)
    return response  # Return the response object itself

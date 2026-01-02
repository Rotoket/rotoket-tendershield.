import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
  return TestClient(app)


def test_login_success(client: TestClient):
  """Успешный вход с корректными учётными данными."""
  resp = client.post(
    "/api/auth/login",
    json={"email": "rotoket@mail.ru", "password": "Rotoket10-34"},
  )
  assert resp.status_code == 200
  data = resp.json()
  assert "access_token" in data
  assert data.get("token_type") == "bearer"


@pytest.mark.parametrize(
  "email,password",
  [
    ("rotoket@mail.ru", "WrongPassword123"),  # неверный пароль
    ("unknown@example.com", "AnyPassword1"),  # неизвестный пользователь
  ],
)
def test_login_failed_wrong_credentials(client: TestClient, email: str, password: str):
  """Неверный пароль или логин должны возвращать 401 без падения сервера."""
  resp = client.post("/api/auth/login", json={"email": email, "password": password})
  assert resp.status_code == 401
  data = resp.json()
  # Структура ответа может меняться, главное — корректный статус и отсутствие трассировки
  assert isinstance(data, dict)


def test_me_requires_auth(client: TestClient):
  """Эндпоинт текущего пользователя должен требовать токен."""
  resp = client.get("/api/auth/me")
  assert resp.status_code in (401, 403)




































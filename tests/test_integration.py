"""
Integration tests for Module 13: JWT Auth + User & Calculation Routes.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _register(client, username="testuser", email=None, password="pass1234"):
    if email is None:
        email = f"{username}@example.com"
    res = client.post("/users/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    assert res.status_code == 201, res.text
    return res.json()["user"]["id"]


def _login(client, email, password):
    return client.post("/users/login", json={"email": email, "password": password})


def _add_calc(client, user_id, a=10, b=5, op="Add"):
    res = client.post("/calculations/", json={"a": a, "b": b, "type": op, "user_id": user_id})
    assert res.status_code == 201, res.text
    return res.json()


# ── User Registration Tests ───────────────────────────────────────────────────

def test_register_success(client):
    res = client.post("/users/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["username"] == "alice"
    assert data["user"]["email"] == "alice@example.com"
    assert "id" in data["user"]
    assert "created_at" in data["user"]
    assert "token" in data
    assert len(data["token"]) > 0
    assert data["message"] == "Registration successful"


def test_register_returns_jwt(client):
    res = client.post("/users/register", json={
        "email": "jwttest@example.com",
        "password": "securepass",
    })
    assert res.status_code == 201
    data = res.json()
    assert "token" in data
    parts = data["token"].split(".")
    assert len(parts) == 3


def test_register_omits_password_hash(client):
    res = client.post("/users/register", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "supersecret",
    })
    user_data = res.json()["user"]
    assert "password" not in user_data
    assert "password_hash" not in user_data


def test_register_without_username_uses_email_prefix(client):
    res = client.post("/users/register", json={
        "email": "noname@example.com",
        "password": "pass1234",
    })
    assert res.status_code == 201
    assert res.json()["user"]["username"] == "noname"


def test_register_duplicate_username_rejected(client):
    _register(client, "charlie", "c1@example.com")
    res = client.post("/users/register", json={
        "username": "charlie",
        "email": "c2@example.com",
        "password": "p",
    })
    assert res.status_code == 400


def test_register_duplicate_email_rejected(client):
    _register(client, "dave1", "dave@example.com")
    res = client.post("/users/register", json={
        "username": "dave2",
        "email": "dave@example.com",
        "password": "p",
    })
    assert res.status_code == 400


def test_register_invalid_email_rejected(client):
    res = client.post("/users/register", json={
        "username": "eve",
        "email": "not-an-email",
        "password": "pass",
    })
    assert res.status_code == 422


def test_register_missing_fields_rejected(client):
    res = client.post("/users/register", json={"username": "incomplete"})
    assert res.status_code == 422


# ── User Login Tests ──────────────────────────────────────────────────────────

def test_login_success(client):
    _register(client, "frank", password="mypassword")
    res = _login(client, "frank@example.com", "mypassword")
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Login successful"
    assert data["user"]["username"] == "frank"
    assert "id" in data["user"]
    assert "token" in data
    assert len(data["token"]) > 0


def test_login_returns_jwt(client):
    _register(client, "tokencheck", password="pass1234")
    res = _login(client, "tokencheck@example.com", "pass1234")
    assert res.status_code == 200
    token = res.json()["token"]
    parts = token.split(".")
    assert len(parts) == 3


def test_login_wrong_password(client):
    _register(client, "grace", password="correctpass")
    res = _login(client, "grace@example.com", "wrongpass")
    assert res.status_code == 401


def test_login_nonexistent_user(client):
    res = _login(client, "nobody@example.com", "pass")
    assert res.status_code == 401


def test_login_response_omits_password(client):
    _register(client, "henry", password="secret")
    res = _login(client, "henry@example.com", "secret")
    user_data = res.json()["user"]
    assert "password" not in user_data
    assert "password_hash" not in user_data


def test_login_verifies_hashed_password_in_db(client, db_session):
    from app import models
    _register(client, "iris", password="mypass")
    user = db_session.query(models.User).filter_by(username="iris").first()
    assert user is not None
    assert user.password_hash != "mypass"
    from app.auth import verify_password
    assert verify_password("mypass", user.password_hash)


# ── User Read/Delete Tests ────────────────────────────────────────────────────

def test_get_user_by_id(client):
    user_id = _register(client, "jack")
    res = client.get(f"/users/{user_id}")
    assert res.status_code == 200
    assert res.json()["username"] == "jack"


def test_get_nonexistent_user_returns_404(client):
    assert client.get("/users/99999").status_code == 404


def test_list_users(client):
    _register(client, "user_a", "ua@example.com")
    _register(client, "user_b", "ub@example.com")
    res = client.get("/users/")
    assert res.status_code == 200
    assert len(res.json()) >= 2


def test_delete_user(client):
    user_id = _register(client, "todelete")
    assert client.delete(f"/users/{user_id}").status_code == 204
    assert client.get(f"/users/{user_id}").status_code == 404


# ── Calculation Add (POST) Tests ──────────────────────────────────────────────

def test_add_calculation_add(client):
    user_id = _register(client, "cu1")
    data = _add_calc(client, user_id, 10, 5, "Add")
    assert data["result"] == 15.0
    assert data["type"] == "Add"


def test_add_calculation_sub(client):
    user_id = _register(client, "cu2")
    data = _add_calc(client, user_id, 20, 8, "Sub")
    assert data["result"] == 12.0


def test_add_calculation_multiply(client):
    user_id = _register(client, "cu3")
    data = _add_calc(client, user_id, 6, 7, "Multiply")
    assert data["result"] == 42.0


def test_add_calculation_divide(client):
    user_id = _register(client, "cu4")
    data = _add_calc(client, user_id, 15, 3, "Divide")
    assert data["result"] == 5.0


def test_add_calculation_stores_user_id(client):
    user_id = _register(client, "cu5")
    data = _add_calc(client, user_id, 4, 4, "Add")
    assert data["user_id"] == user_id


def test_add_calculation_has_timestamp(client):
    user_id = _register(client, "cu6")
    data = _add_calc(client, user_id, 1, 1, "Add")
    assert data.get("timestamp") is not None


def test_add_calculation_invalid_user(client):
    res = client.post("/calculations/", json={"a": 5, "b": 3, "type": "Add", "user_id": 99999})
    assert res.status_code == 404


def test_add_calculation_divide_by_zero(client):
    user_id = _register(client, "cu7")
    res = client.post("/calculations/", json={"a": 10, "b": 0, "type": "Divide", "user_id": user_id})
    assert res.status_code == 422


def test_add_calculation_invalid_type(client):
    user_id = _register(client, "cu8")
    res = client.post("/calculations/", json={"a": 5, "b": 3, "type": "Power", "user_id": user_id})
    assert res.status_code == 422


# ── Calculation Browse (GET /) Tests ──────────────────────────────────────────

def test_browse_calculations(client):
    user_id = _register(client, "browse_user")
    _add_calc(client, user_id, 1, 2, "Add")
    _add_calc(client, user_id, 3, 4, "Multiply")
    res = client.get("/calculations/")
    assert res.status_code == 200
    assert len(res.json()) >= 2


def test_browse_returns_list(client):
    res = client.get("/calculations/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ── Calculation Read (GET /{id}) Tests ────────────────────────────────────────

def test_read_calculation_by_id(client):
    user_id = _register(client, "read_user")
    created = _add_calc(client, user_id, 4, 4, "Add")
    calc_id = created["id"]
    res = client.get(f"/calculations/{calc_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["a"] == 4.0
    assert data["b"] == 4.0
    assert data["result"] == 8.0
    assert data["type"] == "Add"
    assert data["user_id"] == user_id


def test_read_nonexistent_calculation_returns_404(client):
    assert client.get("/calculations/99999").status_code == 404


# ── Calculation Edit (PUT /{id}) Tests ────────────────────────────────────────

def test_edit_calculation_change_operands(client):
    user_id = _register(client, "edit_user1")
    calc = _add_calc(client, user_id, 10, 5, "Add")
    calc_id = calc["id"]
    res = client.put(f"/calculations/{calc_id}", json={"a": 20, "b": 10})
    assert res.status_code == 200
    data = res.json()
    assert data["a"] == 20.0
    assert data["b"] == 10.0
    assert data["result"] == 30.0
    assert data["type"] == "Add"


def test_edit_calculation_change_type(client):
    user_id = _register(client, "edit_user2")
    calc = _add_calc(client, user_id, 6, 3, "Add")
    calc_id = calc["id"]
    res = client.put(f"/calculations/{calc_id}", json={"type": "Multiply"})
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "Multiply"
    assert data["result"] == 18.0


def test_edit_calculation_partial_update(client):
    user_id = _register(client, "edit_user3")
    calc = _add_calc(client, user_id, 10, 2, "Divide")
    calc_id = calc["id"]
    res = client.put(f"/calculations/{calc_id}", json={"a": 20})
    assert res.status_code == 200
    data = res.json()
    assert data["a"] == 20.0
    assert data["b"] == 2.0
    assert data["result"] == 10.0


def test_edit_calculation_result_recomputed(client):
    user_id = _register(client, "edit_user4")
    calc = _add_calc(client, user_id, 5, 5, "Sub")
    calc_id = calc["id"]
    res = client.put(f"/calculations/{calc_id}", json={"a": 100, "b": 40})
    assert res.status_code == 200
    assert res.json()["result"] == 60.0


def test_edit_nonexistent_calculation_returns_404(client):
    res = client.put("/calculations/99999", json={"a": 1})
    assert res.status_code == 404


def test_edit_calculation_divide_by_zero_rejected(client):
    user_id = _register(client, "edit_user5")
    calc = _add_calc(client, user_id, 10, 5, "Divide")
    calc_id = calc["id"]
    res = client.put(f"/calculations/{calc_id}", json={"b": 0})
    assert res.status_code == 422


# ── Calculation Delete Tests ──────────────────────────────────────────────────

def test_delete_calculation(client):
    user_id = _register(client, "del_user")
    calc = _add_calc(client, user_id, 2, 2, "Multiply")
    calc_id = calc["id"]
    assert client.delete(f"/calculations/{calc_id}").status_code == 204
    assert client.get(f"/calculations/{calc_id}").status_code == 404


def test_delete_nonexistent_calculation_returns_404(client):
    assert client.delete("/calculations/99999").status_code == 404


def test_delete_user_cascades_calculations(client):
    user_id = _register(client, "cascade_user")
    calc = _add_calc(client, user_id, 5, 5, "Add")
    calc_id = calc["id"]
    client.delete(f"/users/{user_id}")
    assert client.get(f"/calculations/{calc_id}").status_code == 404


# ── Join Query Tests ──────────────────────────────────────────────────────────

def test_join_query_returns_username(client):
    user_id = _register(client, "join_user")
    _add_calc(client, user_id, 3, 3, "Add")
    res = client.get("/calculations/join/all")
    assert res.status_code == 200
    entries = res.json()
    assert any(e["username"] == "join_user" for e in entries)


# ── Health Check ──────────────────────────────────────────────────────────────

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

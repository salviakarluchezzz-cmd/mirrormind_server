from fastapi import FastAPI, Request
import hashlib

app = FastAPI()

# ========= НАСТРОЙКИ =========

# Секрет ЮMoney из настроек уведомлений (пока-пустышка, потом заменишь)
YOOMONEY_SECRET = "YOUR_SECRET_HERE"

# Сумма, начиная с которой даём PRO-доступ (можно менять)
MIN_PRO_AMOUNT = 290.0

# MVP-хранилище оплаченных пользователей в памяти
# ключ: telegram_id (строка), значение: True
paid_users = {}


def check_signature(params: dict) -> bool:
    """
    Проверка подписи уведомления от ЮMoney.
    Формула описана в документации QuickPay.
    """
    s = ";".join([
        params.get("notification_type", ""),
        params.get("operation_id", ""),
        params.get("amount", ""),
        params.get("currency", ""),
        params.get("datetime", ""),
        params.get("sender", ""),
        params.get("codepro", ""),
        YOOMONEY_SECRET,
        params.get("label", ""),
    ])
    sha = hashlib.sha1(s.encode("utf-8")).hexdigest()
    return sha == params.get("sha1_hash")


@app.get("/health")
async def health():
    """
    Простой health-check, чтобы проверять, что сервер жив.
    """
    return {"status": "ok"}


@app.post("/yoomoney/callback")
async def yoomoney_callback(request: Request):
    """
    Эндпоинт, который будет дергать ЮMoney после успешного платежа.
    """
    form = dict(await request.form())

    # Проверяем подпись
    if not check_signature(form):
        return "invalid signature"

    label = form.get("label")  # сюда мы передаём telegram_id из бота
    amount_str = form.get("amount", "0") or "0"

    try:
        amount = float(amount_str.replace(",", "."))
    except ValueError:
        amount = 0.0

    if not label:
        return "no label"

    # Простая логика: любая оплата >= MIN_PRO_AMOUNT даёт доступ PRO
    if amount >= MIN_PRO_AMOUNT:
        paid_users[label] = True

    return "ok"


@app.get("/check_access")
async def check_access(user_id: str):
    """
    Бот будет спрашивать тут, есть ли у пользователя PRO-доступ.
    """
    has_access = paid_users.get(user_id, False)
    return {"pro": has_access}

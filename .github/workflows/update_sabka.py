import requests
import base64
import os
import re
import feedparser
from datetime import datetime


# =====================
# НАСТРОЙКИ
# =====================

PUB_TOKEN = os.environ["PUB_TOKEN"]

FILE = "RizzyVPN-Free.txt"
CHANNEL = "@RizzyVPN"

RSS_FEED_URL = "https://rss.app/feeds/akOKCzaTuxmRKJgr.xml"

COUNTRY_NAME = "Польша"

FLAG_URL = "%F0%9F%87%B5%F0%9F%87%B1"

ANCHOR = (
    "%D0%91%D0%95%D0%A1%D0%9F%D0%9B%D0%90%D0%A2%D0%9D%D0%AB%D0%99"
    "%20VPN%20%D0%92%20t.me%2FRizzyVPN"
)


# =====================
# ЛОГИ
# =====================

def log(text):
    print(f"[RizzyVPN] {text}")


# =====================
# ОПРЕДЕЛЕНИЕ ПРОТОКОЛА
# =====================

def detect_proto(key):
    if key.startswith("hysteria2://"):
        return "HY2"

    if "type=xhttp" in key:
        return "VLx"

    return "VL"


# =====================
# СОЗДАНИЕ КОММЕНТАРИЯ
# =====================

def build_comment(proto):
    date = datetime.now().strftime("%d.%m")

    text = f"{proto} | RizzyVPN до {date}"

    encoded = text.encode("utf-8").hex().upper()

    result = ""

    for i in range(0, len(encoded), 2):
        result += "%" + encoded[i:i+2]

    return f"{FLAG_URL}%20{result}"
    # =====================
# БЕЗОПАСНОЕ ОЧИЩЕНИЕ КЛЮЧА
# =====================

def clean_key(key):
    # удаляем старый комментарий
    if "#" in key:
        key = key.split("#")[0]

    # убираем пробелы
    key = key.strip()

    return key


# =====================
# ПОЛУЧЕНИЕ ССЫЛКИ НА САБКУ
# =====================

def get_subscription_url():
    log("Читаем RSS...")

    feed = feedparser.parse(RSS_FEED_URL)

    if not feed.entries:
        raise Exception("RSS пустой")

    for entry in feed.entries:
        text = (
            entry.get("summary", "")
            + " "
            + entry.get("title", "")
        )

        links = re.findall(
            r"https?://[^\s\"<>]+",
            text
        )

        for url in links:
            if "sb.embrofree.org" in url.lower():
                log(f"Найдена сабка: {url}")
                return url, entry

    raise Exception("Ссылка на сабку не найдена")


# =====================
# СКАЧИВАНИЕ САБКИ
# =====================

def download_subscription(url):
    log("Скачиваем подписку...")

    response = requests.get(
        url,
        timeout=30,
        verify=False
    )

    response.raise_for_status()

    return response.text
    # =====================
# ПОИСК КЛЮЧЕЙ
# =====================

def extract_keys(data):
    log("Ищем ключи...")

    keys = []

    # обычная подписка
    found = re.findall(
        r"(?:vless|hysteria2)://[^\s#\"<>]+",
        data
    )

    keys.extend(found)

    # если это base64
    if not keys:
        try:
            decoded = base64.b64decode(
                data
            ).decode(
                "utf-8",
                errors="ignore"
            )

            found = re.findall(
                r"(?:vless|hysteria2)://[^\s#\"<>]+",
                decoded
            )

            keys.extend(found)

        except Exception:
            pass


    # убрать дубли
    keys = list(dict.fromkeys(keys))


    if not keys:
        raise Exception(
            "Ключи не найдены"
        )


    log(
        f"Найдено ключей: {len(keys)}"
    )

    return keys


# =====================
# СОЗДАНИЕ НОВОЙ САБКИ
# =====================

def build_subscription(keys):
    log("Обрабатываем ключи...")

    new_keys = []

    for key in keys:
        key = clean_key(key)

        proto = detect_proto(key)

        comment = build_comment(proto)

        # НЕ трогаем vless:// или hysteria2://
        new_key = key + "#" + comment

        new_keys.append(new_key)

    return new_keys
    # =====================
# СОХРАНЕНИЕ ФАЙЛА
# =====================

def save_subscription(keys):
    log("Сохраняем подписку...")

    content = "\n".join(keys)

    with open(
        FILE,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(content)

    log(
        f"Сохранено ключей: {len(keys)}"
    )


# =====================
# ПОЛУЧЕНИЕ ПРОТОКОЛОВ
# =====================

def get_protocols(keys):
    protocols = set()

    for key in keys:
        protocols.add(
            detect_proto(key)
        )

    return ", ".join(
        sorted(protocols)
    )


# =====================
# ПУБЛИКАЦИЯ В TELEGRAM
# =====================

def send_telegram(protocols):
    log("Создаём пост...")

    text = (
        "<b>Rizzy конфигурация #VPN</b>\n\n"
        "🔑 Автоматически обновлённая сабка\n\n"
        f"🌎 Локация: {COUNTRY_NAME}\n"
        f"⚡️ Протоколы: {protocols}\n\n"
        "📎 Сабка:\n"
        "<code>"
        "https://raw.githubusercontent.com/"
        "rizzyprotogen/RizzyVPN-t.me-RizzyVPN/"
        "main/RizzyVPN-Free.txt"
        "</code>\n\n"
        "❤️ Поддержи проект!"
    )

    url = (
        f"https://api.telegram.org/"
        f"bot{PUB_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    response = requests.post(
        url,
        json=payload,
        timeout=20
    )

    if response.status_code == 200:
        log("Пост отправлен ✅")
    else:
        log(
            f"Ошибка Telegram: {response.text}"
        )
        # =====================
# ЗАПУСК
# =====================

def main():
    try:
        url, entry = get_subscription_url()

        data = download_subscription(url)

        keys = extract_keys(data)

        new_keys = build_subscription(keys)

        save_subscription(new_keys)

        protocols = get_protocols(new_keys)

        send_telegram(protocols)

        log(
            "Готово! Обновление завершено 🚀"
        )

    except Exception as e:
        log(
            f"ОШИБКА: {e}"
        )
        raise


if __name__ == "__main__":
    main()

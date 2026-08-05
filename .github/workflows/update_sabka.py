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

COUNTER_FILE = "counter.txt"

RSS_FEED_URL = "https://rss.app/feeds/akOKCzaTuxmRKJgr.xml"

COUNTRY_NAME = "Польша"

FLAG_URL = "%F0%9F%87%B5%F0%9F%87%B1"


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
# ОЧИСТКА КЛЮЧА
# =====================

def clean_key(key):

    if "#" in key:
        key = key.split("#")[0]

    return key.strip()
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
            +
            " "
            +
            entry.get("title", "")
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
# ПОИСК VPN КЛЮЧЕЙ
# =====================

def extract_keys(data):

    log("Ищем ключи...")


    keys = []


    found = re.findall(
        r"(?:vless|hysteria2)://[^\s#\"<>]+",
        data
    )


    keys.extend(found)



    # Если подписка была base64

    if not keys:

        try:

            decoded = base64.b64decode(data).decode(
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



    # Убираем дубли

    keys = list(dict.fromkeys(keys))


    if not keys:

        raise Exception("Ключи не найдены")


    log(f"Найдено ключей: {len(keys)}")


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
# ЧТЕНИЕ ИНФОРМАЦИИ ИЗ ПОСТА
# =====================

def parse_post_info(post_info):

    result = {

        "title": "🔑 Публичная сабка",

        "contact": "",

        "location": "",

        "limit": ""

    }



    post_info = re.sub(

        r"<br\s*/?>",

        "\n",

        post_info

    )



    # Название

    match = re.search(

        r"(🔑.*?)(?=\n|🌎|По вопросам)",

        post_info

    )



    if match:

        title = match.group(1).strip()


        title = re.sub(

            r"\s*#\d+",

            "",

            title

        )


        result["title"] = title




    # Контакт

    match = re.search(

        r"По вопросам.*?(?=\n|🌎|$)",

        post_info

    )



    if match:

        contact = match.group(0).strip()


        contact = re.sub(

            r"@\w+https?://[^)]+",

            "@RizzyVPN",

            contact

        )


        result["contact"] = contact




    # Локация

    match = re.search(

        r"🌎\s*(?:\S+\s+)?(.+?)(?=\s+с протоколами|\n|$)",

        post_info

    )



    if match:

        result["location"] = match.group(1).strip()




    # Лимит

    match = re.search(

        r"Общий лимит.*?(?=\n|$)",

        post_info

    )



    if match:

        result["limit"] = match.group(0).strip()



    return result




# =====================
# СЧЁТЧИК ПОСТОВ
# =====================

def get_post_number():

    if not os.path.exists(COUNTER_FILE):

        return 0


    with open(
        COUNTER_FILE,
        "r"
    ) as f:

        return int(
            f.read().strip()
        )



def save_post_number(number):

    with open(
        COUNTER_FILE,
        "w"
    ) as f:

        f.write(
            str(number)
            # =====================
# СОЗДАНИЕ ПОСТА
# =====================

def build_post(info, keys):

    number = get_post_number() + 1

    protocols = get_protocols(keys)


    text = f"""
{info["title"]}

🌎 {info["location"]}

🇵🇱 Страна: {COUNTRY_NAME}

⚡ Протоколы: {protocols}

📦 Серверов: {len(keys)}

{info["limit"]}

{info["contact"]}

📅 Обновлено: {datetime.now().strftime("%d.%m.%Y")}


⬇️ Скачать VPN:
https://t.me/{CHANNEL.replace("@", "")}


#{number}
"""


    return text.strip(), number



# =====================
# ОТПРАВКА В TELEGRAM
# =====================

def send_post(text):

    log("Отправляем пост...")


    url = (
        "https://api.telegram.org/"
        f"bot{PUB_TOKEN}/sendMessage"
    )


    data = {

        "chat_id": CHANNEL,

        "text": text,

        "disable_web_page_preview": True

    }


    response = requests.post(

        url,

        data=data,

        timeout=30

    )


    response.raise_for_status()


    log("Пост отправлен")



# =====================
# ГЛАВНАЯ ФУНКЦИЯ
# =====================

def main():

    log("=== RizzyVPN Auto Start ===")


    url, entry = get_subscription_url()


    raw = download_subscription(url)


    keys = extract_keys(raw)


    new_keys = build_subscription(keys)


    save_subscription(new_keys)



    post_info = (

        entry.get("summary", "")

        +

        "\n"

        +

        entry.get("title", "")

    )


    info = parse_post_info(post_info)



    post, number = build_post(

        info,

        new_keys

    )



    send_post(post)



    save_post_number(number)



    log("=== Готово ===")



# =====================
# ЗАПУСК
# =====================

if __name__ == "__main__":

    main()

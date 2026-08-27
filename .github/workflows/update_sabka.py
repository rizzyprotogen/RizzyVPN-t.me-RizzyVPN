# RizzyVPN Auto - СТИЛЬ RIZZY
import requests
import base64
import os
import re
import feedparser
from datetime import datetime

# =====================
# НАСТРОЙКИ
# =====================

PUB_TOKEN = os.environ.get("PUB_TOKEN", "")

if not PUB_TOKEN:
    print("[RizzyVPN] ОШИБКА: PUB_TOKEN не найден в переменных окружения!")
    exit(1)

FILE = "RizzyVPN-Free.txt"
CHANNEL = "@RizzyVPN"
COUNTER_FILE = "counter.txt"

RSS_FEED_URL = "https://rsshub.app/telegram/channel/freekvn"
FALLBACK_URL = "https://t.me/s/freekvn"

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
    log("Пробуем RSSHub...")
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if feed.entries:
            for entry in feed.entries[:1]:
                text = entry.get("summary", "") + " " + entry.get("title", "")
                links = re.findall(r"https?://[^\s\"<>]+", text)
                for url in links:
                    if "sb.embrofree.org" in url.lower():
                        log(f"✅ Найдена сабка через RSSHub: {url}")
                        return url, entry
    except Exception as e:
        log(f"⚠️ RSSHub не работает: {e}")

    log("Пробуем парсинг t.me/s/freekvn...")
    try:
        html = requests.get(FALLBACK_URL, timeout=30).text
        match = re.search(r'https?://sb\.embrofree\.org[^\s"<>]+', html)
        if match:
            url = match.group(0)
            log(f"✅ Найдена сабка через парсинг: {url}")
            return url, None
    except Exception as e:
        log(f"⚠️ Парсинг не удался: {e}")

    raise Exception("Не удалось получить ссылку на сабку")

# =====================
# СКАЧИВАНИЕ САБКИ
# =====================

def download_subscription(url):
    log("Скачиваем подписку...")
    try:
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        log(f"Ошибка скачивания: {e}")
        raise

# =====================
# ПОИСК VPN КЛЮЧЕЙ
# =====================

def extract_keys(data):
    log("Ищем ключи...")
    keys = []
    
    found = re.findall(r"(?:vless|hysteria2)://[^\s#\"<>]+", data)
    keys.extend(found)
    
    if not keys:
        try:
            decoded = base64.b64decode(data).decode("utf-8", errors="ignore")
            found = re.findall(r"(?:vless|hysteria2)://[^\s#\"<>]+", decoded)
            keys.extend(found)
        except Exception as e:
            log(f"Ошибка декодирования base64: {e}")
    
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
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(content)
    log(f"Сохранено ключей: {len(keys)}")

# =====================
# ПОЛУЧЕНИЕ ПРОТОКОЛОВ
# =====================

def get_protocols(keys):
    protocols = set()
    for key in keys:
        protocols.add(detect_proto(key))
    return ", ".join(sorted(protocols))

# =====================
# СЧЁТЧИК ПОСТОВ
# =====================

def get_post_number():
    if not os.path.exists(COUNTER_FILE):
        return 0
    try:
        with open(COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_post_number(number):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(number))

# =====================
# ГЕНЕРАЦИЯ RSS ФИДА (feed.xml)
# =====================

def generate_feed(keys):
    log("Генерируем feed.xml...")
    try:
        import xml.etree.ElementTree as ET
        
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        
        ET.SubElement(channel, "title").text = "RizzyVPN Free"
        ET.SubElement(channel, "link").text = "https://t.me/RizzyVPN"
        ET.SubElement(channel, "description").text = "Бесплатные VPN-ключи"
        
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"VPN Keys {datetime.now().strftime('%d.%m.%Y')}"
        ET.SubElement(item, "description").text = "\n".join(keys[:10])
        ET.SubElement(item, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        tree = ET.ElementTree(rss)
        tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
        log("✅ feed.xml обновлён")
    except Exception as e:
        log(f"⚠️ Ошибка генерации feed.xml: {e}")

# =====================
# ГЛАВНАЯ ФУНКЦИЯ
# =====================

def main():
    log("=== RizzyVPN Auto Start ===")
    
    try:
        url, entry = get_subscription_url()
        raw = download_subscription(url)
        keys = extract_keys(raw)
        new_keys = build_subscription(keys)
        save_subscription(new_keys)
        generate_feed(new_keys)
        
        # ========================================
        # ПОСТ В СТИЛЕ RIZZY (ТВОЙ ВАРИАНТ)
        # ========================================
        number = get_post_number() + 1
        protocols = get_protocols(new_keys)
        
        text = f"""
Rizzy конфигурация #VPN

🔑Публичная сабка до 7.08, либо до исчерпания трафика. #{number}

По вопросам писать @EmbroKVN. Помогаю бесплатно!

🌎 Локация: Польша
⚡️ Протоколы: {protocols}

📎 Сабка:
https://raw.githubusercontent.com/rizzyprotogen/RizzyVPN-t.me-RizzyVPN/main/RizzyVPN-Free.txt#%D0%91%D0%95%D0%A1%D0%9F%D0%9B%D0%90%D0%A2%D0%9D%D0%AB%D0%99%20VPN%20%D0%92%20t.me%2FRizzyVPN

❤️ Поставь сердечко.
📢 Перешли ключ друзьям.
"""
        send_post(text.strip())
        save_post_number(number)
        
        log("=== Готово ===")
    except Exception as e:
        log(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        raise

# =====================
# ОТПРАВКА В TELEGRAM
# =====================

def send_post(text):
    log("Отправляем пост...")
    url = f"https://api.telegram.org/bot{PUB_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL,
        "text": text,
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        log("Пост отправлен")
    except Exception as e:
        log(f"Ошибка отправки: {e}")
        raise

# =====================
# ЗАПУСК
# =====================

if __name__ == "__main__":
    main()

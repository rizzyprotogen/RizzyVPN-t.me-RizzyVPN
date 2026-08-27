import requests, re, html, os
from datetime import datetime, timezone

CHANNEL = "freekvn"
URL = f"https://t.me/s/{CHANNEL}"
OUTPUT_FILE = "feed.xml"


def fetch_posts():
    """Достаёт посты из веб-версии Telegram-канала."""
    try:
        resp = requests.get(URL, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return []

    # Находим блоки с текстом сообщений
    raw_posts = re.findall(
        r'<div class="tgme_widget_message_text js-message_text".*?</div>',
        resp.text,
        re.DOTALL,
    )
    posts = []
    for raw in raw_posts:
        # Убираем HTML-теги и лишние пробелы
        text = re.sub(r"<br/>", "\n", raw)
        text = re.sub(r"<.*?>", "", text)
        text = html.unescape(text)
        text = text.strip()
        if text:
            posts.append(text)
    return posts


def build_rss(posts):
    """Собирает валидный RSS-файл из списка постов."""
    items = []
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    for i, post in enumerate(posts[:5]):  # Берём последние 5 постов
        title = post[:100].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        desc = post.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        items.append(
            f"""<item>
      <title>{title}</title>
      <description>{desc}</description>
      <pubDate>{now}</pubDate>
      <guid>https://t.me/s/{CHANNEL}/post-{i}</guid>
    </item>"""
        )

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{CHANNEL}</title>
    <link>https://t.me/s/{CHANNEL}</link>
    <description>Автоматическая RSS-лента для RizzyVPN</description>
    {''.join(items)}
  </channel>
</rss>"""
    return rss


def main():
    posts = fetch_posts()
    if posts:
        rss_content = build_rss(posts)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_content)
        print(f"✅ RSS обновлена: {len(posts)} постов.")
    else:
        print("❌ Посты не найдены. RSS не обновлена.")


if __name__ == "__main__":
    main()

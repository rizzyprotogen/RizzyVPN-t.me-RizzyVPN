import requests, base64, json, os, re, feedparser
from bs4 import BeautifulSoup

TOKEN = os.environ['GH_TOKEN']
PUB_TOKEN = os.environ['PUB_TOKEN']
REPO = 'rizzyprotogen/RizzyVPN-t.me-RizzyVPN'
FILE = 'RizzyVPN-Free.txt'
CHANNEL = '@RizzyVPN'
RSS_FEED_URL = 'https://rss.app/feeds/Z1ZlIWdpk8TJRDfs.xml'
COUNTER_FILE = 'counter.txt'
ANCHOR = '%D0%91%D0%95%D0%A1%D0%9F%D0%9B%D0%90%D0%A2%D0%9D%D0%AB%D0%99%20VPN%20%D0%92%20t.me%2FRizzyVPN'
COUNTRY_NAME = 'Польша'
FLAG_URL = '%F0%9F%87%B5%F0%9F%87%B1'

def detect_proto(key):
    if key.startswith('hysteria2://'): return 'HY2'
    if 'type=xhttp' in key or 'xhttp' in key.split('&'): return 'VLx'
    return 'VL'

def build_rizzy_comment(proto, date):
    comment_text = f'{proto} | RizzyVPN до {date}'
    comment_encoded = comment_text.encode().hex().upper()
    comment_url = ''.join(f'%{comment_encoded[i:i+2]}' for i in range(0, len(comment_encoded), 2))
    return f'{FLAG_URL}%20{comment_url}'

def get_next_issue():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE) as f:
            last = f.read().strip()
        next_issue = int(last) + 1 if last.isdigit() else 1
    else:
        next_issue = 1
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(next_issue))
    return next_issue

feed = feedparser.parse(RSS_FEED_URL)
if not feed.entries:
    print('Нет записей в RSS.')
    exit(0)

sub_url = None
entry_with_sub = None
for entry in feed.entries:
    text = entry.get('summary', entry.get('title', ''))
    match = re.search(r'https?://\S+/kvn/\S+', text)
    if match:
        sub_url = match.group(0)
        entry_with_sub = entry
        break

if not sub_url:
    print('Пост с сабкой не найден.')
    exit(0)

resp = requests.get(sub_url, verify=False, timeout=30)
if resp.status_code != 200:
    print(f'Ошибка скачивания: {resp.status_code}')
    exit(1)

soup = BeautifulSoup(resp.text, 'html.parser')
copy_btn = soup.find('button', string=re.compile(r'копировать все конфигурации', re.I))
if copy_btn:
    parent = copy_btn.find_parent()
    keys_raw = re.findall(r'(vless|hysteria2)://[^\s#\"]+', parent.get_text())
else:
    keys_raw = re.findall(r'(vless|hysteria2)://[^\s#\"]+', resp.text)

if not keys_raw:
    try:
        decoded = base64.b64decode(resp.text).decode('utf-8', errors='ignore')
        keys_raw = re.findall(r'(vless|hysteria2)://[^\s#\"]+', decoded)
    except:
        pass

if not keys_raw:
    print('Ключи не найдены.')
    exit(1)

print(f'Найдено ключей: {len(keys_raw)}')
date_match = re.search(r'до (\d{2}\.\d{2})', entry_with_sub.get('title', ''))
date = date_match.group(1) if date_match else '01.01'

new_keys = []
for key in keys_raw:
    if '#' in key:
        key = key[:key.find('#')]
    proto = detect_proto(key)
    comment = build_rizzy_comment(proto, date)
    new_keys.append(key + '#' + comment)

content = '\n'.join(new_keys)
with open(FILE, 'w') as f:
    f.write(content)

issue = get_next_issue()
protos = set()
for k in new_keys:
    protos.add(detect_proto(k))
protos_str = ', '.join(sorted(protos))

text = f'<b>Rizzy конфигурация #VPN</b>\n\n'
text += f'🔑 Публичная сабка #{issue} до {date}\n\n'
text += f'По вопросам писать @famchilli_bot. Помогаю бесплатно!\n\n'
text += f'🌎 Локация: {COUNTRY_NAME} [{protos_str}]\n'
text += f'⚡️ Протоколы: {protos_str}\n'
text += f'ℹ️ Общий лимит 3 ТБ, без ограничений по устройствам\n\n'
text += f'📎 Сабка:\n<code>https://raw.githubusercontent.com/rizzyprotogen/RizzyVPN-t.me-RizzyVPN/main/RizzyVPN-Free.txt#{ANCHOR}</code>\n\n'
text += f'Поддержи проект:\n❤️ Поставь сердечко.\n📢 Перешли ключ друзьям.'

url = f'https://api.telegram.org/bot{PUB_TOKEN}/sendMessage'
payload = {
    'chat_id': CHANNEL,
    'text': text,
    'parse_mode': 'HTML',
    'disable_web_page_preview': True
}
resp = requests.post(url, json=payload)
if resp.status_code == 200:
    print('✅ Пост опубликован в канале!')
else:
    print(f'❌ Ошибка публикации: {resp.status_code} {resp.text}')

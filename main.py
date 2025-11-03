import time
import requests
import json
import re
import os
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
from pathlib import Path
import sqlite3
import telebot
import traceback
from telebot import types
import threading
import random

# ======================
# ⚙️ الإعدادات الأصلية (من الملف المرفق)
# ======================
BASE = "http://109.236.84.81"
AJAX_PATH = "/ints/agent/res/data_smscdr.php"
LOGIN_PAGE_URL = BASE + "/ints/login"
LOGIN_POST_URL = BASE + "/ints/signin"
USERNAME = "Albrans"
PASSWORD = "Albrans000"
BOT_TOKEN = "8438435636:AAH9hg5ZzS0BK1JNPbXXy3ZnU-gh0D5aw6I"
#$#$
CHAT_FILE = "chat_ids.json"

def load_chat_ids():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return ["-1002805778712"]  # القيمة الافتراضية

def save_chat_ids(chat_ids):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_ids, f, ensure_ascii=False, indent=2)

CHAT_IDS = load_chat_ids()
#$##$
REFRESH_INTERVAL = 5
TIMEOUT = 500
MAX_RETRIES = 5
RETRY_DELAY = 5
IDX_DATE = 0
IDX_NUMBER = 2
IDX_SMS = 5
SENT_MESSAGES_FILE = "sent_messages.json"

# ======================
# ⚙️ إعدادات البوت التفاعلي الجديد
# ======================
ADMIN_IDS = [8038053114]  # ❗ غيّر هذا إلى معرفك الحقيقي في Telegram
DB_PATH = "bot.db"
FORCE_SUB_CHANNEL = None
FORCE_SUB_ENABLED = False

# ======================
# 🔒 التحقق من المتغيرات
# ======================
if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN must be set in Secrets (Environment Variables)")
if not CHAT_IDS:
    raise SystemExit("❌ CHAT_IDS must be configured")
if not USERNAME or not PASSWORD:
    print("⚠️  WARNING: SITE_USERNAME and SITE_PASSWORD not set in Secrets")
    print("⚠️  Bot will continue but login may fail")

# ======================
# 🌍 قاعدة بيانات الدول (كاملة كما في الملف الأصلي)
# ======================
COUNTRY_CODES = {
    "1": ("USA/Canada", "🇺🇸", "USA/CANADA"),
    "7": ("Russia", "🇷🇺", "RUSSIA"),
    "20": ("Egypt", "🇪🇬", "EGYPT"),
    "27": ("South Africa", "🇿🇦", "SOUTH AFRICA"),
    "30": ("Greece", "🇬🇷", "GREECE"),
    "31": ("Netherlands", "🇳🇱", "NETHERLANDS"),
    "32": ("Belgium", "🇧🇪", "BELGIUM"),
    "33": ("France", "🇫🇷", "FRANCE"),
    "34": ("Spain", "🇪🇸", "SPAIN"),
    "36": ("Hungary", "🇭🇺", "HUNGARY"),
    "39": ("Italy", "🇮🇹", "ITALY"),
    "40": ("Romania", "🇷🇴", "ROMANIA"),
    "41": ("Switzerland", "🇨🇭", "SWITZERLAND"),
    "43": ("Austria", "🇦🇹", "AUSTRIA"),
    "44": ("UK", "🇬🇧", "UK"),
    "45": ("Denmark", "🇩🇰", "DENMARK"),
    "46": ("Sweden", "🇸🇪", "SWEDEN"),
    "47": ("Norway", "🇳🇴", "NORWAY"),
    "48": ("Poland", "🇵🇱", "POLAND"),
    "49": ("Germany", "🇩🇪", "GERMANY"),
    "51": ("Peru", "🇵🇪", "PERU"),
    "52": ("Mexico", "🇲🇽", "MEXICO"),
    "972": ("Israel", "🇮🇱", "ISRAEL"),
    "53": ("Cuba", "🇨🇺", "CUBA"),
    "54": ("Argentina", "🇦🇷", "ARGENTINA"),
    "55": ("Brazil", "🇧🇷", "BRAZIL"),
    "56": ("Chile", "🇨🇱", "CHILE"),
    "57": ("Colombia", "🇨🇴", "COLOMBIA"),
    "58": ("Venezuela", "🇻🇪", "VENEZUELA"),
    "60": ("Malaysia", "🇲🇾", "MALAYSIA"),
    "61": ("Australia", "🇦🇺", "AUSTRALIA"),
    "62": ("Indonesia", "🇮🇩", "INDONESIA"),
    "63": ("Philippines", "🇵🇭", "PHILIPPINES"),
    "64": ("New Zealand", "🇳🇿", "NEW ZEALAND"),
    "65": ("Singapore", "🇸🇬", "SINGAPORE"),
    "66": ("Thailand", "🇹🇭", "THAILAND"),
    "81": ("Japan", "🇯🇵", "JAPAN"),
    "82": ("South Korea", "🇰🇷", "SOUTH KOREA"),
    "84": ("Vietnam", "🇻🇳", "VIETNAM"),
    "86": ("China", "🇨🇳", "CHINA"),
    "90": ("Turkey", "🇹🇷", "TURKEY"),
    "91": ("India", "🇮🇳", "INDIA"),
    "92": ("Pakistan", "🇵🇰", "PAKISTAN"),
    "93": ("Afghanistan", "🇦🇫", "AFGHANISTAN"),
    "94": ("Sri Lanka", "🇱🇰", "SRI LANKA"),
    "95": ("Myanmar", "🇲🇲", "MYANMAR"),
    "98": ("Iran", "🇮🇷", "IRAN"),
    "211": ("South Sudan", "🇸🇸", "SOUTH SUDAN"),
    "212": ("Morocco", "🇲🇦", "MOROCCO"),
    "213": ("Algeria", "🇩🇿", "ALGERIA"),
    "216": ("Tunisia", "🇹🇳", "TUNISIA"),
    "218": ("Libya", "🇱🇾", "LIBYA"),
    "220": ("Gambia", "🇬🇲", "GAMBIA"),
    "221": ("Senegal", "🇸🇳", "SENEGAL"),
    "222": ("Mauritania", "🇲🇷", "MAURITANIA"),
    "223": ("Mali", "🇲🇱", "MALI"),
    "224": ("Guinea", "🇬🇳", "GUINEA"),
    "225": ("Ivory Coast", "🇨🇮", "IVORY COAST"),
    "226": ("Burkina Faso", "🇧🇫", "BURKINA FASO"),
    "227": ("Niger", "🇳🇪", "NIGER"),
    "228": ("Togo", "🇹🇬", "TOGO"),
    "229": ("Benin", "🇧🇯", "BENIN"),
    "230": ("Mauritius", "🇲🇺", "MAURITIUS"),
    "231": ("Liberia", "🇱🇷", "LIBERIA"),
    "232": ("Sierra Leone", "🇸🇱", "SIERRA LEONE"),
    "233": ("Ghana", "🇬🇭", "GHANA"),
    "234": ("Nigeria", "🇳🇬", "NIGERIA"),
    "235": ("Chad", "🇹🇩", "CHAD"),
    "236": ("CAR", "🇨🇫", "CENTRAL AFRICAN REP"),
    "237": ("Cameroon", "🇨🇲", "CAMEROON"),
    "238": ("Cape Verde", "🇨🇻", "CAPE VERDE"),
    "239": ("Sao Tome", "🇸🇹", "SAO TOME"),
    "240": ("Eq. Guinea", "🇬🇶", "EQUATORIAL GUINEA"),
    "241": ("Gabon", "🇬🇦", "GABON"),
    "242": ("Congo", "🇨🇬", "CONGO"),
    "243": ("DR Congo", "🇨🇩", "DR CONGO"),
    "244": ("Angola", "🇦🇴", "ANGOLA"),
    "245": ("Guinea-Bissau", "🇬🇼", "GUINEA-BISSAU"),
    "248": ("Seychelles", "🇸🇨", "SEYCHELLES"),
    "249": ("Sudan", "🇸🇩", "SUDAN"),
    "250": ("Rwanda", "🇷🇼", "RWANDA"),
    "251": ("Ethiopia", "🇪🇹", "ETHIOPIA"),
    "252": ("Somalia", "🇸🇴", "SOMALIA"),
    "253": ("Djibouti", "🇩🇯", "DJIBOUTI"),
    "254": ("Kenya", "🇰🇪", "KENYA"),
    "255": ("Tanzania", "🇹🇿", "TANZANIA"),
    "256": ("Uganda", "🇺🇬", "UGANDA"),
    "257": ("Burundi", "🇧🇮", "BURUNDI"),
    "258": ("Mozambique", "🇲🇿", "MOZAMBIQUE"),
    "260": ("Zambia", "🇿🇲", "ZAMBIA"),
    "261": ("Madagascar", "🇲🇬", "MADAGASCAR"),
    "262": ("Reunion", "🇷🇪", "REUNION"),
    "263": ("Zimbabwe", "🇿🇼", "ZIMBABWE"),
    "264": ("Namibia", "🇳🇦", "NAMIBIA"),
    "265": ("Malawi", "🇲🇼", "MALAWI"),
    "266": ("Lesotho", "🇱🇸", "LESOTHO"),
    "267": ("Botswana", "🇧🇼", "BOTSWANA"),
    "268": ("Eswatini", "🇸🇿", "ESWATINI"),
    "269": ("Comoros", "🇰🇲", "COMOROS"),
    "350": ("Gibraltar", "🇬🇮", "GIBRALTAR"),
    "351": ("Portugal", "🇵🇹", "PORTUGAL"),
    "352": ("Luxembourg", "🇱🇺", "LUXEMBOURG"),
    "353": ("Ireland", "🇮🇪", "IRELAND"),
    "354": ("Iceland", "🇮🇸", "ICELAND"),
    "355": ("Albania", "🇦🇱", "ALBANIA"),
    "356": ("Malta", "🇲🇹", "MALTA"),
    "357": ("Cyprus", "🇨🇾", "CYPRUS"),
    "358": ("Finland", "🇫🇮", "FINLAND"),
    "359": ("Bulgaria", "🇧🇬", "BULGARIA"),
    "370": ("Lithuania", "🇱🇹", "LITHUANIA"),
    "371": ("Latvia", "🇱🇻", "LATVIA"),
    "372": ("Estonia", "🇪🇪", "ESTONIA"),
    "373": ("Moldova", "🇲🇩", "MOLDOVA"),
    "374": ("Armenia", "🇦🇲", "ARMENIA"),
    "375": ("Belarus", "🇧🇾", "BELARUS"),
    "376": ("Andorra", "🇦🇩", "ANDORRA"),
    "377": ("Monaco", "🇲🇨", "MONACO"),
    "378": ("San Marino", "🇸🇲", "SAN MARINO"),
    "380": ("Ukraine", "🇺🇦", "UKRAINE"),
    "381": ("Serbia", "🇷🇸", "SERBIA"),
    "382": ("Montenegro", "🇲🇪", "MONTENEGRO"),
    "383": ("Kosovo", "🇽🇰", "KOSOVO"),
    "385": ("Croatia", "🇭🇷", "CROATIA"),
    "386": ("Slovenia", "🇸🇮", "SLOVENIA"),
    "387": ("Bosnia", "🇧🇦", "BOSNIA"),
    "389": ("N. Macedonia", "🇲🇰", "NORTH MACEDONIA"),
    "420": ("Czech Rep", "🇨🇿", "CZECH REPUBLIC"),
    "421": ("Slovakia", "🇸🇰", "SLOVAKIA"),
    "423": ("Liechtenstein", "🇱🇮", "LIECHTENSTEIN"),
    "500": ("Falkland", "🇫🇰", "FALKLAND ISLANDS"),
    "501": ("Belize", "🇧🇿", "BELIZE"),
    "502": ("Guatemala", "🇬🇹", "GUATEMALA"),
    "503": ("El Salvador", "🇸🇻", "EL SALVADOR"),
    "504": ("Honduras", "🇭🇳", "HONDURAS"),
    "505": ("Nicaragua", "🇳🇮", "NICARAGUA"),
    "506": ("Costa Rica", "🇨🇷", "COSTA RICA"),
    "507": ("Panama", "🇵🇦", "PANAMA"),
    "509": ("Haiti", "🇭🇹", "HAITI"),
    "591": ("Bolivia", "🇧🇴", "BOLIVIA"),
    "592": ("Guyana", "🇬🇾", "GUYANA"),
    "593": ("Ecuador", "🇪🇨", "ECUADOR"),
    "595": ("Paraguay", "🇵🇾", "PARAGUAY"),
    "597": ("Suriname", "🇸🇷", "SURINAME"),
    "598": ("Uruguay", "🇺🇾", "URUGUAY"),
    "670": ("Timor-Leste", "🇹🇱", "TIMOR-LESTE"),
    "673": ("Brunei", "🇧🇳", "BRUNEI"),
    "674": ("Nauru", "🇳🇷", "NAURU"),
    "675": ("PNG", "🇵🇬", "PAPUA NEW GUINEA"),
    "676": ("Tonga", "🇹🇴", "TONGA"),
    "677": ("Solomon Is", "🇸🇧", "SOLOMON ISLANDS"),
    "678": ("Vanuatu", "🇻🇺", "VANUATU"),
    "679": ("Fiji", "🇫🇯", "FIJI"),
    "680": ("Palau", "🇵🇼", "PALAU"),
    "685": ("Samoa", "🇼🇸", "SAMOA"),
    "686": ("Kiribati", "🇰🇮", "KIRIBATI"),
    "687": ("New Caledonia", "🇳🇨", "NEW CALEDONIA"),
    "688": ("Tuvalu", "🇹🇻", "TUVALU"),
    "689": ("Fr Polynesia", "🇵🇫", "FRENCH POLYNESIA"),
    "691": ("Micronesia", "🇫🇲", "MICRONESIA"),
    "692": ("Marshall Is", "🇲🇭", "MARSHALL ISLANDS"),
    "850": ("North Korea", "🇰🇵", "NORTH KOREA"),
    "852": ("Hong Kong", "🇭🇰", "HONG KONG"),
    "853": ("Macau", "🇲🇴", "MACAU"),
    "855": ("Cambodia", "🇰🇭", "CAMBODIA"),
    "856": ("Laos", "🇱🇦", "LAOS"),
    "960": ("Maldives", "🇲🇻", "MALDIVES"),
    "961": ("Lebanon", "🇱🇧", "LEBANON"),
    "962": ("Jordan", "🇯🇴", "JORDAN"),
    "963": ("Syria", "🇸🇾", "SYRIA"),
    "964": ("Iraq", "🇮🇶", "IRAQ"),
    "965": ("Kuwait", "🇰🇼", "KUWAIT"),
    "966": ("Saudi Arabia", "🇸🇦", "SAUDI ARABIA"),
    "967": ("Yemen", "🇾🇪", "YEMEN"),
    "968": ("Oman", "🇴🇲", "OMAN"),
    "970": ("Palestine", "🇵🇸", "PALESTINE"),
    "971": ("UAE", "🇦🇪", "UAE"),
    "972": ("Israel", "🇮🇱", "ISRAEL"),
    "973": ("Bahrain", "🇧🇭", "BAHRAIN"),
    "974": ("Qatar", "🇶🇦", "QATAR"),
    "975": ("Bhutan", "🇧🇹", "BHUTAN"),
    "976": ("Mongolia", "🇲🇳", "MONGOLIA"),
    "977": ("Nepal", "🇳🇵", "NEPAL"),
    "992": ("Tajikistan", "🇹🇯", "TAJIKISTAN"),
    "993": ("Turkmenistan", "🇹🇲", "TURKMENISTAN"),
    "994": ("Azerbaijan", "🇦🇿", "AZERBAIJAN"),
    "995": ("Georgia", "🇬🇪", "GEORGIA"),
    "996": ("Kyrgyzstan", "🇰🇬", "KYRGYZSTAN"),
    "998": ("Uzbekistan", "🇺🇿", "UZBEKISTAN"),
}

# ======================
# 🧠 إنشاء قاعدة البيانات (مع جداول جديدة)
# ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT UNIQUE,
            numbers TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            base_url TEXT,
            ajax_path TEXT,
            login_page TEXT,
            login_post TEXT,
            username TEXT,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER,
            country_code TEXT,
            numbers TEXT,
            PRIMARY KEY (user_id, country_code)
        )
    ''')
    # تهيئة الإعدادات الافتراضية
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_channel', '')")
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_enabled', '0')")
    conn.commit()
    conn.close()

init_db()

# ======================
# 🧰 دوال إدارة قاعدة البيانات (محدثة)
# ======================
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None):
    """
    يحفظ أو يحدّث بيانات المستخدم باستخدام استعلام واحد (INSERT OR REPLACE).
    هذا يمنع أخطاء التزامن (race conditions) في البيئات متعددة الخيوط.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # نحتاج إلى جلب البيانات القديمة التي لا نريد تغييرها إذا لم يتم توفيرها
    # هذا يمنع مسح البيانات القيمة مثل country_code عند استدعاء الدالة بمعلومات أساسية فقط
    existing_data = get_user(user_id)
    if existing_data:
        # إذا لم يتم توفير country_code جديد، استخدم القديم
        if country_code is None:
            country_code = existing_data[4]
        # إذا لم يتم توفير assigned_number جديد، استخدم القديم
        if assigned_number is None:
            assigned_number = existing_data[5]
        # إذا لم يتم توفير private_combo_country جديد، استخدم القديم
        if private_combo_country is None:
            private_combo_country = existing_data[7]

    c.execute("""
        REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), ?)
    """, (
        user_id,
        username,
        first_name,
        last_name,
        country_code,
        assigned_number,
        user_id, # يُستخدم في COALESCE لجلب حالة الحظر القديمة
        private_combo_country
    ))
    conn.commit()
    conn.close()


def ban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_combo(country_code, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        row = c.fetchone()
        if row:
            conn.close()
            return json.loads(row[0])
    c.execute("SELECT numbers FROM combos WHERE country_code=?", (country_code,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo(country_code, numbers, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)",
                  (user_id, country_code, json.dumps(numbers)))
    else:
        c.execute("REPLACE INTO combos (country_code, numbers) VALUES (?, ?)",
                  (country_code, json.dumps(numbers)))
    conn.commit()
    conn.close()

def delete_combo(country_code, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("DELETE FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
    else:
        c.execute("DELETE FROM combos WHERE country_code=?", (country_code,))
    conn.commit()
    conn.close()

def get_all_combos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code FROM combos")
    combos = [row[0] for row in c.fetchall()]
    conn.close()
    return combos

def assign_number_to_user(user_id, number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (number, user_id))
    conn.commit()
    conn.close()

def get_user_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE assigned_number=?", (number,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def log_otp(number, otp, full_message, assigned_to=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
    conn.commit()
    conn.close()

def release_number(old_number):
    if not old_number:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    conn.commit()
    conn.close()

def get_otp_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs")
    logs = c.fetchall()
    conn.close()
    return logs

def get_user_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# ======================
# 🔐 دوال الاشتراك الإجباري
# ======================
def force_sub_check(user_id):
    enabled = get_setting("force_sub_enabled") == "1"
    if not enabled:
        return True
    channel = get_setting("force_sub_channel")
    if not channel:
        return True
    try:
        if channel.startswith("https://t.me/"):
            channel = "@" + channel.split("/")[-1]
        member = bot.get_chat_member(channel, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def force_sub_markup():
    channel = get_setting("force_sub_channel")
    if not channel:
        return None
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 اشترك في القناة", url=channel))
    markup.add(types.InlineKeyboardButton("✅ تحقق", callback_data="check_sub"))
    return markup

# ======================
# 🤖 إنشاء بوت Telegram
# ======================
bot = telebot.TeleBot(BOT_TOKEN)

# ======================
# 🎮 وظائف البوت التفاعلي
# ======================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_total_users():
    """ترجع عدد المستخدمين الكلي"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count
    
#$#$#@
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 You are banned.")
        return

    full_name = message.from_user.first_name or "عزيزي"

    # 🔒 التحقق من الاشتراك الإجباري
    if not force_sub_check(message.from_user.id):
        markup = force_sub_markup()
        if markup:
            text = (
                "╔══💎 <b>𝐁𝐎𝐓 𝐀𝐋𝐁𝐑𝐀𝐍𝐒 𝐀𝐂𝐂𝐄𝐒𝐒</b> 💎══╗\n\n"
                f"🖤︙<b>أهلاً وسهلاً {full_name} 💫</b>\n\n"
                "🔒 لا يمكنك استخدام البوت قبل الاشتراك بالقنوات الرسمية 📢\n"
                "🚀 <b>اشترك الآن</b> ثم اضغط على الزر بالأسفل للتحقق ✅\n\n"
                "✨ نحن هنا لتقديم أفضل الخدمات لك!\n"
                "🤍 <b>شكراً لثقتك واستخدامك BOT ALBRANS 💎</b>\n"
                "╚════════════════════════╝"
            )
            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                "🔒 الاشتراك الإجباري مفعل لكن لم يتم تحديد قناة!"
            )
        return

    # 🟢 تحقق إذا كان مستخدم جديد
    is_new_user = not get_user(message.from_user.id)
    save_user(
        message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or ""
    )

    # 🟣 لو جديد، أرسل إشعار للأدمن
    if is_new_user:
        total_users = get_total_users()
        for admin in ADMIN_IDS:
            try:
                caption = (
                    f"🆕 <b>مستخدم جديد دخل البوت:</b>\n"
                    f"🆔<b> الأيدي:</b> <code>{message.from_user.id}</code>\n"
                    f"👤 <b>يوزر:</b>@{message.from_user.username or 'None'}\n"
                    f"👨‍💼 <b>الاسم: </b>{message.from_user.first_name or ''} {message.from_user.last_name or ''}\n"
                    f"👥 <b>عدد الأعضاء الكلي الآن:</b> {total_users}"
                )

                # لو عنده صورة بروفايل
                photos = bot.get_user_profile_photos(message.from_user.id).photos
                if photos:
                    bot.send_photo(admin, photos[0][-1].file_id, caption=caption, parse_mode="HTML")
                else:
                    bot.send_message(admin, caption, parse_mode="HTML")

            except Exception as e:
                print(f"[!] خطأ أثناء إرسال إشعار للأدمن: {e}")

    # 🟡 بناء لوحة الدول — صف واحد لكل زر (تحت بعض دائماً)
    markup = types.InlineKeyboardMarkup(row_width=1)
    user = get_user(message.from_user.id)
    private_combo = user[7] if user else None
    all_combos = get_all_combos()

    # إضافة الكومبو الخاص أولاً إن وجد
    if private_combo and private_combo in COUNTRY_CODES:
        name, flag, _ = COUNTRY_CODES[private_combo]
        markup.add(types.InlineKeyboardButton(f"{flag} {name} (Private)", callback_data=f"country_{private_combo}"))

    # إضافة باقي الكومبوهات العامة — زر واحد في كل سطر
    for code in all_combos:
        if code in COUNTRY_CODES and code != private_combo:
            name, flag, _ = COUNTRY_CODES[code]
            markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"country_{code}"))

    # زر الأدمن إن كان المستخدم أدمن
    if is_admin(message.from_user.id):
        admin_btn = types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")
        markup.add(admin_btn)

    bot.send_message(
        message.chat.id,
        "🌍 <b>Choose Your Country</b>👇",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if force_sub_check(call.from_user.id):
        try:
            # حذف رسالة الاشتراك بعد النجاح
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.answer_callback_query(call.id, "✅ تم الاشتراك بنجاح!", show_alert=True)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def handle_country_selection(call):
    if is_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 You are banned.", show_alert=True)
        return
    if not force_sub_check(call.from_user.id):
        markup = force_sub_markup()
        if markup:
            bot.send_message(call.message.chat.id, "🔒 يجب الاشتراك في القناة لاستخدام البوت.", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "🔒 الاشتراك الإجباري مفعل لكن لم يتم تحديد قناة!")
        return
    country_code = call.data.split("_", 1)[1]
    available_numbers = get_available_numbers(country_code, call.from_user.id)
    if not available_numbers:
        bot.edit_message_text("❌ جميع الأرقام قيد الاستخدام حاليًا.", call.message.chat.id, call.message.message_id)
        return
    assigned = random.choice(available_numbers)
    old_user = get_user(call.from_user.id)
    if old_user and old_user[5]:
        release_number(old_user[5])
    assign_number_to_user(call.from_user.id, assigned)
    save_user(call.from_user.id, country_code=country_code, assigned_number=assigned)
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    msg_text = f"""📱 <b>Number:</b> <code>{assigned}</code>
🌍 <b>Country:</b> {flag} {name}
⏳ <b>Waiting For OTP..</b>📱"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"change_num_{country_code}"))
    markup.add(types.InlineKeyboardButton("🌎 Change Country", callback_data="back_to_countries"))
    bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def change_number(call):
    if is_banned(call.from_user.id):
        return
    if not force_sub_check(call.from_user.id):
        return
    country_code = call.data.split("_", 2)[2]
    available_numbers = get_available_numbers(country_code, call.from_user.id)
    if not available_numbers:
        bot.answer_callback_query(call.id, "❌ جميع الأرقام قيد الاستخدام.", show_alert=True)
        return
    old_user = get_user(call.from_user.id)
    if old_user and old_user[5]:
        release_number(old_user[5])
    assigned = random.choice(available_numbers)
    assign_number_to_user(call.from_user.id, assigned)
    save_user(call.from_user.id, assigned_number=assigned)
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    msg_text = f"""📱 <b>Number:</b> <code>{assigned}</code>
🌍 <b>Country:</b> {flag} {name}
⏳ <b>Waiting For OTP..</b>📱"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"change_num_{country_code}"))
    markup.add(types.InlineKeyboardButton("🌎 Change Country", callback_data="back_to_countries"))
    bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    user = get_user(call.from_user.id)
    private_combo = user[7] if user else None
    all_combos = get_all_combos()

    if private_combo and private_combo in COUNTRY_CODES:
        name, flag, _ = COUNTRY_CODES[private_combo]
        buttons.append(types.InlineKeyboardButton(f"{flag} {name} (Private)", callback_data=f"country_{private_combo}"))

    for code in all_combos:
        if code in COUNTRY_CODES and code != private_combo:
            name, flag, _ = COUNTRY_CODES[code]
            buttons.append(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"country_{code}"))

    for button in buttons:
        markup.add(button)

    if is_admin(call.from_user.id):
        admin_btn = types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")
        markup.add(admin_btn)

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🌍 <b>Choose Your Country</b> 👇",
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[!] Error editing message: {e}")
        bot.answer_callback_query(call.id)


# ======================
# 🔐 لوحة التحكم الإدارية (محدثة)
# ======================
user_states = {}

def admin_main_menu():
    markup = types.InlineKeyboardMarkup()
    btns = [
        types.InlineKeyboardButton("📥 إضافة ارقام", callback_data="admin_add_combo"),
        types.InlineKeyboardButton("🗑️ حذف ارقام", callback_data="admin_del_combo"),
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 التقرير الكامل", callback_data="admin_full_report"),
        types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ إلغاء حظر مستخدم", callback_data="admin_unban"),
        types.InlineKeyboardButton("📢 بث إلى الجميع", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("📨 بث لمستخدم محدد", callback_data="admin_broadcast_user"),
        types.InlineKeyboardButton("👤 معلومات المستخدم", callback_data="admin_user_info"),
        types.InlineKeyboardButton("🔗 الاشتراك الإجباري", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("🖥️ لوحات الأرقام", callback_data="admin_dashboards"),
        types.InlineKeyboardButton("👤 كومبو خاص", callback_data="admin_private_combo"),
    ]
    for i in range(0, len(btns), 2):
        markup.row(*btns[i:i+2])
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if not is_admin(call.from_user.id):
        return
    bot.edit_message_text("🔐 Admin Panel", call.message.chat.id, call.message.message_id, reply_markup=admin_main_menu())

# ======================
# 📌 ميزة الاشتراك الإجباري في لوحة الإدارة
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_force_sub")
def admin_force_sub(call):
    if not is_admin(call.from_user.id):
        return
    enabled = get_setting("force_sub_enabled") == "1"
    channel = get_setting("force_sub_channel") or "غير محدد"
    status = "مفعل" if enabled else "معطل"
    text = f"⚙️ إعدادات الاشتراك الإجباري:\nالحالة: {status}\nالقناة: {channel}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعيين رابط القناة", callback_data="admin_set_force_sub_channel"))
    if enabled:
        markup.add(types.InlineKeyboardButton("❌ تعطيل", callback_data="admin_disable_force_sub"))
    else:
        markup.add(types.InlineKeyboardButton("✅ تفعيل", callback_data="admin_enable_force_sub"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_set_force_sub_channel")
def admin_set_force_sub_channel(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "set_force_sub_channel"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    bot.edit_message_text("أرسل رابط القناة (@ أو https://t.me/...):", call.message.chat.id, call.message.message_id, reply_markup=markup)
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "waiting_combo_file"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("📤 أرسل ملف الارقام بصيغة TXT", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(content_types=['document'])
def handle_combo_file(message):
    if not is_admin(message.from_user.id):
        return
    if user_states.get(message.from_user.id) != "waiting_combo_file":
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            bot.reply_to(message, "❌ الملف فارغ!")
            return

        # تحقق من أول 5 أرقام لتحديد الدولة
        country_code = None
        for line in lines[:5]:
            num = clean_number(line)
            for code in COUNTRY_CODES:
                if num.startswith(code):
                    country_code = code
                    break
            if country_code:
                break  # وجدنا الدولة، نوقف البحث

        if not country_code:
            bot.reply_to(message, "❌ لا يمكن تحديد الدولة من الأرقام!")
            return

        save_combo(country_code, lines)
        name, flag, _ = COUNTRY_CODES[country_code]
        bot.reply_to(message, f"✅ تم حفظ ارقام لدولة {flag} {name}\n🔢 عدد الأرقام: {len(lines)}")
        del user_states[message.from_user.id]

    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def admin_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    combos = get_all_combos()
    if not combos:
        bot.answer_callback_query(call.id, "لا توجد كومبوهات!")
        return
    markup = types.InlineKeyboardMarkup()
    for code in combos:
        if code in COUNTRY_CODES:
            name, flag, _ = COUNTRY_CODES[code]
            markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"del_combo_{code}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("اختر دوله للحذف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_combo_"))
def confirm_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    code = call.data.split("_", 2)[2]
    delete_combo(code)
    name, flag, _ = COUNTRY_CODES.get(code, ("Unknown", "🌍", ""))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(f"✅ تم حذف الارقام: {flag} {name}", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        return

    # 🧮 البيانات من قاعدة البوت
    total_users = len(get_all_users())
    combos = get_all_combos()
    total_numbers = sum(len(get_combo(c)) for c in combos)
    otp_count = len(get_otp_logs())

    # 📊 بيانات الرسائل من stats.json
    stats_file = "stats.json"
    if os.path.exists(stats_file):
        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
        total_msgs = stats.get("total", 0)
        today = date.today().strftime("%Y-%m-%d")
        daily_msgs = stats.get("daily", {}).get(today, 0)
    else:
        total_msgs = daily_msgs = 0

    # عدد الجروبات المراقبة
    groups_count = len(CHAT_IDS)

    # عدد المحظورين
    try:
        banned_users = get_banned_users()
        banned_count = len(banned_users)
    except:
        banned_count = 0

    # ⏰ الوقت الحالي
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ⌨️ الأزرار
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))

    # 💬 الرسالة النهائية
    text = (
        f"📊 <b>حالة البوت</b>\n\n"
        f"🔄 <b>المراقبة:</b> مفعّلة ✅\n"
        f"📅 <b>التاريخ الحالي:</b> {now}\n\n"
        f"📱 <b>عدد الرسائل اليوم:</b> {daily_msgs}\n"
        f"📊 <b>إجمالي الرسائل:</b> {total_msgs}\n"
        f"👥 <b>عدد المجموعات:</b> {groups_count}\n"
        f"🧑‍💻 <b>عدد مستخدمي البوت الكلي:</b> {total_users}\n"
        f"⛔ <b>عدد المحظورين:</b> {banned_count}\n\n"
        f"🌐 <b>الدول المضافة:</b> {len(combos)}\n"
        f"📞 <b>إجمالي الأرقام:</b> {total_numbers}\n"
        f"🔑 <b>إجمالي الأكواد المستلمة:</b> {otp_count}"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML"
    )
@bot.callback_query_handler(func=lambda call: call.data == "admin_full_report")
def admin_full_report(call):
    if not is_admin(call.from_user.id):
        return
    try:
        report = "📊 تقرير شامل عن البوت\n" + "="*40 + "\n\n"
        # المستخدمون
        report += "👥 المستخدمون:\n"
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        for u in users:
            status = "محظور" if u[6] else "نشط"
            report += f"ID: {u[0]} | @{u[1] or 'N/A'} | الرقم: {u[5] or 'N/A'} | الحالة: {status}\n"
        report += "\n" + "="*40 + "\n\n"
        # الأكواد
        report += "🔑 سجل الأكواد:\n"
        c.execute("SELECT * FROM otp_logs")
        logs = c.fetchall()
        for log in logs:
            user_info = get_user_info(log[5]) if log[5] else None
            user_tag = f"@{user_info[1]}" if user_info and user_info[1] else f"ID:{log[5] or 'N/A'}"
            report += f"الرقم: {log[1]} | الكود: {log[2]} | المستخدم: {user_tag} | الوقت: {log[4]}\n"
        conn.close()
        report += "\n" + "="*40 + "\n\n"
        report += "تم إنشاء التقرير في: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("bot_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        with open("bot_report.txt", "rb") as f:
            bot.send_document(call.from_user.id, f)
        os.remove("bot_report.txt")
        bot.answer_callback_query(call.id, "✅ تم إرسال التقرير!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "ban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لحظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "ban_user")
def admin_ban_step2(message):
    try:
        uid = int(message.text)
        ban_user(uid)
        bot.reply_to(message, f"✅ تم حظر المستخدم {uid}")
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "unban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم لفك حظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "unban_user")
def admin_unban_step2(message):
    try:
        uid = int(message.text)
        unban_user(uid)
        bot.reply_to(message, f"✅ تم فك حظر المستخدم {uid}")
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_all_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "broadcast_all"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أرسل الرسالة للإرسال للجميع:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_all")
def admin_broadcast_all_step2(message):
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            success += 1
        except:
            pass
    bot.reply_to(message, f"✅ تم الإرسال إلى {success}/{len(users)} مستخدم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_user")
def admin_broadcast_user_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "broadcast_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_user_id")
def admin_broadcast_user_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"broadcast_msg_{uid}"
        bot.reply_to(message, "أرسل الرسالة:")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and str(user_states[msg.from_user.id].get("state", "")).startswith("broadcast_msg_"))
def admin_broadcast_user_step3(message):
    uid = int(user_states[message.from_user.id].split("_")[2])
    try:
        bot.send_message(uid, message.text)
        bot.reply_to(message, f"✅ تم الإرسال للمستخدم {uid}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل: {e}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_info")
def admin_user_info_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "get_user_info"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "get_user_info")
def admin_user_info_step2(message):
    try:
        uid = int(message.text)
        user = get_user_info(uid)
        if not user:
            bot.reply_to(message, "❌ المستخدم غير موجود!")
            return
        status = "محظور" if user[6] else "نشط"
        info = f"👤 معلومات المستخدم:\n"
        info += f"🆔: {user[0]}\n"
        info += f".Username: @{user[1] or 'N/A'}\n"
        info += f"الاسم: {user[2] or ''} {user[3] or ''}\n"
        info += f"الرقم المخصص: {user[5] or 'N/A'}\n"
        info += f"الحالة: {status}"
        bot.reply_to(message, info)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")
    del user_states[message.from_user.id]
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "set_force_sub_channel")
def admin_set_force_sub_channel_step2(message):
    channel = message.text.strip()
    if not (channel.startswith("@") or channel.startswith("https://t.me/")):
        bot.reply_to(message, "❌ رابط غير صالح! يجب أن يبدأ بـ @ أو https://t.me/")
        return
    set_setting("force_sub_channel", channel)
    bot.reply_to(message, f"✅ تم تعيين القناة: {channel}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_enable_force_sub")
def admin_enable_force_sub(call):
    set_setting("force_sub_enabled", "1")
    bot.answer_callback_query(call.id, "✅ تم تفعيل الاشتراك الإجباري!", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_disable_force_sub")
def admin_disable_force_sub(call):
    set_setting("force_sub_enabled", "0")
    bot.answer_callback_query(call.id, "❌ تم تعطيل الاشتراك الإجباري!", show_alert=True)
    admin_force_sub(call)

# ======================
# 🖥️ ميزة لوحات الأرقام المتعددة
# ======================
# 🖥️ ميزة لوحات الأرقام المتعددة
# ======================

def get_dashboards():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM dashboards")
    rows = c.fetchall()
    conn.close()
    return rows


def save_dashboard(name, base_url, ajax_path, login_page, login_post, username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO dashboards (name, base_url, ajax_path, login_page, login_post, username, password)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, base_url, ajax_path, login_page, login_post, username, password))
    conn.commit()
    conn.close()


def delete_dashboard(dash_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM dashboards WHERE id=?", (dash_id,))
    conn.commit()
    conn.close()


# --- لوحة الإدارة ---
@bot.callback_query_handler(func=lambda call: call.data == "admin_dashboards")
def admin_dashboards(call):
    if not is_admin(call.from_user.id):
        return
    dashboards = get_dashboards()
    markup = types.InlineKeyboardMarkup()
    if dashboards:
        for d in dashboards:
            markup.add(types.InlineKeyboardButton(f"🖥️ {d[1]}", callback_data=f"view_dashboard_{d[0]}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة لوحة", callback_data="add_dashboard"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("🖥️ لوحات الأرقام:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- عرض لوحة ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("view_dashboard_"))
def view_dashboard(call):
    dash_id = int(call.data.split("_")[2])
    dashboards = get_dashboards()
    dash = next((d for d in dashboards if d[0] == dash_id), None)
    if not dash:
        bot.answer_callback_query(call.id, "❌ اللوحة غير موجودة!")
        return
    text = (
        f"🖥️ <b>{dash[1]}</b>\n"
        f"🌐 Base URL: {dash[2]}\n"
        f"👤 Username: {dash[6]}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"del_dashboard_{dash_id}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_dashboards"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")


# --- حذف لوحة ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("del_dashboard_"))
def del_dashboard(call):
    dash_id = int(call.data.split("_")[2])
    delete_dashboard(dash_id)
    bot.answer_callback_query(call.id, "✅ تم الحذف!", show_alert=True)
    admin_dashboards(call)


# --- إضافة لوحة جديدة ---
@bot.callback_query_handler(func=lambda call: call.data == "add_dashboard")
def add_dashboard_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = {"step": "name"}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_dashboards"))
    bot.edit_message_text(
        "✨ أدخل اسم اللوحة الجديد ✨",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# --- إدخال اسم اللوحة ---
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "name")
def add_dashboard_name(message):
    user_states[message.from_user.id]["name"] = message.text
    user_states[message.from_user.id]["step"] = "base"
    sent_msg = bot.reply_to(
        message,
        f"💠 اسم اللوحة: <b>{message.text}</b>\nالآن أدخل Base URL:",
        parse_mode="HTML"
    )
    user_states[message.from_user.id]["msg_id"] = [message.message_id, sent_msg.message_id]


# --- Base URL ---
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "base")
def add_dashboard_base(message):
    data = user_states[message.from_user.id]
    data["base"] = message.text
    data["step"] = "username"
    sent_msg = bot.reply_to(message, f"🌐 Base URL تم حفظه: <code>{message.text}</code>\nأدخل Username:", parse_mode="HTML")
    data["msg_id"].append(message.message_id)
    data["msg_id"].append(sent_msg.message_id)


# --- Username ---
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "username")
def add_dashboard_username(message):
    data = user_states[message.from_user.id]
    data["username"] = message.text
    data["step"] = "password"
    sent_msg = bot.reply_to(message, f"👤 Username تم حفظه: <b>{message.text}</b>\nأدخل Password:", parse_mode="HTML")
    data["msg_id"].append(message.message_id)
    data["msg_id"].append(sent_msg.message_id)


# --- Password ---
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "password")
def add_dashboard_password(message):
    data = user_states[message.from_user.id]
    password = message.text

    # القيم الثابتة
    AJAX_PATH = "/ints/agent/res/data_smscdr.php"
    LOGIN_PAGE_URL = data["base"] + "/ints/login"
    LOGIN_POST_URL = data["base"] + "/ints/signin"

    # حفظ في قاعدة البيانات
    save_dashboard(
        name=data["name"],
        base_url=data["base"],
        ajax_path=AJAX_PATH,
        login_page=LOGIN_PAGE_URL,
        login_post=LOGIN_POST_URL,
        username=data["username"],
        password=password
    )

    # حذف الرسائل القديمة
    for msg_id in data.get("msg_id", []):
        try:
            bot.delete_message(message.chat.id, msg_id)
        except Exception:
            pass

    # رسالة النجاح
    bot.reply_to(
        message,
        f"✅ تم إضافة اللوحة بنجاح 💎\n"
        f"💠 الاسم: <b>{data['name']}</b>\n"
        f"🌐 Base URL: <code>{data['base']}</code>",
        parse_mode="HTML"
    )

    del user_states[message.from_user.id]


# عند تشغيل البوت لأول مرة، شغّل هذه الدالة:
init_dashboards_table()

# ======================
# 👤 ميزة كومبو برايفت
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_private_combo")
def admin_private_combo(call):
    if not is_admin(call.from_user.id):
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة كومبو برايفت", callback_data="add_private_combo"))
    markup.add(types.InlineKeyboardButton("🗑️ مسح كومبو برايفت", callback_data="del_private_combo"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("👤 كومبو برايفت:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_private_combo")
def add_private_combo_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "add_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_private_user_id")
def add_private_combo_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"add_private_country_{uid}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for code in get_all_combos():
            if code in COUNTRY_CODES:
                name, flag, _ = COUNTRY_CODES[code]
                buttons.append(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"select_private_{uid}_{code}"))
        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
        bot.reply_to(message, "اختر الدولة:", reply_markup=markup)
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_private_"))
def select_private_combo(call):
    parts = call.data.split("_")
    uid = int(parts[2])
    country_code = parts[3]
    save_user(uid, private_combo_country=country_code)
    name, flag, _ = COUNTRY_CODES[country_code]
    bot.answer_callback_query(call.id, f"✅ تم تعيين كومبو برايفت لـ {uid} - {flag} {name}", show_alert=True)
    admin_private_combo(call)

@bot.callback_query_handler(func=lambda call: call.data == "del_private_combo")
def del_private_combo_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "del_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_private_combo"))
    bot.edit_message_text("أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "del_private_user_id")
def del_private_combo_step2(message):
    try:
        uid = int(message.text)
        save_user(uid, private_combo_country=None)
        bot.reply_to(message, f"✅ تم مسح الكومبو البرايفت للمستخدم {uid}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح!")
    del user_states[message.from_user.id]

# ======================
# 🆕 دالة جديدة: جلب الأرقام المتاحة (غير المستخدمة) مع دعم private
# ======================
def get_available_numbers(country_code, user_id=None):
    all_numbers = get_combo(country_code, user_id)
    if not all_numbers:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    used_numbers = set(row[0] for row in c.fetchall())
    conn.close()
    available = [num for num in all_numbers if num not in used_numbers]
    return available

# ======================
# 🔄 الدالة المعدلة لإرسال OTP للمستخدم + الجروب
# =========================
import re
import sqlite3
from datetime import datetime
from telebot import TeleBot

# ============================
# إعدادات البوت
# ============================

CHANNEL_IDS = ["-1003214839852"]  # جروبات أو قنوات المراقبة
sent_cache = set()  # لتجنب إرسال الكود أكثر من مرة

ADMIN_ID = 8038053114  # اختياري لإرسال نسخة من الأكواد
# =====

# ============================
# دوال مساعدة
# ============================
def extract_otp(text):
    match = re.search(r'\b(\d{4,8})\b', text)
    return match.group(1) if match else None

def find_masked_number(text):
    match = re.search(r'(\d{4})\D+(\d{4})', text)
    if match:
        return match.group(1), match.group(2)
    return None, None

def get_user_by_mask(first4, last4):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, assigned_number FROM users WHERE assigned_number LIKE ?",
        (f"%{last4}",)  # نركز على آخر 4 أرقام فقط
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None

def get_user_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE assigned_number=?", (number,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def log_otp(number, otp, full_message, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
        (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id)
    )
    conn.commit()
    conn.close()

def detect_service(text):
    match = re.search(r'Service[:\s]*(\w+)', text, re.IGNORECASE)
    return match.group(1) if match else "Unknown"

def html_escape(text):
    return html.escape(text)

# ============================
# إرسال OTP للمستخدم + الجروب
# ============================
def send_otp_to_user_and_group(date_str, number, sms):
    try:
        otp_code = extract_otp(sms)
        user_id = get_user_by_number(number)
        log_otp(number, otp_code, sms, user_id)

        # =========================
        # إرسال للمستخدم
        # =========================
        if user_id and otp_code:
            try:
                service = detect_service(sms)
                bot.send_message(
                    user_id,
                    f"<b>New OTP Received 🎉</b>\n\n"
                    f"☎️ <b>Number:</b> <code>{number}</code>\n"
                    f"🔑 <b>OTP:</b> <code>{otp_code}</code>\n"
                    f"💬 <b>Service:</b> {service}",
                    parse_mode="HTML"
                )
                print(f"[DEBUG] OTP sent to user {user_id}")
            except Exception as e:
                print(f"[!] Failed to send OTP to user {user_id}: {e}")

        # =========================
        # إرسال نسخة للجروب/القناة مؤقتة (ثانية واحدة ثم حذف)
        # =========================
        msg = format_message(date_str, number, sms)
        for group_id in CHANNEL_IDS:
            try:
                sent_msg = bot.send_message(group_id, msg, parse_mode="HTML")
                time.sleep(1)  # انتظر ثانية واحدة
                bot.delete_message(group_id, sent_msg.message_id)  # حذف الرسالة
            except Exception as e:
                print(f"[!] فشل إرسال/حذف الرسالة في الجروب {group_id}: {e}")

        # =========================
        # إرسال نسخة للأدمن
        # =========================
        if ADMIN_ID:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            admin_msg = (
                f"👤 المستخدم: {user_id}\n"
                f"☎️ الرقم: <code>{number}</code>\n"
                f"🔐 الكود: <code>{otp_code}</code>\n"
                f"💬 الخدمة: {detect_service(sms)}\n"
                f"⏱️ الوقت: {now}"
            )
            try:
                bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
            except Exception as e:
                print(f"[!] فشل إرسال الرسالة للأدمن: {e}")

    except Exception as e:
        print(f"[!] send_otp_to_user_and_group Error: {e}")
        import traceback
        traceback.print_exc()

# ============================
# مراقبة القناة / الجروب
# ============================
@bot.message_handler(func=lambda m: str(m.chat.id) in CHANNEL_IDS, content_types=['text'])
def handle_group_msg(message):
    try:
        text = message.text or ""
        print(f"[DEBUG] Received in monitored channel/group: {text}")

        otp_code = extract_otp(text)
        _, last4 = find_masked_number(text)

        if not last4:
            return

        user_id, full_number = get_user_by_mask(None, last4)
        if user_id:
            cache_key = f"{user_id}:{otp_code}"
            if cache_key not in sent_cache:
                sent_cache.add(cache_key)
                send_otp_to_user_and_group(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), full_number, text)

    except Exception as e:
        print(f"[!] Error in handle_group_msg: {e}")
        import traceback
        traceback.print_exc()

# ============================
# ======================
# 📡 دوال الاتصال بالـ Dashboard (كما هي من الملف الأصلي)
# ======================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE + "/ints/agent/SMSCDRReports",
    "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8"
})

def retry_request(func, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY):
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                print(f"⚠️  محاولة {attempt + 1}/{max_retries} فشلت: {type(e).__name__}")
                print(f"⏳ انتظار {retry_delay} ثانية قبل إعادة المحاولة...")
                time.sleep(retry_delay)
            else:
                print(f"❌ جميع المحاولات ({max_retries}) فشلت")
                raise
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            raise

def login():
    print("[*] محاولة تسجيل الدخول...")
    def do_login():
        try:
            resp = session.get(LOGIN_PAGE_URL, timeout=TIMEOUT)
            match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
            if not match:
                print("[!] لم يتم العثور على captcha في صفحة تسجيل الدخول")
                return False
            num1, num2 = int(match.group(1)), int(match.group(2))
            captcha_answer = num1 + num2
            print(f"[*] حل captcha: {num1} + {num2} = {captcha_answer}")
            payload = {
                "username": USERNAME,
                "password": PASSWORD,
                "capt": str(captcha_answer)
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": LOGIN_PAGE_URL,
                "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            print(f"[*] إرسال طلب تسجيل الدخول لـ: {USERNAME}")
            resp = session.post(LOGIN_POST_URL, data=payload, headers=headers, timeout=TIMEOUT, allow_redirects=True)
            print(f"[*] حالة الاستجابة: {resp.status_code}")
            if ("dashboard" in resp.text.lower() or 
                "logout" in resp.text.lower() or 
                "agent" in resp.url.lower() or
                "/ints/agent" in resp.url or
                resp.url != LOGIN_PAGE_URL):
                print("[+] تسجيل الدخول نجح ✅")
                return True
            else:
                print("[!] فشل تسجيل الدخول ❌")
                if "incorrect" in resp.text.lower() or "invalid" in resp.text.lower():
                    print("[!] اسم المستخدم أو كلمة المرور غير صحيحة")
                return False
        except Exception as e:
            print(f"[!] خطأ في تسجيل الدخول: {e}")
            raise
    try:
        return retry_request(do_login)
    except:
        return False

is_logged_in = False

def build_ajax_url(start_date=None, end_date=None, wide_range=False):
    if wide_range:
        start_date = date.today() - timedelta(days=3650)
        end_date = date.today() + timedelta(days=1)
    else:
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today() + timedelta(days=1)
    fdate1 = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    fdate2 = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
    q = (
        f"fdate1={quote_plus(fdate1)}&fdate2={quote_plus(fdate2)}&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth=&fgrange="
        f"&fgclient=&fgnumber=&fgcli=&fg=0&sEcho=1&iColumns=9&sColumns=%2C%2C%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=5000"
        f"&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&mDataProp_8=8"
        f"&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1&_={int(time.time()*1000)}"
    )
    return BASE + AJAX_PATH + "?" + q

def fetch_ajax_json(url):
    global is_logged_in
    def do_fetch():
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code == 403:
            raise Exception("Session expired")
        r.raise_for_status()
        try:
            data = r.json()
            if not isinstance(data, (dict, list)):
                raise Exception("Invalid JSON response")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            if "login" in r.text.lower() and r.url and "login" in r.url.lower():
                raise Exception("Session expired")
            raise
    try:
        return retry_request(do_fetch, max_retries=2, retry_delay=3)
    except Exception as e:
        if "Session expired" in str(e):
            print("[!] انتهت صلاحية الجلسة. إعادة تسجيل الدخول...")
            is_logged_in = False
            if login():
                is_logged_in = True
                try:
                    return retry_request(do_fetch, max_retries=2, retry_delay=3)
                except:
                    return None
            else:
                return None
        print("[!] خطأ في جلب/تحليل AJAX:", e)
        return None

def extract_rows_from_json(j):
    if j is None:
        return []
    for key in ("data", "aaData", "rows", "aa_data"):
        if isinstance(j, dict) and key in j:
            return j[key]
    if isinstance(j, list):
        return j
    if isinstance(j, dict):
        for v in j.values():
            if isinstance(v, list):
                return v
    return []

def clean_html(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    return text

def clean_number(number):
    if not number:
        return ""
    number = re.sub(r'\D', '', str(number))
    return number

def row_to_tuple(row):
    date_str = ""
    number_str = ""
    sms_str = ""
    if isinstance(row, (list, tuple)):
        if len(row) > IDX_DATE:
            date_str = clean_html(row[IDX_DATE])
        if len(row) > IDX_NUMBER:
            number_str = clean_number(row[IDX_NUMBER])
        if len(row) > IDX_SMS:
            sms_str = clean_html(row[IDX_SMS])
    elif isinstance(row, dict):
        for k in ("date","time","datetime","dt","created_at"):
            if k in row and not date_str:
                date_str = clean_html(row[k])
        for k in ("number","msisdn","cli","from","sender"):
            if k in row and not number_str:
                number_str = clean_number(row[k])
        for k in ("sms","message","msg","body","text"):
            if k in row and not sms_str:
                sms_str = clean_html(row[k])
        if not sms_str:
            vals = list(row.values())
            if len(vals) > IDX_SMS:
                sms_str = clean_html(vals[IDX_SMS])
            elif vals:
                sms_str = clean_html(vals[-1])
    unique_key = f"{date_str}|{number_str}|{sms_str}"
    return date_str, number_str, sms_str, unique_key

def get_country_info(number):
    number = number.strip().replace("+", "").replace(" ", "").replace("-", "")
    for code, (name, flag, upper_name) in COUNTRY_CODES.items():
        if number.startswith(code):
            return name, flag, upper_name
    return "Unknown", "🌍", "UNKNOWN"

def mask_number(number: str) -> str:
    """
    إخفاء الرقم بحيث يظهر أول 4 أرقام وآخر 4 أرقام، 
    ويُستبدل ما بينهما بـ '•••'.
    مثال: 201183737 → 2011•••8373
    """
    number = number.strip()
    if len(number) <= 8:
        return number
    return number[:4] + "•••" + number[-4:]


def extract_otp(message):
    patterns = [
        r'(?:code|رمز|كود|verification|تحقق|otp|pin)[:\s]+[‎]?(\d{3,8}(?:[- ]\d{3,4})?)',
        r'(\d{3})[- ](\d{3,4})',
        r'\b(\d{4,8})\b',
        r'[‎](\d{3,8})',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            if len(match.groups()) > 1:
                return ''.join(match.groups())
            return match.group(1).replace(' ', '').replace('-', '')
    all_numbers = re.findall(r'\d{4,8}', message)
    if all_numbers:
        return all_numbers[0]
    return "N/A"

def detect_service(message):
    message_lower = message.lower()
    services = {
        "whatsapp": ["whatsapp", "واتساب", "واتس", "whats"],
        "facebook": ["facebook", "فيسبوك", "fb", "meta"],
        "instagram": ["instagram", "انستقرام", "انستا", "insta"],
        "telegram": ["telegram", "تيليجرام", "تلجرام"],
        "twitter": ["twitter", "تويتر", "x.com", "twitter/x"],
        "tiktok": ["tiktok", "تيك توك"],
        "snapchat": ["snapchat", "سناب شات", "snap"],
        "google": ["google", "جوجل", "gmail", "g-"],
        "uber": ["uber", "اوبر"],
        "careem": ["careem", "كريم"],
        "linkedin": ["linkedin", "لينكد ان", "لينكدان"],
        "youtube": ["youtube", "يوتيوب"],
        "netflix": ["netflix", "نتفليكس"],
        "amazon": ["amazon", "امازون"],
        "paypal": ["paypal", "باي بال"],
        "microsoft": ["microsoft", "مايكروسوفت", "outlook", "hotmail"],
        "apple": ["apple", "ابل", "icloud", "app store"],
        "discord": ["discord", "ديسكورد"],
        "reddit": ["reddit", "ريديت"],
        "pinterest": ["pinterest", "بينترست"],
        "twitch": ["twitch", "تويتش"],
        "spotify": ["spotify", "سبوتيفاي"],
        "viber": ["viber", "فايبر"],
        "wechat": ["wechat", "وي شات"],
        "line": ["line"],
        "signal": ["signal", "سيجنال"],
        "skype": ["skype", "سكايب"],
        "zoom": ["zoom", "زوم"],
        "teams": ["teams", "تيمز"],
        "steam": ["steam", "ستيم"],
        "ebay": ["ebay", "ايباي"],
        "alibaba": ["alibaba", "علي بابا"],
        "airbnb": ["airbnb", "اير بي ان بي"],
        "booking": ["booking", "بوكينج"],
        "shopify": ["shopify", "شوبيفاي"],
        "dropbox": ["dropbox", "دروب بوكس"],
        "onedrive": ["onedrive", "وان درايف"],
        "binance": ["binance", "بينانس"],
        "coinbase": ["coinbase", "كوين بيز"],
        "payoneer": ["payoneer", "بايونير"],
        "stripe": ["stripe", "سترايب"],
        "venmo": ["venmo", "فينمو"],
        "cashapp": ["cash app", "كاش اب"],
        "revolut": ["revolut", "ريفولوت"],
        "transferwise": ["wise", "transferwise", "وايز"],
        "tinder": ["tinder", "تيندر"],
        "bumble": ["bumble", "بامبل"],
        "yahoo": ["yahoo", "ياهو"],
        "bing": ["bing", "بينج"],
        "duckduckgo": ["duckduckgo"],
        "vk": ["vk", "vkontakte"],
        "ok": ["ok.ru", "odnoklassniki"],
        "yandex": ["yandex", "ياندكس"],
        "mailru": ["mail.ru"],
        "baidu": ["baidu", "بايدو"],
        "weibo": ["weibo", "ويبو"],
        "qq": ["qq"],
    }
    for service, keywords in services.items():
        for keyword in keywords:
            if keyword in message_lower:
                return service.upper()
    return "GENERAL"

def send_to_telegram_group(text):
    """
    إرسال الرسائل إلى المجموعات بدون أزرار.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    success_count = 0

    for chat_id in CHAT_IDS:
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            resp = requests.post(url, data=payload, timeout=10)
            if resp.status_code != 200:
                print(f"[!] فشل إرسال Telegram إلى {chat_id}: {resp.status_code}")
            else:
                print(f"[+] تم إرسال الرسالة إلى: {chat_id}")
                success_count += 1
        except Exception as e:
            print(f"[!] خطأ Telegram لـ {chat_id}: {e}")

    return success_count > 0

def html_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "<")
            .replace(">", ">")
            .replace('"', "&quot;"))

def format_message(date_str, number, sms):
    country_name, country_flag, country_upper = get_country_info(number)
    masked_num = mask_number(number)
    otp_code = extract_otp(sms)
    service = detect_service(sms)

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        formatted_time = date_str

    if otp_code != "N/A":
        otp_display = html_escape(otp_code)
    else:
        otp_display = "N/A"

    sms_escaped = html_escape(sms)

    # 🟢 نفس المتغيرات القديمة + التنسيق الجديد
    message = f"""▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
▌ <b>New</b> {country_flag} <b>{country_name} {service}</b> ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟
╔═•◈•══════════════•◈•═╗
║📱 <b>Number:</b> <code>{masked_num}</code>
║🔒 <b>Code:</b> <code>{otp_display}</code>
║🌍 <b>Country:</b> {country_flag} <b>{country_name}</b>
║⚙️ <b>Service:</b> <b>{service}</b>
║🕒 <b>Time:</b> <code>{formatted_time}</code>
║💌 <b>Full Message:</b>
╚═•◈•══════════════•◈•═╝
<pre>{sms_escaped}</pre>
•◈•══════════════════•◈•"""
    
    return message
# ======================
@bot.message_handler(commands=["groupadd"])
def add_group(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر مخصص للإدارة فقط.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ استخدم الأمر بهذا الشكل:\n`/groupadd -100xxxxxxxxx`", parse_mode="Markdown")
        return

    group_id = parts[1].strip()
    if group_id in CHAT_IDS:
        bot.reply_to(message, "✅ المجموعة موجودة بالفعل في قائمة التحويل.")
        return

    CHAT_IDS.append(group_id)
    save_chat_ids(CHAT_IDS)
    bot.reply_to(message, f"✅ تمت إضافة المجموعة {group_id} بنجاح!")


@bot.message_handler(commands=["groupdel"])
def delete_group(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر مخصص للإدارة فقط.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ استخدم الأمر بهذا الشكل:\n`/groupdel -100xxxxxxxxx`", parse_mode="Markdown")
        return

    group_id = parts[1].strip()
    if group_id not in CHAT_IDS:
        bot.reply_to(message, "❌ هذه المجموعة غير موجودة.")
        return

    CHAT_IDS.remove(group_id)
    save_chat_ids(CHAT_IDS)
    bot.reply_to(message, f"🗑️ تم حذف المجموعة {group_id} من قائمة التحويل.")


@bot.message_handler(commands=["groups"])
def list_groups(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر مخصص للإدارة فقط.")
        return

    if not CHAT_IDS:
        bot.reply_to(message, "📭 لا توجد مجموعات حالياً.")
        return

    text = "📋 <b>قائمة مجموعات التحويل الحالية:</b>\n\n"
    for i, g in enumerate(CHAT_IDS, start=1):
        text += f"{i}. <code>{g}</code>\n"
    bot.reply_to(message, text, parse_mode="HTML")
# 🔄 الحلقة الرئيسية (معدلة لدعم لوحات متعددة)
@bot.message_handler(commands=['admin'])
def admin_help(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر مخصص للإدارة فقط.")
        return

    text = (  
        "🤖 <b>بوت مراقبة OTP - نظام الإدارة</b>\n\n"  
        "الأوامر المتاحة:\n"  
        "🔹 /groupadd - إضافة مجموعة جديدة للتحويل\n"  
        "🔹 /groupdel - حذف مجموعة من التحويل\n"  
        "🔹 /groups - عرض جميع المجموعات الحالية\n"  
        "\n🛠️ المطور:<b> <a href='https://t.me/Albrans_01'>عمو البرنس</a> </b>"  
    )  

    bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)
# ======================
ERROR_LOG_FILE = "bot_errors.log"

# ======================================
# دالة تسجيل الأخطاء في ملف
def log_error(e):
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {str(e)}\n")
        f.write(traceback.format_exc())
        f.write("\n\n")

# ======================================

@bot.message_handler(commands=['id'])
def send_my_info(message):
    send_user_info(message.chat.id, message.from_user.id)

def send_user_info(chat_id, user_id):
    try:
        user = bot.get_chat(user_id)
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "❌ لا يوجد"
        bio = user.bio if hasattr(user, 'bio') and user.bio else "❌ لا يوجد"

        # نص فخم للعرض
        fancy_text = (
            "🌟━━━━━━━━━━━━━━━━🌟\n"
            f"👤 <b>الاسم:</b> {name}\n"
            f"🔗 <b>اسم المستخدم:</b> {username}\n"
            f"📝 <b>البايو:</b> {bio}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            "🌟━━━━━━━━━━━━━━━━🌟"
        )

        # محاولة إرسال صورة البروفايل إذا موجودة
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos and photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(chat_id, file_id, caption=fancy_text, parse_mode="HTML")
        else:
            bot.send_message(chat_id, fancy_text, parse_mode="HTML")

    except Exception as e:
        bot.send_message(chat_id, "❌ لا يمكن الوصول لهذا الحساب.")
# ======================================
# ======================================


# لتخزين حالة المستخدم
user_states = {}

# ===== أمر /help =====
@bot.message_handler(commands=['help'])
def help_command(message):
    chat_id = message.chat.id

    # زر تفاعلي فخم للتواصل مع المطور
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✉️✨ تواصل مع المطوّر ✨✉️", callback_data="contact_dev"))

    # نص الرسالة الفخم
    fancy_text_lines = [
        "🌟━━━━━━━━━━━━━━━━🌟",
        "💡 مرحبًا بك في قسم المساعدة! 💡",
        "📩 يمكنك التواصل مع المطوّر مباشرة من هنا:",
        "🛠️ أرسل استفسارك أو سؤالك وسيصلك الرد قريبًا.",
        "💎 شكراً لتواصلك معنا.",
        "🌟━━━━━━━━━━━━━━━━🌟"
    ]

    # إرسال رسالة فارغة أولية
    sent_msg = bot.send_message(chat_id, "⏳...", reply_markup=markup, parse_mode="HTML")

    # تأثير الكتابة السريع جدًا
    def animate_typing():
        typed_text = ""
        for line in fancy_text_lines:
            typed_text += line + "\n"
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=sent_msg.message_id,
                                  text=typed_text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            pass

    threading.Thread(target=animate_typing).start()


# زر الاتصال بالمطور
@bot.callback_query_handler(func=lambda call: call.data == "contact_dev")
def callback_contact_dev(call):
    chat_id = call.message.chat.id

    # رسالة الاتصال الأولية
    loading_msg = bot.send_message(chat_id, "⏳ <b>يتم الاتصال بالمطور</b>", parse_mode="HTML")
    user_states[call.from_user.id] = {"state": "contact_dev", "msg_id": loading_msg.message_id}

    # تأثير الكتابة السريع والوميض الفخم
    def fancy_loading():
        flashes = ["✨", "💫", "⚡", "🌟"]
        for f in flashes:
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=loading_msg.message_id,
                                      text=f"⏳ <b>تم الاتصال بالمطور</b> {f}", parse_mode="HTML")
            except Exception:
                pass
            time.sleep(0.05)

        # الرسالة النهائية الفخمة
        final_text_lines = [
            "✨━━━━━━━━━━━━━━━━✨",
            "💥 <b>تم الاتصال بالمطور بنجاح!</b> 💥",
            "📨 يمكنك الآن إرسال رسالتك مباشرة.",
            "🛠️ المطور سيطلع عليها قريبًا.",
            "💎 شكراً لتواصلك معنا.",
            "✨━━━━━━━━━━━━━━━━✨"
        ]

        # دمج النصوص في رسالة واحدة فورية
        final_text = "\n".join(final_text_lines)
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=loading_msg.message_id,
                                  text=final_text, parse_mode="HTML")
        except Exception:
            pass

    threading.Thread(target=fancy_loading).start()


# استقبال رسالة المستخدم وتحويلها للأدمن وحذف الرسالة السابقة
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "contact_dev")
def forward_to_admin(message):
    data = user_states.get(message.from_user.id)
    msg_id = data.get("msg_id")
    chat_id = message.chat.id

    # حذف رسالة الاتصال السابقة
    try:
        bot.delete_message(chat_id, msg_id)
    except Exception:
        pass

    # إرسال الرسالة للأدمن فورًا
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(
                admin_id,
                f"📨 <b>رسالة من المستخدم</b>:\n"
                f"👤 {message.from_user.first_name} (@{message.from_user.username})\n"
                f"🆔 {message.from_user.id}\n\n"
                f"💬 {message.text}",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[!] خطأ في إرسال الرسالة للأدمن {admin_id}: {e}")

    # إزالة حالة المستخدم
    del user_states[message.from_user.id]
 # ======================================

# --- قائمة الأدعية ---


import threading
import time
import random

# 🕌 قائمة الأدعية
duas = [
    "اللّهُ لا إلهَ إلاّ هو الحيّ القيّوم 🌟",
    "رَبّنا آتنا في الدنيا حسنة وفي الآخرة حسنة وقنا عذاب النار 💫",
    "اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ 📖",
    "وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ 🌹",
    "اللّهُ نُورُ السَّمَاوَاتِ وَالأَرْضِ ✨",
    "رَبِّ زِدْنِي عِلْمًا 📚",
    "فَاذْكُرُونِي أَذْكُرْكُمْ 🕊️",
    "وَعِبَادُ الرَّحْمَنِ الَّذِينَ يَمْشُونَ عَلَى الْأَرْضِ هَوْنًا 🌿",
    "وَقُل رَّبِّ زِدْنِي عِلْمًا 💎",
    "فَصْلِهَا فِي لَيْلَةٍ مُبَارَكَة 🌙",
    "إِنَّمَا الْمُؤْمِنُونَ إِخْوَةٌ 🕊️",
    "وَاللَّهُ غَفُورٌ رَّحِيمٌ 🌹",
    "رَبِّ اغْفِرْ وَارْحَمْ وَأَنتَ خَيْرُ الرَّاحِمِينَ 💖",
    "قُل هُوَ اللَّهُ أَحَدٌ 🕋",
    "اللّهُ أَكْبَرُ، لا إِلَهَ إِلَّا هُوَ 🔔",
    "رَبِّ اجْعَلْنِي مُقِيمَ الصَّلَاةِ 💫",
    "فَإِذَا قَرَأْتَ الْقُرْآنَ فَاسْتَمِعْ لَهُ وَأَنْصِتْ 💎",
    "وَلَا تَيْأَسُوا مِن رَّوْحِ اللَّهِ 🌟",
    "اللّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَآلِهِ 🕊️",
    "رَبِّ اجْعَلْنِي مِنَ الْمُتَّقِينَ 🌹",
    # 21
    "اللّهُمَّ اجعل القرآن ربيع قلبي ونور صدري وجلاء حزني 🌟",
    "وَمَنْ يَتَّقِ اللَّهَ يَجْعَل لَهُ مَخْرَجًا 💫",
    "اللّهُمَّ اهْدِنِي وَسَدِّدْنِي ✨",
    "رَبِّ اجْعَلْنِي لَكَ شَكَّارًا صَبَّارًا 🌿",
    "فَصْبِرْ صَبْرًا جَمِيلًا 💎",
    "وَقُل رَّبِّ زِدْنِي عِلْمًا 📚",
    "اللّهُمَّ طَهِّرْ قَلْبِي وَنَقِّيهِ 🕊️",
    "اللّهُمَّ اجعل أعمالنا خالصة لوجهك الكريم 💖",
    "اللّهُمَّ اجعلنا من عبادك الصالحين 🌟",
    "رَبِّ اجعلنا من الذين يستمعون القول فيتبعون أحسنه 🌙",
    # 31
    "اللّهُمَّ اجعلنا من الفائزين بالجنة 🌸",
    "اللّهُمَّ اجعلنا من الذين لا خوف عليهم ولا هم يحزنون 🌿",
    "رَبِّ اجعلني من الذين يصلون ويذكرونك دائمًا 💫",
    "اللّهُمَّ اجعل القرآن لنا شفيعًا يوم القيامة 📖",
    "وَاللَّهُ وَاسِعٌ عَلِيمٌ 💎",
    "اللّهُمَّ اجعل قلبي عامرًا بذكرك 🌹",
    "اللّهُمَّ اجعلنا من الذين يستغفرونك دائمًا 🕊️",
    "رَبِّ اجعلنا من الموفقين في حياتنا 💖",
    "اللّهُمَّ اجعلنا من عبادك الشاكرين 🌟",
    "اللّهُمَّ اجعلنا من الذين يرضون بقضائك 💫",
    # 41
    "رَبِّ اجعلنا من الذين يذكرونك في السر والعلن ✨",
    "اللّهُمَّ اجعلنا من الذين ينظرون إلى الخير 🌿",
    "اللّهُمَّ اجعلنا من الذين يصلون في أوقاتها 💎",
    "اللّهُمَّ اجعلنا من الذين يبتسمون للخلق 🌸",
    "اللّهُمَّ اجعلنا من الذين يرحمون الصغار ويوقرون الكبار 🕊️",
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للناس 🌹",
    "رَبِّ اجعلنا من الذين ينالون رضاك 💖",
    "اللّهُمَّ اجعلنا من الذين لا يغترون بالدنيا 🌟",
    "اللّهُمَّ اجعلنا من الذين يذكرونك دائمًا 💫",
    "رَبِّ اجعلنا من الذين يبتعدون عن المعاصي 🌿",
    # 51
    "اللّهُمَّ اجعلنا من الذين يحسنون الظن بالآخرين ✨",
    "اللّهُمَّ اجعلنا من الذين يتعلمون العلم النافع 📚",
    "رَبِّ اجعلنا من الذين يصلون على النبي ﷺ دائمًا 🕊️",
    "اللّهُمَّ اجعلنا من الذين يبتسمون ويصفحون 🌸",
    "اللّهُمَّ اجعلنا من الذين يتقونك في السر والعلن 💖",
    "اللّهُمَّ اجعلنا من الذين يزرعون المحبة والسلام 🌹",
    "رَبِّ اجعلنا من الذين ينصرون الضعفاء 🌟",
    "اللّهُمَّ اجعلنا من الذين يغفرون للناس 💫",
    "اللّهُمَّ اجعلنا من الذين يكثرون الذكر والعبادة 🌿",
    "رَبِّ اجعلنا من الذين يخلصون في القول والعمل 💎",
    # 61
    "اللّهُمَّ اجعلنا من الذين يصلحون بين الناس 🕊️",
    "اللّهُمَّ اجعلنا من الذين يسعون للخير 🌸",
    "رَبِّ اجعلنا من الذين يحبون النبي ﷺ 💖",
    "اللّهُمَّ اجعلنا من الذين يرضون بقضائك 🌟",
    "اللّهُمَّ اجعلنا من الذين يستعينون بك دائمًا 💫",
    "اللّهُمَّ اجعلنا من الذين يشكرون نعمك 🌿",
    "رَبِّ اجعلنا من الذين يتفكرون في خلقك 💎",
    "اللّهُمَّ اجعلنا من الذين يتواضعون 🌹",
    "اللّهُمَّ اجعلنا من الذين يتذكرون الموت دائمًا 🕊️",
    "رَبِّ اجعلنا من الذين يصلحون قلوبهم 🌟",
    # 71
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للخلق 💖",
    "اللّهُمَّ اجعلنا من الذين يرضون بما قسمته لهم 🌸",
    "رَبِّ اجعلنا من الذين يستغفرونك في الليل والنهار 💫",
    "اللّهُمَّ اجعلنا من الذين يبتعدون عن المعاصي 🌿",
    "اللّهُمَّ اجعلنا من الذين يحسنون الأدب مع الجميع ✨",
    "رَبِّ اجعلنا من الذين يذكرونك في كل لحظة 📚",
    "اللّهُمَّ اجعلنا من الذين يحبون العلم والعمل 💎",
    "اللّهُمَّ اجعلنا من الذين يسعدون قلوب الناس 🌹",
    "رَبِّ اجعلنا من الذين يطمئنون بذكرك 🕊️",
    "اللّهُمَّ اجعلنا من الذين يسعون للسلام 🌟",
    # 81
    "اللّهُمَّ اجعلنا من الذين يحبون العدل 💫",
    "رَبِّ اجعلنا من الذين يبتعدون عن الحقد والبغضاء 🌸",
    "اللّهُمَّ اجعلنا من الذين يذكرونك في كل حال 💖",
    "اللّهُمَّ اجعلنا من الذين يزرعون الخير دائمًا 🌿",
    "رَبِّ اجعلنا من الذين يتقونك في السر والعلن ✨",
    "اللّهُمَّ اجعلنا من الذين يطيعون أوامرك 💎",
    "اللّهُمَّ اجعلنا من الذين يبتسمون ويصفحون 💫",
    "رَبِّ اجعلنا من الذين يخلصون في القول والعمل 🌟",
    "اللّهُمَّ اجعلنا من الذين يصلحون بين الناس 🌹",
    "رَبِّ اجعلنا من الذين يغفرون للناس 🕊️",
    # 91
    "اللّهُمَّ اجعلنا من الذين يحبون النبي ﷺ 🌸",
    "اللّهُمَّ اجعلنا من الذين يذكرونك دائمًا 💖",
    "رَبِّ اجعلنا من الذين يكثرون الدعاء 🌿",
    "اللّهُمَّ اجعلنا من الذين يكثرون الصلاة على النبي ﷺ 🌟",
    "رَبِّ اجعلنا من الذين يبتعدون عن كل شر 💫",
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للآخرين ✨",
    "رَبِّ اجعلنا من الذين يرزقون الصبر 🌹",
    "اللّهُمَّ اجعلنا من الذين يرضون بما كتبت لهم 💎",
    "رَبِّ اجعلنا من الذين يستمعون القول فيتبعون أحسنه 💖",
    "اللّهُمَّ اجعلنا من الذين يصلون في أوقاتها 🌸",
    # 101
    "رَبِّ اجعلنا من الذين يحسنون الظن بالآخرين 🌿",
    "اللّهُمَّ اجعلنا من الذين يحبون العمل الصالح 🌟",
    "رَبِّ اجعلنا من الذين ينالون رضاك 💫",
    "اللّهُمَّ اجعلنا من الذين يستغفرونك دائمًا 💎",
    "رَبِّ اجعلنا من الذين يصلحون قلوبهم 🕊️",
    "اللّهُمَّ اجعلنا من الذين يسعون للخير 🌸",
    "رَبِّ اجعلنا من الذين يحبون العلم والعمل 💖",
    "اللّهُمَّ اجعلنا من الذين يرضون بقضائك 🌿",
    "رَبِّ اجعلنا من الذين يبتعدون عن المعاصي 🌟",
    "اللّهُمَّ اجعلنا من الذين يذكرونك دائمًا 💫",
    # 111
    "رَبِّ اجعلنا من الذين يغفرون للناس 🌹",
    "اللّهُمَّ اجعلنا من الذين يحبون العدل 🌿",
    "رَبِّ اجعلنا من الذين يبتسمون ويصفحون 💖",
    "اللّهُمَّ اجعلنا من الذين يزرعون السلام 🌸",
    "رَبِّ اجعلنا من الذين يحبون الخير للخلق 🌟",
    "اللّهُمَّ اجعلنا من الذين يرضون بما قسمته لهم 💫",
    "رَبِّ اجعلنا من الذين يستغفرونك دائمًا 💎",
    "اللّهُمَّ اجعلنا من الذين يبتعدون عن الشر 🌿",
    "رَبِّ اجعلنا من الذين يتقونك في السر والعلن ✨",
    "اللّهُمَّ اجعلنا من الذين يحبون النبي ﷺ 🌸",
    # 121
    "رَبِّ اجعلنا من الذين يصلون على النبي ﷺ دائمًا 💖",
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للآخرين 🌟",
    "رَبِّ اجعلنا من الذين يبتسمون ويصفحون 💫",
    "اللّهُمَّ اجعلنا من الذين يتواضعون 🌿",
    "رَبِّ اجعلنا من الذين يذكرونك دائمًا 💎",
    "اللّهُمَّ اجعلنا من الذين يكثرون الدعاء 🌸",
    "رَبِّ اجعلنا من الذين يستمعون القول فيتبعون أحسنه 🌟",
    "اللّهُمَّ اجعلنا من الذين يصلحون بين الناس 💫",
    "رَبِّ اجعلنا من الذين يغفرون للناس 💖",
    "اللّهُمَّ اجعلنا من الذين يبتعدون عن المعاصي 🌿",
    # 131
    "رَبِّ اجعلنا من الذين يحبون العلم والعمل 🌟",
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للخلق 💎",
    "رَبِّ اجعلنا من الذين يرضون بقضائك 🌸",
    "اللّهُمَّ اجعلنا من الذين يبتسمون ويصفحون 💖",
    "رَبِّ اجعلنا من الذين يصلحون قلوبهم 🌿",
    "اللّهُمَّ اجعلنا من الذين يتقونك في السر والعلن 🌟",
    "رَبِّ اجعلنا من الذين يستغفرونك دائمًا 💫",
    "اللّهُمَّ اجعلنا من الذين يحبون النبي ﷺ 🌸",
    "رَبِّ اجعلنا من الذين يكثرون الصلاة على النبي ﷺ 💖",
    "اللّهُمَّ اجعلنا من الذين يحبون السلام 💎",
    # 141
    "رَبِّ اجعلنا من الذين يحبون الخير للآخرين 🌟",
    "اللّهُمَّ اجعلنا من الذين يحبون العلم والعمل 💫",
    "رَبِّ اجعلنا من الذين يبتعدون عن كل شر 🌸",
    "اللّهُمَّ اجعلنا من الذين يستمعون القول فيتبعون أحسنه 💖",
    "رَبِّ اجعلنا من الذين يكثرون الدعاء 🌿",
    "اللّهُمَّ اجعلنا من الذين يرضون بقضائك 🌟",
    "رَبِّ اجعلنا من الذين يصلحون بين الناس 💫",
    "اللّهُمَّ اجعلنا من الذين يغفرون للناس 💖",
    "رَبِّ اجعلنا من الذين يحبون العدل 🌸",
    "اللّهُمَّ اجعلنا من الذين يبتسمون ويصفحون 🌿",
    # 151
    "رَبِّ اجعلنا من الذين يزرعون الخير دائمًا 💎",
    "اللّهُمَّ اجعلنا من الذين يحبون النبي ﷺ 🌟",
    "رَبِّ اجعلنا من الذين يكثرون الصلاة على النبي ﷺ 💫",
    "اللّهُمَّ اجعلنا من الذين يحبون السلام 🌸",
    "رَبِّ اجعلنا من الذين يحبون الخير للخلق 💖",
    "اللّهُمَّ اجعلنا من الذين يبتعدون عن الشر 🌿",
    "رَبِّ اجعلنا من الذين يتقونك في السر والعلن 🌟",
    "اللّهُمَّ اجعلنا من الذين يحبون العلم والعمل 💫",
    "رَبِّ اجعلنا من الذين يحبون الخير للآخرين 🌸",
    "اللّهُمَّ اجعلنا من الذين يرضون بقضائك 💖",
    # 161
    "رَبِّ اجعلنا من الذين يستغفرونك دائمًا 🌿",
    "اللّهُمَّ اجعلنا من الذين يبتسمون ويصفحون 🌟",
    "رَبِّ اجعلنا من الذين يصلحون بين الناس 💫",
    "اللّهُمَّ اجعلنا من الذين يغفرون للناس 💖",
    "رَبِّ اجعلنا من الذين يحبون النبي ﷺ 🌸",
    "اللّهُمَّ اجعلنا من الذين يكثرون الصلاة على النبي ﷺ 🌿",
    "رَبِّ اجعلنا من الذين يحبون السلام 🌟",
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للخلق 💫",
    "رَبِّ اجعلنا من الذين يبتعدون عن الشر 🌸",
    "اللّهُمَّ اجعلنا من الذين يتقونك دائمًا 💖",
    # 171
    "رَبِّ اجعلنا من الذين يحبون العلم والعمل 🌿",
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للآخرين 🌟",
    "رَبِّ اجعلنا من الذين يرضون بقضائك 💫",
    "اللّهُمَّ اجعلنا من الذين يبتسمون ويصفحون 🌸",
    "رَبِّ اجعلنا من الذين يصلحون قلوبهم 💖",
    "اللّهُمَّ اجعلنا من الذين يستغفرونك دائمًا 🌿",
    "رَبِّ اجعلنا من الذين يحبون النبي ﷺ 🌟",
    "اللّهُمَّ اجعلنا من الذين يكثرون الصلاة على النبي ﷺ 💫",
    "رَبِّ اجعلنا من الذين يحبون السلام 🌸",
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للخلق 💖",
    # 181
    "رَبِّ اجعلنا من الذين يبتعدون عن الشر 🌿",
    "اللّهُمَّ اجعلنا من الذين يتقونك في السر والعلن 🌟",
    "رَبِّ اجعلنا من الذين يحبون العلم والعمل 💫",
    "اللّهُمَّ اجعلنا من الذين يحبون الخير للآخرين 🌸",
    "رَبِّ اجعلنا من الذين يرضون بقضائك 💖",
    "اللّهُمَّ اجعلنا من الذين يستغفرونك دائمًا 🌿",
    "رَبِّ اجعلنا من الذين يحبون النبي ﷺ 🌟",
    "اللّهُمَّ اجعلنا من الذين يكثرون الصلاة على النبي ﷺ 💫",
    "رَبِّ اجعلنا من الذين يحبون السلام 🌸",
    "أصبحنا واصبح الملك لله لا تنسو اذكار الصباح", 
    " لا إله الا الله وحده لا شريك له له الملك وله الحمد وهو على كل شيء قدير",
    "اذكرونا بدعوة 🙏🏼",
]

# 🕋 ضع هنا ID الجروبات اللي البوت فيها مشرف
GROUP_CHAT_IDS = [
    "-1002805778712",  # مثال: اكتب هنا ID الجروب
    # تقدر تضيف أكثر من جروب
]

# 💫 دالة إرسال الدعاء كل ساعة
def send_hourly_dua():
    while True:
        try:
            dua = random.choice(duas)
            for chat_id in GROUP_CHAT_IDS:
                try:
                    bot.send_message(chat_id, dua, parse_mode="HTML")
                    print(f"[+] تم إرسال دعاء إلى الجروب {chat_id}")
                except Exception as e:
                    print(f"[!] خطأ أثناء الإرسال للجروب {chat_id}: {e}")
        except Exception as e:
            print(f"[!] خطأ عام في send_hourly_dua: {e}")

        time.sleep(60 * 60)  # كل ساعة

# 🚀 تشغيل الدالة في خيط مستقل
threading.Thread(target=send_hourly_dua, daemon=True).start()
# ======================================
# تشغيل البوت في حلقة لا نهائية
def run_bot():
    print("[*] Starting private bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"[!] Bot polling error: {e}")
            log_error(e)
            time.sleep(RETRY_DELAY)

# ======================================
# main_loop بنفس شكل كودك الحالي تماماً
def main_loop():
    global is_logged_in
    sent_messages = set()
    last_message_time = None

    print("=" * 60)
    print("🚀 Numbers Bot بدأ العمل")
    print("=" * 60)

    login_success = login()
    if not login_success:
        print("\n⚠️  تحذير: فشل تسجيل الدخول")
        print("⚠️  البوت سيستمر في العمل ولكن قد تحدث مشاكل")
        print("⚠️  للإصلاح: أضف SITE_USERNAME و SITE_PASSWORD في Secrets")
    else:
        is_logged_in = True

    print("\n🔍 جلب آخر رسالة موجودة (من أي تاريخ)...")
    try:
        url = build_ajax_url(wide_range=True)
        j = fetch_ajax_json(url)
        rows = extract_rows_from_json(j)
        if rows:
            valid_rows = []
            for row in rows:
                if isinstance(row, list) and len(row) > IDX_SMS:
                    date_val = clean_html(row[IDX_DATE])
                    number_val = clean_number(row[IDX_NUMBER])
                    sms_val = clean_html(row[IDX_SMS]) if row[IDX_SMS] else ""
                    if (date_val and '-' in date_val and ':' in date_val and
                        number_val and len(number_val) >= 10 and
                        sms_val and len(sms_val) > 5):
                        valid_rows.append(row)
            if valid_rows:
                def get_datetime(row):
                    try:
                        date_str = clean_html(row[IDX_DATE])
                        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        return datetime.min
                valid_rows.sort(key=get_datetime, reverse=True)
                latest_row = valid_rows[0]
                date_str, number, sms, key = row_to_tuple(latest_row)
                print(f"✅ تم العثور على آخر رسالة: {date_str} - الرقم: {mask_number(number)}")
                print("📤 إرسال آخر رسالة للجروب...")
                send_otp_to_user_and_group(date_str, number, sms)
                print(f"✅ تم إرسال آخر رسالة بنجاح")
                print(f"   الرقم: {mask_number(number)}")
                print(f"   الوقت: {date_str}")
                last_message_time = date_str
                sent_messages.add(key)
                print("📌 البوت الآن سيراقب وينتظر الرسائل الجديدة فقط\n")
    except Exception as e:
        print(f"⚠️  خطأ في جلب الرسالة الأولية: {e}")
        log_error(e)

    print(f"✅ بدء المراقبة كل {REFRESH_INTERVAL} ثانية...")
    print("=" * 60 + "\n")

    consecutive_errors = 0
    max_consecutive_errors = 5

    while True:
        try:
            url = build_ajax_url(wide_range=True)
            j = fetch_ajax_json(url)
            rows = extract_rows_from_json(j)
            if not rows:
                print("[=] لا توجد بيانات متاحة")
                consecutive_errors = 0
            else:
                valid_rows = []
                for row in rows:
                    if isinstance(row, list) and len(row) > IDX_SMS:
                        date_val = clean_html(row[IDX_DATE])
                        number_val = clean_number(row[IDX_NUMBER])
                        sms_val = clean_html(row[IDX_SMS]) if row[IDX_SMS] else ""
                        if (date_val and '-' in date_val and ':' in date_val and
                            number_val and len(number_val) >= 10 and
                            sms_val and len(sms_val) > 5):
                            valid_rows.append(row)
                if not valid_rows:
                    print("[=] لا توجد رسائل جديدة")
                    consecutive_errors = 0
                else:
                    def get_datetime(row):
                        try:
                            date_str = clean_html(row[IDX_DATE])
                            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            return datetime.min
                    valid_rows.sort(key=get_datetime, reverse=True)
                    current_latest_row = valid_rows[0]
                    date_str, number, sms, key = row_to_tuple(current_latest_row)
                    if last_message_time is None or date_str > last_message_time:
                        if key not in sent_messages:
                            send_otp_to_user_and_group(date_str, number, sms)
                            print(f"✅ تم إرسال رسالة جديدة")
                            print(f"   الرقم: {mask_number(number)}")
                            sent_messages.add(key)
                            last_message_time = date_str
                            consecutive_errors = 0
                            time.sleep(3)
                        else:
                            print("[=] لا توجد رسائل جديدة")
                            consecutive_errors = 0
                    else:
                        print("[=] لا توجد رسائل جديدة")
                        consecutive_errors = 0
                    if len(sent_messages) > 500:
                        sent_messages = set(list(sent_messages)[-500:])
        except KeyboardInterrupt:
            print("\n⛔ تم إيقاف البوت بواسطة المستخدم")
            break
        except Exception as e:
            consecutive_errors += 1
            print(f"❌ خطأ في الحلقة الرئيسية ({consecutive_errors}/{max_consecutive_errors}): {e}")
            log_error(e)
            if consecutive_errors >= max_consecutive_errors:
                print(f"\n⛔ تم تجاوز الحد الأقصى للأخطاء المتتالية ({max_consecutive_errors})")
                print("⚠️ إعادة تشغيل main_loop بعد فترة قصيرة...")
                time.sleep(RETRY_DELAY)
                consecutive_errors = 0
        time.sleep(REFRESH_INTERVAL)

# ======================
# تشغيل البوت في Thread منفصل + main_loop
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()  # غير daemon لضمان استمرار البوت
    main_loop()
import os
import re
import time
import json
import random
import html
import logging
import requests
import html as html_lib
import threading
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, date

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8438435636:AAFLsC9aoP6xABrgHJy-elXlw1wCZ4OCsLk"
ADMIN_ID = int(os.getenv("ADMIN_ID") or 8038053114)
CHANNEL_ID = -1003214839852
CHAT_IDS = []

# ======== MULTI-ACCOUNT CONFIG ========
ACCOUNTS = [
    {
        "name": "acc1",
        "username": "Ammm00",
        "password": "Ammm00",
        "api_url": "https://d-group.stats.direct/rest/sms"
    },
    {
        "name": "acc2",
        "username": "Albrans",
        "password": "Albrans00",
        "api_url": "https://d-group.stats.direct/rest/sms"
    }
]
# ======================================

POLL_INTERVAL = 3
PER_PAGE = 100
FORCE_RESEND_ON_START = True
REPLY_MAPPING = {}

REQUIRED_CHANNELS = ["@AlBrAnS_OtP", "@OTP_GROUP_ALBRANS"]

GARBLED_PATTERNS = ["CH/", "H'*3'", "#(/'"]

# ================== logging ==================
logging.basicConfig(level=logging.INFO, format=" %(message)s")
logger = logging.getLogger("master_bot")
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("telebot").setLevel(logging.CRITICAL)

# ================== bot & session ==================
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible)"})

# ================== أدوات التخزين ==================
def load_json(filename, default=None):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================== ملفات التخزين ==================
USERS_FILE = "bot_users.json"
USER_FILE = "user_numbers.json"
SENT_MESSAGES_FILE = "sent_messages.json"
COUNTRIES_FILE = "countries.json"
COUNTRY_VISIBILITY_FILE = "country_visibility.json"
NUMBERS_DIR = "numbers"
os.makedirs(NUMBERS_DIR, exist_ok=True)

# ================== تتبع المستخدمين ==================
def load_users():
    return load_json(USERS_FILE, {})

def save_bot_users(users):
    save_json(USERS_FILE, users)

def track_user_and_notify_admin(m):
    users = load_users()
    user_id = str(m.from_user.id)
    if user_id not in users:
        users[user_id] = {
            "first_name": m.from_user.first_name or "",
            "last_name": m.from_user.last_name or "",
            "username": m.from_user.username or ""
        }
        save_bot_users(users)
        total_users = len(users)
        full_name = f"{m.from_user.first_name} {m.from_user.last_name}" if m.from_user.last_name else m.from_user.first_name
        username = f"@{m.from_user.username}" if m.from_user.username else "لا يوجد"
        try:
            bot.send_message(
                ADMIN_ID,
                f"👤 دخل مستخدم جديد للبوت!\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"👤 الاسم: {full_name}\n"
                f"🔹 اليوزر: {username}\n"
                f"📊 العدد الكلي للمستخدمين: {total_users}",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[ERROR] Failed to notify admin: {e}")

# ================== أدوات عامة ==================
def mask_number(number: str) -> str:
    if len(number) <= 7:
        return number
    mid = (len(number) - 4) // 2
    return number[:mid] + "•••" + number[-4:]

def html_escape(v):
    try:
        return html_lib.escape(str(v))
    except Exception:
        return html_lib.escape(repr(v))

# ================== الآيات القرآنية ==================
QURAN_AYAT = [
    "📖إِنَّ مَعَ الْعُسْرِ يُسْرًا — *Verily, with hardship comes ease.* (94:6)",
    "📖اللَّهُ نُورُ السَّمَاوَاتِ وَالْأَرْضِ — *Allah is the Light of the heavens and the earth.* (24:35)",
    "📖فَاذْكُرُونِي أَذْكُرْكُمْ — *So remember Me; I will remember you.* (2:152)",
    "📖وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ — *And He is over all things.* (5:120)",
    "📖حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ — *Allah is sufficient for us, and He is the best disposer.* (3:173)"
]

# ================== الدول ==================
DEFAULT_COUNTRIES = {
    "EG": "🇪🇬 Egypt",
    "YE": "🇾🇪 Yemen",
    "IL": "🇮🇱 Israel",
    "IR": "🇮🇷 Iran",
    "RU": "🇷🇺 Russia",
    "SA": "🇸🇦 Saudi Arabia",
    "AF": "🇦🇫 Afghanistan",
    "US": "🇺🇸 United States",
    "NE": "🇳🇵 Nepal",
    "TA": "🇹🇿 Tanzania",
    "WU": "🇰🇼 Kuwait",
    "GB": "🇬🇧 United Kingdom",
    "IT": "🇺🇿 Uzbekistan",
    "IN": "🇰🇬 Kyrgyzstan",
    "BR": "🇲🇷 Mauritania",
    "BA": "🇧🇩 Bangladesh"
}

COUNTRIES = load_json(COUNTRIES_FILE, DEFAULT_COUNTRIES)
save_json(COUNTRIES_FILE, COUNTRIES)

COUNTRY_VISIBILITY = load_json(COUNTRY_VISIBILITY_FILE, {code: True for code in COUNTRIES})
save_json(COUNTRY_VISIBILITY_FILE, COUNTRY_VISIBILITY)

# ================== إدارة الدول ==================
@bot.callback_query_handler(func=lambda call: call.data == "manage_countries")
def callback_manage_countries(call):
    markup = InlineKeyboardMarkup(row_width=2)
    for code, name in COUNTRIES.items():
        visible = COUNTRY_VISIBILITY.get(code, True)
        status = "✅ ظاهرة" if visible else "🚫 مخفية"
        markup.add(InlineKeyboardButton(f"{name} {status}", callback_data=f"toggle_country_{code}"))
    markup.add(InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_admin"))
    bot.edit_message_text("🌍 إدارة ظهور الدول:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_country_"))
def callback_toggle_country(call):
    try:
        code = call.data.split("_")[-1]
        COUNTRY_VISIBILITY[code] = not COUNTRY_VISIBILITY.get(code, True)
        save_json(COUNTRY_VISIBILITY_FILE, COUNTRY_VISIBILITY)
        bot.answer_callback_query(call.id, "✅ تم التحديث")
        callback_manage_countries(call)
    except Exception as e:
        bot.answer_callback_query(call.id, f"⚠️ خطأ: {e}")

# ================== لوحة التحكم ==================
@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 هذا الأمر مخصص للمشرف فقط.")
        return
    show_admin_panel(message.chat.id)

def show_admin_panel(chat_id, message_id=None):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📤 رفع الأرقام", callback_data="choose_country_upload"),
        InlineKeyboardButton("🗑️ حذف الأرقام", callback_data="choose_country_delete")
    )
    markup.add(
        InlineKeyboardButton("🌍 إدارة الدول", callback_data="manage_countries"),
        InlineKeyboardButton("➕ إضافة دولة جديدة", callback_data="add_new_country")
    )
    text = "🛠️ لوحة التحكم:"
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
def callback_back_to_admin(call):
    show_admin_panel(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "↩️ تم الرجوع إلى لوحة التحكم")

# ================== رفع / حذف الأرقام ==================
@bot.callback_query_handler(func=lambda call: call.data in ["choose_country_upload", "choose_country_delete"])
def choose_country_action(call):
    action = "upload" if call.data == "choose_country_upload" else "delete"
    markup = InlineKeyboardMarkup(row_width=2)
    for code, name in COUNTRIES.items():
        if COUNTRY_VISIBILITY.get(code, True):
            markup.add(InlineKeyboardButton(name, callback_data=f"{action}_{code}"))
    markup.add(InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_admin"))
    text = "📤 اختر الدولة لرفع الأرقام:" if action == "upload" else "🗑️ اختر الدولة لحذف الأرقام:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(("upload_", "delete_")))
def handle_country_file_action(call):
    try:
        action, code = call.data.split("_", 1)
        country_name = COUNTRIES.get(code, "غير معروف")
        if action == "upload":
            bot.send_message(call.message.chat.id, f"📤 أرسل الآن ملف أرقام الدولة {country_name} (txt فقط)")
            bot.register_next_step_handler(call.message, lambda msg: receive_numbers_file(msg, code))
        else:
            path = os.path.join(NUMBERS_DIR, f"{code}.txt")
            if os.path.exists(path):
                os.remove(path)
                bot.send_message(call.message.chat.id, f"🗑️ تم حذف أرقام {country_name} بنجاح ✅")
            else:
                bot.send_message(call.message.chat.id, f"⚠️ لا يوجد ملف أرقام لـ {country_name}.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء تنفيذ العملية:\n{e}")

def receive_numbers_file(message, code):
    if not message.document:
        bot.reply_to(message, "❌ من فضلك أرسل ملف نصي بصيغة txt فقط.")
        return
    if not message.document.file_name.lower().endswith(".txt"):
        bot.reply_to(message, "⚠️ الملف يجب أن يكون بصيغة txt فقط.")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        path = os.path.join(NUMBERS_DIR, f"{code}.txt")
        with open(path, "wb") as f:
            f.write(downloaded_file)
        country_name = COUNTRIES.get(code, code)
        bot.send_message(message.chat.id, f"✅ تم رفع أرقام {country_name} بنجاح!")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء حفظ الملف:\n{e}")

# ================== تحميل الذاكرة ==================
SENT_MESSAGES_MEMORY = load_json(SENT_MESSAGES_FILE, [])
save_json(SENT_MESSAGES_FILE, SENT_MESSAGES_MEMORY)
#$#$
def progress_bar(percent: int, width: int = 12) -> str:
    """🔹 شريط تقدم أنيق ومضغوط"""
    percent = max(0, min(100, int(percent)))
    filled = int((percent / 100) * width)
    empty = width - filled
    bar = "▰" * filled + "▱" * empty
    return f"[{bar}] {percent:>3d}%"


def run_loading_effect_for_chat(chat_id: int, found_result: bool = True, text="🚀 جاري المعالجة..."):
    """
    ⚡ تأثير تحميل فخم وسريع جدًا:
      - يتحرك كل 5%
      - مدته الإجمالية أقل من ثانية
      - مؤثرات أنيقة وسريعة
    """
    try:
        stages = [
            "⚙️ معالجة البيانات...",
            "📡 الاتصال بالخوادم...",
            "🔍 فحص النتائج...",
            "✅ اكتمال العملية!"
        ]

        delay = 0.01 if found_result else 0.02  # 🔥 سرعة عالية جدًا
        msg = bot.send_message(chat_id, f"{text}\n{progress_bar(0)}")
        message_id = msg.message_id

        total_stages = len(stages)
        step_per_stage = 100 // (total_stages - 1)

        for i, stage in enumerate(stages):
            start = i * step_per_stage
            end = 100 if i == total_stages - 1 else (i + 1) * step_per_stage

            for p in range(start, end + 1, 5):  # ← كل 5٪ فقط
                animated = random.choice(["⚙️", "💫", "🔄", "⚡", "🚀"])
                bar = progress_bar(p)
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"{animated} <b>{stage}</b>\n\n{bar}",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                time.sleep(delay)

        # 🎯 النص النهائي (فخم ومباشر)
        final_text = (
            f"🎉 <b>تم التحقق بنجاح!</b>\n\n{progress_bar(100)}"
            if found_result else
            f"📭 <b>لم يتم العثور على نتائج.</b>\n\n{progress_bar(100)}"
        )

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=final_text,
            parse_mode="HTML"
        )

        # حذف سريع بعد لحظة
        time.sleep(0.2)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"[ERROR in run_loading_effect_for_chat]: {e}")
        return False
# ========== JSON helpers (shared files) ==========
def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Failed to load %s: %s", path, e)
    return default

def save_json(path, obj):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Failed to save %s: %s", path, e)

def load_config():
    return load_json("config.json", {"monitoring_active": True, "last_check_date": str(date.today())})

def save_config(cfg):
    save_json("config.json", cfg)

def load_groups():
    data = load_json("groups.json", [])
    s = set()
    for g in data:
        try:
            s.add(int(g))
        except Exception:
            s.add(g)
    # if empty, fallback to default CHAT_IDS if provided
    if not s and CHAT_IDS:
        for c in CHAT_IDS:
            try:
                s.add(int(c))
            except Exception:
                s.add(c)
    return s

def save_groups(groups):
    save_json("groups.json", list(groups))

def load_stats():
    return load_json("stats.json", {"today_sms_count": 0, "last_date": str(date.today()), "total_sms_sent": 0})

def save_stats(stats):
    save_json("stats.json", stats)

def load_already_sent(acc_name):
    return set(load_json(f"already_sent_{acc_name}.json", []))

def save_already_sent(acc_name, s):
    save_json(f"already_sent_{acc_name}.json", list(s))

def load_last_id(acc_name):
    p = f"last_id_{acc_name}.txt"
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except:
            return None
    return None

def save_last_id(acc_name, val):
    p = f"last_id_{acc_name}.txt"
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(str(val))
    except Exception as e:
        logger.error("Error saving last_id (%s): %s", acc_name, e)

# ========== banned users handling ==========
def load_bans():
    return set(load_json("banned_users.json", []))

def save_bans(bans_set):
    save_json("banned_users.json", list(bans_set))
    
def check_admin(user_id):
    return user_id == ADMIN_ID
    
def is_banned(user_id):
    try:
        bans = load_bans()
        return int(user_id) in bans
    except Exception:
        return False
#$#$

# 📦 تحميل بيانات المستخدمين
# ==========================
if os.path.exists(USER_FILE):
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            user_numbers = json.load(f)
    except json.JSONDecodeError:
        user_numbers = {}
else:
    user_numbers = {}

# ==========================
# 💾 حفظ بيانات المستخدمين
# ==========================
def save_user_numbers(data=None):
    if data is None:
        data = user_numbers
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================
# 🔢 جلب رقم عشوائي من الدول
# ➕ إضافة دولة جديدة
@bot.callback_query_handler(func=lambda call: call.data == "add_new_country")
def callback_add_new_country(call):
    msg = bot.send_message(call.message.chat.id, "🌍 أرسل رمز الدولة (مثلاً: EG):")
    bot.register_next_step_handler(msg, receive_country_code)


def receive_country_code(message):
    code = message.text.strip().upper()
    if len(code) > 3 or not code.isalpha():
        bot.reply_to(message, "⚠️ رمز الدولة غير صالح، يجب أن يكون مثل EG أو SA.")
        return
    msg = bot.send_message(message.chat.id, "📛 الآن أرسل اسم الدولة مع العلم (مثلاً: 🇪🇬 Egypt):")
    bot.register_next_step_handler(msg, lambda m: save_new_country(m, code))


def save_new_country(message, code):
    name = message.text.strip()
    if not name:
        bot.reply_to(message, "⚠️ لم يتم إدخال اسم الدولة.")
        return

    # ✅ حفظها في القاموس العام
    COUNTRIES[code] = name
    COUNTRY_VISIBILITY[code] = True

    # 💾 حفظ في ملفات JSON
    with open("countries.json", "w", encoding="utf-8") as f:
        json.dump(COUNTRIES, f, ensure_ascii=False, indent=2)

    save_json("country_visibility.json", COUNTRY_VISIBILITY)

    # 🎛️ بعد الحفظ، نعرض زر الرجوع
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅️ رجوع إلى لوحة التحكم", callback_data="back_to_admin"))

    bot.send_message(
        message.chat.id,
        f"✅ تم إضافة الدولة بنجاح:\n\n{code} → {name}",
        reply_markup=markup
    )
    
# ==========================
def get_random_number(code):
    """إرجاع رقم عشوائي من ملف الدولة"""
    file_path = os.path.join(NUMBERS_DIR, f"{code}.txt")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        numbers = [line.strip() for line in f if line.strip()]
    if not numbers:
        return None
    return random.choice(numbers)

# ==========================
# 🧹 حذف الرقم من ملف الدولة
# ==========================
def remove_number_from_file(code, number):
    file_path = os.path.join(NUMBERS_DIR, f"{code}.txt")
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        numbers = [line.strip() for line in f if line.strip()]
    numbers = [n for n in numbers if n != number]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(numbers))

def html_escape(text):
    return html.escape(str(text))
#$$
# ========== decoding and helpers ==========
def basic_auth_header(username, password):
    if not username:
        return {}
    import base64
    combo = f"{username}:{password}"
    b64 = base64.b64encode(combo.encode()).decode()
    return {"Authorization": f"Basic {b64}"}

def decode_short_message(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw)
    s = s.replace('\\u0006', '').replace('\\x06', '').replace('\x06', '')
    s = s.replace('\\u0000', '').replace('\\x00', '').replace('\x00', '')
    try:
        s = s.encode('utf-8').decode('unicode_escape')
    except:
        pass
    s = ''.join(ch for ch in s if ch.isprintable())
    return s.strip()

def detect_country_and_flag(number: str):
    num = re.sub(r"\D", "", number or "")
    
    if num.startswith("20"):
        return "Egypt", "🇪🇬"
    if num.startswith("977"):
        return "Nepal", "🇳🇵"
    if num.startswith("93"):
        return "Afghanistan", "🇦🇫"
    if num.startswith("7"):
        return "Russia", "🇷🇺"
    if num.startswith("967"):
        return "Yemen", "🇾🇪"
    if num.startswith("98"):
        return "Iran", "🇮🇷"
    if num.startswith("972"):
        return "Israel", "🇮🇱"
    if num.startswith("1"):
        return "USA/Canada", "🇺🇸"
    if num.startswith("44"):
        return "United Kingdom", "🇬🇧"
    if num.startswith("91"):
        return "India", "🇮🇳"
    if num.startswith("966"):
        return "Saudi Arabia", "🇸🇦"
    if num.startswith("971"):
        return "United Arab Emirates", "🇦🇪"
    if num.startswith("964"):
        return "Iraq", "🇮🇶"
    if num.startswith("218"):
        return "Libya", "🇱🇾"
    if num.startswith("249"):
        return "Sudan", "🇸🇩"
    if num.startswith("212"):
        return "Morocco", "🇲🇦"
    if num.startswith("213"):
        return "Algeria", "🇩🇿"
    if num.startswith("962"):
        return "Jordan", "🇯🇴"
    if num.startswith("961"):
        return "Lebanon", "🇱🇧"
    if num.startswith("970"):
        return "Palestine", "🇵🇸"
    if num.startswith("92"):
        return "Pakistan", "🇵🇰"
    if num.startswith("880"):
        return "Bangladesh", "🇧🇩"
    if num.startswith("998"):
        return "Uzbekistan", "🇺🇿"
    if num.startswith("996"):
        return "Kyrgyzstan", "🇰🇬"
    if num.startswith("55"):
        return "Brazil", "🇧🇷"
    if num.startswith("49"):
        return "Germany", "🇩🇪"
    if num.startswith("39"):
        return "Italy", "🇮🇹"
    if num.startswith("81"):
        return "Japan", "🇯🇵"
    if num.startswith("86"):
        return "China", "🇨🇳"
    if num.startswith("62"):
        return "Indonesia", "🇮🇩"
    if num.startswith("63"):
        return "Philippines", "🇵🇭"
    if num.startswith("60"):
        return "Malaysia", "🇲🇾"
    if num.startswith("94"):
        return "Sri Lanka", "🇱🇰"
    if num.startswith("27"):
        return "South Africa", "🇿🇦"

    return "International", "🌐"


def extract_otp(message: str):
    if not message:
        return None
    # نبحث عن أي أرقام متتالية من 3 إلى 8 أرقام أو 3-3 أرقام
    m = re.search(r'\d{3}-\d{3}|\d{4,8}', message)
    if not m:
        return None
    # نحذف أي شرطات لتصبح الأرقام متصلة
    return m.group().replace("-", "")

def is_garbled(message: str):
    if not message:
        return False
    for p in GARBLED_PATTERNS:
        if p in message:
            return True
    return False

# ========== fetching ==========
def fetch_sms(api_url, username=None, password=None, last_id=None, page=1, per_page=PER_PAGE, retries=3, timeout=15):
    params = {"page": page, "per-page": per_page}
    if last_id:
        params["id"] = last_id
    headers = basic_auth_header(username, password)
    attempt = 0
    while attempt < retries:
        try:
            resp = session.get(api_url, headers=headers, params=params, timeout=timeout)
            if resp.status_code == 200:
                try:
                    return resp.json(), resp.headers
                except Exception:
                    return None, resp.headers
        except Exception:
            pass
        attempt += 1
        time.sleep(2 ** attempt)
    return None, {}

# ========== monitor logic (synchronous) ==========
def process_account_once(acc: dict, force_resend=False):
    acc_name = acc.get("name", "default")
    already_sent = load_already_sent(acc_name)
    last_id = None if force_resend else load_last_id(acc_name)

    data, headers = fetch_sms(
        api_url=acc.get("api_url"),
        username=acc.get("username"),
        password=acc.get("password"),
        last_id=last_id,
        page=1,
        per_page=PER_PAGE
    )
    if data is None:
        return False

    # normalize
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            items = data["data"]
        elif "items" in data and isinstance(data["items"], list):
            items = data["items"]
        else:
            items = [data]
    else:
        return False

    if not force_resend and last_id is not None:
        try:
            items = [it for it in items if int(it.get("id", 0)) > int(last_id)]
        except Exception:
            pass

    try:
        items_sorted = sorted(items, key=lambda x: int(x.get("id", 0)))
    except Exception:
        items_sorted = items

    sent_any = False
    groups = load_groups()
    sent_numbers_in_cycle = set()  # لتجنب إرسال أكثر من مرة لكل رقم في هذه الدورة

    for row in items_sorted:
        msg_id = str(row.get("id", "") or row.get("ref", ""))
        if not msg_id:
            continue

        date_str = str(row.get("start_stamp") or row.get("date") or "")
        service = str(row.get("source_addr") or row.get("source") or "")
        number = str(row.get("destination_addr") or row.get("destination") or "")
        raw_msg = row.get("short_message") or row.get("short_message_hex") or row.get("message") or ""
        message = decode_short_message(raw_msg)

        country_guess, flag = detect_country_and_flag(number)
        otp = extract_otp(message)
        if not otp:
            already_sent.add(msg_id)
            continue
            
        clean_num = re.sub(r"\D", "", number)
        key = f"{clean_num}|{otp}"
        # تخطي إذا تم الإرسال مسبقًا أو تم إرساله بالفعل في هذه الدورة
        if (not force_resend and (key in already_sent or number in sent_numbers_in_cycle)) or \
           (force_resend and key in already_sent):
            continue

        if is_garbled(message):
            message = f"<#> كود ‏واتساب الخاص بك ‎{otp}\nلا تطلع أحداً عليه\n n4sgLq1p5sV6"

        safe_message = html_lib.escape(message.strip())
        # 💡 تنسيق متكيّف تلقائي حسب طول الرسالة
        msg_len = len(safe_message)
        max_len = 400
        if msg_len > max_len:
            safe_message = safe_message[:max_len] + "\n...continued ⚙️"

        if msg_len < 80:
            level = "compact"
            frame_top = "▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜"
            frame_bottom = "▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟"
        elif msg_len < 300:
            level = "standard"
            frame_top = "▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜"
            frame_bottom = "▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟"
        else:
            level = "minimal"
            frame_top = "╭────────────────────────────╮"
            frame_bottom = "╰────────────────────────────╯"

        # 💎 النص النهائي الفخم
        text = (
            f"{frame_top}\n"
            f"▌<b> {html_lib.escape(flag)} {html_lib.escape(country_guess)}  {html_lib.escape(service.upper())}     ⟡        </b> \n"
            f"{frame_bottom}\n"
            "╔═•◈•══════════════•◈•═╗\n"
            f"║ 📲 <b>Number</b>: <code>{html_lib.escape(mask_number(number))}</code>\n"
            f"║ 🔐 <b>Code</b>: <code>{html_lib.escape(otp)}</code>\n"
            f"║ 🌍 <b>Country</b>: <b>{html_lib.escape(flag)} {html_lib.escape(country_guess)}</b>\n"
            f"║ 🛰️ <b>Service</b>:<b>{html_lib.escape(service)}</b>\n"
            f"║⏱️ <b>Time</b>: <code>{html_lib.escape(date_str)}</code>\n"
            f"║ <b>💌 Full Message:</b>\n"
            "╚═•◈•══════════════•◈•═╝\n"
            f"<pre><code>{safe_message}</code></pre>\n"
            "•◈•══════════════════•◈•\n"
        )
        # إرسال لجميع الجروبات
        sent_to = []
        for gid in groups:
            try:
                bot.send_message(gid, text, parse_mode="HTML")
                SENT_MESSAGES_MEMORY.append({
                    "phone": number,
                    "text": text,
                    "chat_id": gid,
                    "time": time.time()
                })
                sent_to.append(gid)
                time.sleep(1)
            except Exception as e:
                logger.error("Failed to send to %s: %s", gid, e)

        # سجل الإرسال بعد الانتهاء من الحلقة
        if sent_to:
            if len(sent_to) == 1:
                logger.info("[%s] Sent OTP %s | %s to group %s", acc_name, otp, number, sent_to[0])
            else:
                logger.info("[%s] Sent OTP %s | %s To %d groups", acc_name, otp, number, len(sent_to))

        already_sent.add(key)
        sent_numbers_in_cycle.add(number)
        save_already_sent(acc_name, already_sent)
        try:
            save_last_id(acc_name, int(msg_id))
        except Exception:
            pass

        stats = load_stats()
        stats["today_sms_count"] = stats.get("today_sms_count", 0) + 1
        stats["total_sms_sent"] = stats.get("total_sms_sent", 0) + 1
        stats["last_date"] = str(date.today())
        save_stats(stats)

        sent_any = True

    return sent_any

# monitor thread
def monitor_loop():
    logger.info("🚀 Monitor thread started")
    cfg = load_config()
    # initial FORCE_RESEND cycle per-account if enabled
    if FORCE_RESEND_ON_START:
        for acc in ACCOUNTS:
            try:
                process_account_once(acc, force_resend=True)
            except Exception as e:
                logger.error("Error during initial FORCE_RESEND for %s: %s", acc.get("name"), e)

    while True:
        try:
            cfg = load_config()
            if not cfg.get("monitoring_active", True):
                time.sleep(POLL_INTERVAL)
                continue

            for acc in ACCOUNTS:
                try:
                    process_account_once(acc, force_resend=False)
                except Exception as e:
                    logger.exception("Error processing account %s: %s", acc.get("name"), e)
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.exception("Monitor loop crash:")
            time.sleep(POLL_INTERVAL)

# ========== Admin command system (telebot handlers) ==========
def html_escape(v):
    return html_lib.escape(str(v))

# -------------------------
# help / admin info (fix: don't escape whole help text)
# -------------------------
@bot.message_handler(commands=['albrans'])
def cmd_albrans(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ هذا الأمر مخصص للمشرف فقط.")
        return
    text = (
        "🤖 <b>بوت مراقبة OTP - نظام الإدارة</b>\n\n"
        "الأوامر المتاحة:\n"
        "/on - بدء مراقبة الرسائل\n"
        "/off - إيقاف مراقبة الرسائل\n"
        "/status - عرض حالة المراقبة الحالية\n"
        "/admin - عرض لوحه الادمن\n"
        "/groupadd &lt;group_id&gt; - إضافة مجموعة جديدة لتحويل الرسائل\n"
        "/groups - عرض قائمة المجموعات\n"
        "/groupdel &lt;group_id&gt; - حذف مجموعة من التحويل\n"
        "/ban  &lt;user_id&gt; - حظر مستخدم من استخدام البوت\n"
        "/unban &lt;user_id&gt; - فك الحظر\n"
        "/banned - عرض قائمة المحظورين\n"
    )
    # نرسل النص كما هو مع parse_mode HTML (لا نعمل escape هنا)
    bot.send_message(m.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['on'])
def cmd_on(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return
    cfg = load_config()
    cfg["monitoring_active"] = True
    save_config(cfg)
    bot.reply_to(m, "✅ تم تفعيل البوت الآن.", parse_mode="HTML")
    for gid in load_groups():
        try:
            bot.send_message(gid, "✅ <b>تم تفعيل البوت من قبل الإدارة.</b>", parse_mode="HTML")
        except Exception:
            pass

@bot.message_handler(commands=['off'])
def cmd_off(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return
    cfg = load_config()
    cfg["monitoring_active"] = False
    save_config(cfg)
    bot.reply_to(m, "⏸️ تم إيقاف المراقبة.", parse_mode="HTML")
    for gid in load_groups():
        try:
            bot.send_message(gid, "⏸️ <b>تم إيقاف البوت من قبل الإدارة مؤقتاً.</b>", parse_mode="HTML")
        except Exception:
            pass

@bot.message_handler(commands=['status'])
def cmd_status(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return

    cfg = load_config()
    stats = load_stats()
    groups = load_groups()
    users = load_users()
    bans = load_bans()

    txt = "📊 <b>حالة البوت</b>\n\n"
    txt += f"🔄 <b>المراقبة:</b> {'مفعّلة' if cfg.get('monitoring_active', True) else 'متوقفة'}\n"
    txt += f"📅 <b>التاريخ الحالي:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt += f"📱 <b>عدد الرسائل اليوم:</b> {stats.get('today_sms_count', 0)}\n"
    txt += f"📊 <b>إجمالي الرسائل:</b> {stats.get('total_sms_sent', 0)}\n"
    txt += f"👥 <b>عدد المجموعات:</b> {len(groups)}\n"
    txt += f"🧑‍💻 <b>عدد مستخدمي البوت الكلي:</b> {len(users)}\n"
    txt += f"⛔ <b>عدد المحظورين:</b> {len(bans)}\n"

    bot.send_message(m.chat.id, txt, parse_mode="HTML")

# -------------------------
# list groups (عرض بطريقة آمنة)
# -------------------------
@bot.message_handler(commands=['groups'])
def cmd_groups(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return
    groups = load_groups()  # توقع أن العناصر أعداد (ints) أو نصوص رقمية
    if not groups:
        bot.reply_to(m, "📂 لا توجد مجموعات محفوظة.", parse_mode="HTML")
        return

    lines = ["📂 <b>قائمة المجموعات:</b>"]
    for g in sorted(groups, key=lambda x: int(x)):
        # حاول جلب اسم القناة/المجموعة إن أمكن
        try:
            info = bot.get_chat(int(g))
            title = info.title or str(g)
        except Exception:
            title = str(g)
        lines.append(f"- <code>{html_escape(title)}</code> · <code>{html_escape(g)}</code>")

    bot.send_message(m.chat.id, "\n".join(lines), parse_mode="HTML")
@bot.message_handler(commands=['groupadd'])
def cmd_groupadd(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ هذا الأمر مخصص فقط للمشرف.")
        return

    parts = m.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم الأمر بهذا الشكل:\n/groupadd &lt;group_or_channel_id&gt;", parse_mode="HTML")
        return

    raw = parts[1]
    try:
        # محاولة التعرف على المعرف
        if raw.startswith('@'):
            chatinfo = bot.get_chat(raw)
            gid = str(chatinfo.id)
            name = chatinfo.title or raw
        elif raw.lstrip('-').isdigit():
            gid = str(raw)
            chatinfo = bot.get_chat(gid)
            name = chatinfo.title or gid
        else:
            bot.reply_to(m, "⚠️ المعرف غير صالح.", parse_mode="HTML")
            return

        # تحميل المجموعات الحالية
        groups = load_groups()
        if gid in groups:
            bot.reply_to(m, f"⚠️ هذه المجموعة أو القناة مضافة بالفعل: <code>{html_escape(name)}</code>", parse_mode="HTML")
            return

        # الإضافة والحفظ
        groups.add(gid)
        save_groups(groups)

        bot.reply_to(m, f"✅ تم إضافة المجموعة / القناة بنجاح:\n<code>{html_escape(name)}</code>\n🆔 <code>{html_escape(gid)}</code>", parse_mode="HTML")

        try:
            bot.send_message(int(gid), "📡 <b>تم ربط هذه القناة / المجموعة مع نظام البوت.</b>", parse_mode="HTML")
        except Exception as e:
            bot.reply_to(m, f"⚠️ لم يتم إرسال رسالة تأكيد داخل القناة (ربما البوت ليس مشرفًا).\nخطأ: <code>{html_escape(str(e))}</code>", parse_mode="HTML")

    except Exception as e:
        bot.reply_to(m, f"❌ خطأ أثناء الإضافة: <code>{html_escape(str(e))}</code>", parse_mode="HTML")


@bot.message_handler(commands=['groupdel'])
def cmd_groupdel(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ هذا الأمر مخصص فقط للمشرف.")
        return

    parts = m.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم الأمر بهذا الشكل:\n/groupdel &lt;group_or_channel_id&gt;", parse_mode="HTML")
        return

    raw = parts[1]
    try:
        gid = str(raw)
        groups = load_groups()

        if gid not in groups:
            bot.reply_to(m, f"❌ لا يوجد ارتباط بهذه المجموعة أو القناة: <code>{html_escape(gid)}</code>", parse_mode="HTML")
            return

        groups.remove(gid)
        save_groups(groups)

        bot.reply_to(m, f"🗑️ تم حذف المجموعة / القناة:\n<code>{html_escape(gid)}</code>", parse_mode="HTML")

        try:
            bot.send_message(int(gid), "⚠️ <b>تم إزالة هذه القناة / المجموعة من نظام البوت.</b>", parse_mode="HTML")
        except Exception:
            pass

    except Exception as e:
        bot.reply_to(m, f"❌ خطأ أثناء الحذف: <code>{html_escape(str(e))}</code>", parse_mode="HTML")

# ========== Ban / Unban / Banned list ==========
@bot.message_handler(commands=['ban'])
def cmd_ban(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return
    parts = m.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ الاستخدام: /ban &lt;user_id&gt;", parse_mode="HTML")
        return
    try:
        uid = int(parts[1])
        bans = load_bans()
        if uid in bans:
            bot.reply_to(m, f"⚠️ المستخدم <code>{uid}</code> بالفعل محظور.", parse_mode="HTML")
            return
        bans.add(uid)
        save_bans(bans)
        bot.reply_to(m, f"⛔ تم حظر المستخدم: <code>{uid}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(m, f"❌ خطأ: {html_escape(str(e))}", parse_mode="HTML")

@bot.message_handler(commands=['unban'])
def cmd_unban(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return
    parts = m.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ الاستخدام: /unban &lt;user_id&gt;", parse_mode="HTML")
        return
    try:
        uid = int(parts[1])
        bans = load_bans()
        if uid not in bans:
            bot.reply_to(m, f"⚠️ المستخدم <code>{uid}</code> غير محظور.", parse_mode="HTML")
            return
        bans.remove(uid)
        save_bans(bans)
        bot.reply_to(m, f"✅ تم فك الحظر عن المستخدم: <code>{uid}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(m, f"❌ خطأ: {html_escape(str(e))}", parse_mode="HTML")

@bot.message_handler(commands=['banned'])
def cmd_banned(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return
    bans = load_bans()
    if not bans:
        bot.reply_to(m, "📭 لا يوجد محظورين حالياً.", parse_mode="HTML")
        return
    lines = ["⛔ <b>قائمة المحظورين:</b>"]
    for b in sorted(bans):
        lines.append(f"- <code>{html_escape(b)}</code>")
    bot.send_message(m.chat.id, "\n".join(lines), parse_mode="HTML")

# ================== subscription check 
@bot.message_handler(commands=['id'])
def id_command(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📌 معرفة معلوماتك", callback_data="my_info"))
    bot.send_message(
        message.chat.id,
        "اختر أحد الخيارات:",
        reply_markup=markup
    )


# --- زر معرفة معلومات المستخدم ---
@bot.callback_query_handler(func=lambda call: call.data == "my_info")
def send_my_info(call):
    send_user_info(call.message.chat.id, call.from_user.id)


# --- دالة إرسال معلومات المستخدم ---
def send_user_info(chat_id, user_id):
    try:
        user = bot.get_chat(user_id)
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "❌ لا يوجد"
        bio = user.bio if hasattr(user, 'bio') and user.bio else "❌ لا يوجد"

        text = f"""👤 الاسم: {name}
🔗 اسم المستخدم: {username}
📝 البايو: {bio}
🆔 ID: {user_id}"""

        # ✅ محاولة جلب صورة البروفايل
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos and photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(chat_id, file_id, caption=text)
        else:
            bot.send_message(chat_id, text)

    except Exception as e:
        bot.send_message(chat_id, "❌ لا يمكن الوصول لهذا الحساب .")
#& /start ==================
def is_user_subscribed(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            mem = bot.get_chat_member(channel, user_id)
            if mem.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True
#$#$
def get_country_selection():
    markup = InlineKeyboardMarkup(row_width=2)
    visible_countries = [code for code, visible in COUNTRY_VISIBILITY.items() if visible]

    if not visible_countries:
        markup.add(InlineKeyboardButton("🚫 لا توجد دول متاحة حالياً", callback_data="no_countries"))
        return markup

    for code in visible_countries:
        markup.add(InlineKeyboardButton(COUNTRIES[code], callback_data=f"select_{code}"))

    return markup
@bot.message_handler(commands=['start', 'open'])
def cmd_start(m):
    # تتبع المستخدم الجديد فور الدخول
    track_user_and_notify_admin(m)
    chat_id = m.chat.id
    full_name = m.from_user.full_name

    # التحقق من الحظر
    if is_banned(m.from_user.id):
        bot.reply_to(m, "⛔ أنت محظور من استخدام البوت.", parse_mode="HTML")
        return

    # التحقق من الاشتراك في القنوات
    if not is_user_subscribed(m.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تحقق", callback_data="check_subscription"))

        text = (
            f"🖐 <b>︙مرحبًا {full_name}</b>\n\n"
            "- يجب الإشتراك في القنوات الرسمية لاستخدام البوت 📢\n\n"
            + "\n".join([f"➡️ <b>{c}</b>" for c in REQUIRED_CHANNELS])
            + "\n\n🙋‍♂️ ⁞ اضغط على الزر بالأسفل للتحقق ✅"
        )
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
        return

    txt = "<b>🌍 Choose Your Country 👇</b>"
    sent_msg = bot.send_message(m.chat.id, txt, parse_mode="HTML", reply_markup=get_country_selection())
# ============================================================
# 🎯 اختيار الدولة وإعطاء رقم
# ============================================================

def html_escape(text):
    return html.escape(str(text))

def get_random_number(code):
    """إرجاع رقم عشوائي من ملف الدولة"""
    file_path = os.path.join(NUMBERS_DIR, f"{code}.txt")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        numbers = [line.strip() for line in f if line.strip()]
    if not numbers:
        return None
    return random.choice(numbers)

def remove_number_from_file(code, number):
    file_path = os.path.join(NUMBERS_DIR, f"{code}.txt")
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        numbers = [line.strip() for line in f if line.strip()]
    numbers = [n for n in numbers if n != number]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(numbers))

def get_after_number_buttons(code):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🔁 Change Number", callback_data=f"change_number_{code}"))
    markup.add(InlineKeyboardButton("🌍 Change Country", callback_data="change_country"))
    return markup

# =============================
# اختيار الدولة وإعطاء رقم
#
# =============================
# 🇨🇳 اختيار الدولة وإعطاء رقم
# =============================
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_country_select(call):
    code = call.data.split("_", 1)[1]
    country_name = COUNTRIES.get(code, "غير معروف")
    random_number = get_random_number(code)
    bot.answer_callback_query(call.id)

    if not random_number:
        bot.edit_message_text(
            f"⚠️ لا توجد أرقام متاحة لـ {country_name}.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        return

    # 🧩 ربط الرقم بالمستخدم وتسجيله
    user_numbers[str(call.from_user.id)] = {
        "number": random_number,
        "country": code,
        "time": datetime.now().isoformat()
    }
    save_user_numbers()

    text = (
        f"📱 <b>Number:</b> <code>{random_number}</code>\n"
        f"🌍 <b>Country:</b> {country_name}\n"
        "⏳ Waiting For OTP..📱"
    )
    bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_after_number_buttons(code)
    )

# =============================
# تغيير الرقم
# =============================
@bot.callback_query_handler(func=lambda call: call.data.startswith("change_number_"))
def change_number(call):
    code = call.data.split("_", 2)[2]
    country_name = COUNTRIES.get(code, "غير معروف")
    random_number = get_random_number(code)
    bot.answer_callback_query(call.id)

    if not random_number:
        bot.edit_message_text(
            f"⚠️ لا توجد أرقام متاحة لـ {country_name}.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        return

    user_numbers[str(call.from_user.id)] = {
        "number": random_number,
        "country": code,
        "time": datetime.now().isoformat()
    }
    save_user_numbers()

    text = (
        f"📱 <b>Number:</b> <code>{random_number}</code>\n"
        f"🌍 <b>Country:</b> {country_name}\n"
        "⏳ Waiting For OTP...📱"
    )
    bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_after_number_buttons(code)
    )

# =============================
# تغيير الدولة
# =============================
@bot.callback_query_handler(func=lambda call: call.data == "change_country")
def change_country(call):
    bot.edit_message_text(
        "<b>🌍 Choose Your Country 👇</b>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_country_selection()
    )
    bot.answer_callback_query(call.id)

# =============================
# ===============================
@bot.message_handler(commands=['help'])
def cmd_help(m):
    # إنشاء زر التواصل مع الدعم
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📩 تواصل مع الدعم الآن", callback_data="contact_dev")
    markup.add(btn)

    text = (
        "🤖 <b>مرحبًا بك!</b>\n\n"
        "إذا واجهت أي مشكلة أو تحتاج مساعدة، يمكنك التواصل مع فريق الدعم الفني عبر الزر أدناه 👇"
    )

    bot.send_message(m.chat.id, text, parse_mode="HTML", reply_markup=markup)
# 📨 مراقبة رسائل الجروب / القناة
# ===============================
@bot.message_handler(func=lambda message: message.chat.id == CHANNEL_ID)
def handle_channel_message(message):
    text = message.text or ""

    # 🔍 استخراج البيانات من الرسالة (مرن لجميع الدول)
    number_match = re.search(r"Number:\s*([\d+•\s]+)", text)
    code_match = re.search(r"Code:\s*([0-9]+)", text)
    country_match = re.search(r"Country:\s*([^\n]+)", text)
    service_match = re.search(r"Service:\s*([^\n]+)", text)

    if not number_match or not code_match:
        return

    # تنظيف الرقم من المسافات والرموز الغير ضرورية
    number = number_match.group(1).replace("•", "").replace(" ", "").strip()
    code = code_match.group(1).strip()
    country = country_match.group(1).strip() if country_match else "غير معروف"
    service = service_match.group(1).strip() if service_match else "غير محدد"

    # دالة مساعدة لتنظيف الأرقام
    def clean_number(num):
        return re.sub(r"[^\d]", "", num)

    incoming_clean = clean_number(number)
    found_user = None
    full_number = None
    display_name = None

    # البحث عن المستخدم المرتبط بالرقم (آخر 4 أرقام)
    for user_id, info in user_numbers.items():
        user_num_clean = clean_number(info.get("number", ""))
        if user_num_clean.endswith(incoming_clean[-4:]):
            found_user = user_id
            full_number = info["number"]
            # استخدم الاسم الحقيقي إذا متوفر، وإلا اليوزر، وإلا ID
            display_name = info.get("first_name") or info.get("username") or str(user_id)
            break

    if found_user:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # رسالة للمستخدم
        msg = (
            f"☎️ <b>Number:</b> <code>{full_number}</code>\n"
            f"🔐 <b>Code:</b> <code>{code}</code>\n"
        )
        bot.send_message(int(found_user), msg, parse_mode="HTML")

        # رسالة للمشرف مع رابط تيليجرام
        admin_msg = (
            f"👤 المستخدم: <a href='tg://openmessage?user_id={found_user}'>{html_lib.escape(display_name)}</a>\n"
            f"☎️ الرقم: <code>{full_number}</code>\n"
            f"🔐 الكود: <code>{code}</code>\n"
            f"⏱️ الوقت: {now}"
        )
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML", disable_web_page_preview=True)

        # حذف الرقم بعد الإرسال
        del user_numbers[found_user]
        save_user_numbers(user_numbers)

    else:
        print("❌ لم يتم العثور على مستخدم مرتبط بهذا الرقم.")
#$#$
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check_subscription(call):
    if is_user_subscribed(call.from_user.id):
        new_text = "✅ <b>تم التحقق بنجاح 🎉</b>"
        try:
            bot.edit_message_text(
                new_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise

        # بعد التحقق، نعيد تشغيل رسالة /start تلقائياً
        cmd_start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد في القنوات المطلوبة!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "contact_dev")
def callback_contact_dev(call):
    chat_id = call.message.chat.id
    loading = bot.send_message(chat_id, "⏳ <b>جارٍ الاتصال بالمطوّر</b>.\n🛠️ الرجاء الانتظار قليلاً", parse_mode="HTML")
    def animate():
        dots = ["", ".", "..", "..."]
        for _ in range(2):
            for d in dots:
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=loading.message_id,
                                          text=f"⏳ <b>جارٍ الاتصال بالمطوّر</b>{d}", parse_mode="HTML")
                except Exception:
                    pass
                time.sleep(0.4)
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=loading.message_id,
                                  text="✔️ <b>تم الاتصال بالمطوّر.</b>\n\n✉️ أرسل الآن رسالتك أو سؤالك مباشرة هنا.", parse_mode="HTML")
        except Exception:
            pass
    threading.Thread(target=animate, daemon=True).start()

# forward private messages to admin
# Forward user message to admin and store mapping
@bot.message_handler(func=lambda m: m.chat.type == "private" 
                                 and m.from_user.id != ADMIN_ID
                                 and not re.fullmatch(r"\+?\d{7,}", m.text.strip())
                                 and not m.text.startswith("/"))
def forward_to_admin(msg):
    if is_banned(msg.from_user.id):
        bot.send_message(msg.chat.id, "⛔ أنت محظور من استخدام البوت.")
        return

    # تتبع المستخدم الجديد
    track_user_and_notify_admin(msg) 
    
    user = msg.from_user
    full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    username = f"@{user.username}" if user.username else "لا يوجد"
    content = msg.text or msg.caption or "— محتوى غير نصي —"
    info = (
        f"📩 <b>رسالة جديدة من مستخدم</b>\n\n"
        f"👤 <b>الاسم:</b> {html_escape(full_name)}\n"
        f"🆔 <b>اليوزر:</b> {html_escape(username)}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"🗒 <b>الرسالة:</b>\n{html_escape(content)}"
    )
    try:
        sent_msg = bot.send_message(ADMIN_ID, info, parse_mode="HTML")
        REPLY_MAPPING[sent_msg.message_id] = user.id
        #$#$
    except Exception as e:
        logger.error("Failed to forward user msg: %s", e)

# Admin reply using stored mapping
@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def admin_reply(m):
    reply_to_id = m.reply_to_message.message_id
    if reply_to_id in REPLY_MAPPING:
        user_id = REPLY_MAPPING[reply_to_id]
        try:
            if m.text:
                bot.send_message(
                    user_id,
                    f"💬 <b>رسالة من المطوّر:</b>\n{html_escape(m.text)}",
                    parse_mode="HTML"
                )
            elif m.photo:
                bot.send_photo(
                    user_id,
                    m.photo[-1].file_id,
                    caption="💬 رسالة من المطوّر",
                    parse_mode="HTML"
                )
            bot.reply_to(m, "✅ تم إرسال الرد بنجاح.")
        except Exception as e:
            bot.reply_to(m, f"❌ خطأ أثناء الإرسال: {html_escape(str(e))}")
    else:
        bot.reply_to(m, "⚠️ لا يمكن تحديد المستخدم المرتبط بهذه الرسالة.")

# ================== Search handler (number lookup) ==================
@bot.message_handler(func=lambda m: isinstance(m.text, str) and re.fullmatch(r"[+\d•]{7,}", m.text.strip()))
def handle_check(message):
    """
    🔢 عند إرسال رقم هاتف، يتم البحث عنه:
    1️⃣ أولاً في الذاكرة SENT_MESSAGES_MEMORY (حسب أول وآخر 4 أرقام)
    2️⃣ ثم في الـ API إن لم توجد نتيجة
    """
    if is_banned(message.from_user.id):
        bot.reply_to(message, "⛔ أنت محظور من استخدام البوت.")
        return

    try:
        phone = message.text.strip()
        norm_q = re.sub(r"\D", "", phone)
        chat_id = message.chat.id

        # 🎛️ تأثير التحميل
        loading_success = run_loading_effect_for_chat(chat_id, "🔎 جاري البحث عن الكود...")
        if not loading_success:
            bot.reply_to(message, "⚠️ حدث خطأ أثناء التحميل. حاول مرة أخرى.", parse_mode="HTML")
            return

        start_part = norm_q[:4]
        end_part = norm_q[-4:]
        found_results = []

        # ✅ 1. البحث في الذاكرة
        for msg in SENT_MESSAGES_MEMORY:
            stored_phone = str(msg.get("phone", ""))
            clean_stored = re.sub(r"\D", "", stored_phone)
            if (
                clean_stored == norm_q
                or (clean_stored.startswith(start_part) and clean_stored.endswith(end_part))
                or (stored_phone.startswith(start_part) and stored_phone.endswith(end_part))
                or (f"{start_part}•••{end_part}" in stored_phone)
                or (f"{start_part}***{end_part}" in stored_phone)
            ):
                found_results.append(msg["text"])

        # ✅ 2. البحث في الـ API إذا لم نجد في الذاكرة
        if not found_results:
            for acc in ACCOUNTS:
                data, _ = fetch_sms(
                    api_url=acc.get("api_url"),
                    username=acc.get("username"),
                    password=acc.get("password"),
                    last_id=None,
                    page=1,
                    per_page=PER_PAGE
                )
                if not data:
                    continue

                # التعامل مع شكل البيانات
                items = data if isinstance(data, list) else data.get("data") or data.get("items") or []

                for row in items:
                    number = str(row.get("destination_addr") or row.get("destination") or "")
                    raw_msg = row.get("short_message") or row.get("message") or ""
                    msg_text = decode_short_message(raw_msg)
                    otp = extract_otp(msg_text)
                    if not otp:
                        continue

                    norm_num = re.sub(r"\D", "", number)
                    if (
                        norm_q == norm_num
                        or norm_q.endswith(norm_num)
                        or norm_num.endswith(norm_q)
                        or (norm_num.startswith(start_part) and norm_num.endswith(end_part))
                    ):
                        country_name, country_flag = detect_country_and_flag(number)
                        safe_msg = html_lib.escape(msg_text.strip())
                        date_str = str(row.get("start_stamp") or row.get("date") or "")

                        formatted = (
                            f"☎️ <b>Number:</b> <code>{html_escape(number)}</code>\n"
                            f"🔐 <b>Code:</b> <code>{html_escape(otp)}</code>\n"
                            f"🌎 <b>Country:</b> {country_flag} <b>{html_escape(country_name)}</b>\n"
                            f"🕒 <b>Time:</b> <code>{html_escape(date_str)}</code>\n"
                            f"<pre><b>💌 Full Message</b></pre>\n<pre>{safe_msg}</pre>"
                        )
                        found_results.append(formatted)

        # 🔁 إزالة التكرارات
        found_results = list(dict.fromkeys(found_results))

        # 📩 عرض النتائج
        if not found_results:
            bot.send_message(
                chat_id,
                f"📭 لا توجد أكواد لهذا الرقم: <code>{html_escape(phone)}</code>",
                parse_mode="HTML"
            )
            return

        bot.send_message(
            chat_id,
            f"📬 تم العثور على {len(found_results)} نتيجة{' واحدة' if len(found_results) == 1 else ''} لرقم\n<code>{html_escape(phone)}</code>",
            parse_mode="HTML"
        )

        for res in found_results:
            bot.send_message(chat_id, res, parse_mode="HTML")

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ خطأ: <code>{html_escape(str(e))}</code>",
            parse_mode="HTML"
        )
#####
def is_user_subscribed(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            mem = bot.get_chat_member(channel, user_id)
            if mem.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True
#$#$
# --- إرسال الرسائل إلى الجروبات مع تأخير ---
def send_to_groups(message_text, groups):
    for gid in groups:
        try:
            bot.send_message(gid, message_text, parse_mode="HTML")
            time.sleep(0.6)  # تأخير 1 ثانية بين كل رسالة
        except Exception as e:
            logger.error("Failed to send message to group %s: %s", gid, e)

# --- إرسال الرسائل إلى المستخدمين مع تأخير ---
def send_to_users(message_text, users):
    for uid in users:
        try:
            bot.send_message(uid, message_text, parse_mode="HTML")
            time.sleep(0.2)  # تأخير 1 ثانية
        except Exception as e:
            logger.error("Failed to send message to user %s: %s", uid, e)

# --- إذاعة عامة للمستخدمين والجروبات ---
@bot.message_handler(commands=['all'])
def all_message_handler(message):
    if not check_admin(message.from_user.id):
        bot.reply_to(message, "❌ ليس لديك صلاحية إرسال إذاعة.")
        return

    msg = bot.send_message(message.chat.id, "📢 أرسل نص الرسالة للإذاعة:")
    bot.register_next_step_handler(msg, process_all_message)

def process_all_message(message):
    text_to_send = message.text
    groups = load_groups()
    users = load_users()
    sent_count = 0

    send_to_groups(text_to_send, groups)
    sent_count += len(groups)
    send_to_users(text_to_send, users)
    sent_count += len(users)

    bot.reply_to(message, f"✅ تم إرسال الإذاعة إلى {sent_count} جروبات ومستخدمين.")
#$#$
# 🌟 إعدادات النسخ الاحتياطي
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

BACKUP_INTERVAL = 60 * 60 * 2  # كل ساعتين
MAX_BACKUPS = 3  # الاحتفاظ بآخر 3 نسخ فقط
ADMIN_ID = 8038053114  # ضع هنا ID الإدمن

# الملفات الأساسية
USER_FILE = "user_numbers.json"

# 🧹 تنظيف النسخ القديمة
def cleanup_old_backups():
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")],
        key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x))
    )
    if len(backups) > MAX_BACKUPS:
        to_delete = backups[:-MAX_BACKUPS]
        for f in to_delete:
            try:
                os.remove(os.path.join(BACKUP_DIR, f))
                print(f"🗑️ تم حذف النسخة القديمة: {f}")
            except Exception as e:
                print(f"⚠️ فشل حذف {f}: {e}")

# 📦 إنشاء نسخة احتياطية
def create_backup():
    try:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{now}.json")

        # تحميل المستخدمين الحاليين
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                users_data = json.load(f)
        except Exception:
            users_data = {}

        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "users": users_data,  # ✅ حفظ المستخدمين
            "users_count": len(users_data),
            "sent_messages_memory": globals().get("SENT_MESSAGES_MEMORY", []),
            "banned_users": list(globals().get("BANNED_USERS", [])),
            "settings": {
                "required_channels": globals().get("REQUIRED_CHANNELS", []),
                "accounts": globals().get("ACCOUNTS", []),
            },
        }

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        print(f"✅ تم إنشاء نسخة احتياطية: {backup_file}")
        cleanup_old_backups()
        return backup_file
    except Exception as e:
        print("❌ خطأ أثناء إنشاء النسخة:", e)
        return None

# 🕒 إرسال النسخة للإدمن تلقائيًا
def send_backup_to_admin():
    try:
        backup_path = create_backup()
        if backup_path:
            with open(backup_path, "rb") as f:
                bot.send_document(
                    ADMIN_ID,
                    f,
                    caption=f"📦 نسخة احتياطية جديدة\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
    except Exception as e:
        print("⚠️ فشل إرسال النسخة:", e)
    finally:
        threading.Timer(BACKUP_INTERVAL, send_backup_to_admin).start()

# 🚀 بدء النسخ التلقائي بعد 10 ثواني من تشغيل البوت
threading.Timer(10, send_backup_to_admin).start()

# ========== أوامر يدوية ==========
@bot.message_handler(commands=["backup"])
def cmd_backup(message):
    if message.from_user.id != ADMIN_ID:
        return
    backup_path = create_backup()
    if backup_path:
        with open(backup_path, "rb") as f:
            bot.send_document(
                ADMIN_ID,
                f,
                caption="📦 نسخة احتياطية يدوية تم إنشاؤها الآن."
            )

@bot.message_handler(content_types=["document"])
def handle_backup_upload(message):
    """
    🧰 عند رفع ملف backup.json → استرجاع البيانات مباشرة
    """
    if message.from_user.id != ADMIN_ID:
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)

        restore_path = os.path.join(BACKUP_DIR, "restore.json")
        with open(restore_path, "wb") as f:
            f.write(downloaded)

        with open(restore_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        # 🔁 استرجاع البيانات
        global SENT_MESSAGES_MEMORY, BANNED_USERS, REQUIRED_CHANNELS, ACCOUNTS, user_numbers
        SENT_MESSAGES_MEMORY = backup_data.get("sent_messages_memory", [])
        BANNED_USERS = set(backup_data.get("banned_users", []))
        REQUIRED_CHANNELS = backup_data["settings"].get("required_channels", [])
        ACCOUNTS = backup_data["settings"].get("accounts", [])
        user_numbers = backup_data.get("users", {})  # ✅ استرجاع المستخدمين

        # حفظ المستخدمين في الملف الفعلي
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(user_numbers, f, ensure_ascii=False, indent=2)

        bot.reply_to(message, "✅ تم استرجاع النسخة الاحتياطية بنجاح.")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل الاسترجاع: <code>{html_escape(str(e))}</code>", parse_mode="HTML")
# ========== Memory Cleanup System ==========
def cleanup_sent_memory():
    """
    🧹 تنظيف الرسائل القديمة من الذاكرة كل 6 ساعات.
    - يحتفظ فقط بالرسائل الأحدث من 24 ساعة.
    - يظهر عداد في السجل بعد كل عملية تنظيف.
    """
    while True:
        try:
            now = time.time()
            max_age = 2 * 3600  # 24 ساعة
            before = len(SENT_MESSAGES_MEMORY)

            # الاحتفاظ فقط بالرسائل الحديثة
            SENT_MESSAGES_MEMORY[:] = [
                m for m in SENT_MESSAGES_MEMORY if now - m["time"] < max_age
            ]

            after = len(SENT_MESSAGES_MEMORY)
            logger.info(f"🧹 Memory cleanup done: {before} → {after} messages remaining 🧠")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

        time.sleep(1 * 3600)  # كل 3 ساعات

# ========== startup ==========
if __name__ == "__main__":
    logger.info("Master bot starting...")

    # تأكد من وجود الملفات الأساسية
    if not os.path.exists("config.json"):
        save_config({"monitoring_active": True, "last_check_date": str(date.today())})
    if not os.path.exists("groups.json"):
        save_groups(set())
    if not os.path.exists("stats.json"):
        save_stats({
            "today_sms_count": 0,
            "last_date": str(date.today()),
            "total_sms_sent": 0
        })
    if not os.path.exists("banned_users.json"):
        save_json("banned_users.json", [])

    # تشغيل الخيوط الخلفية
    threading.Thread(target=monitor_loop, daemon=True).start()
    threading.Thread(target=cleanup_sent_memory, daemon=True).start()

    # بدء تشغيل البوت مع إعادة الاتصال التلقائي
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"[WARNING] ⚠️ البوت انفصل مؤقتًا: {e}")
            time.sleep(5)
            print("[*] 🔄 إعادة الاتصال...")
            continue

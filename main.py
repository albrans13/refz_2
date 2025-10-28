
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
#$#$

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8438435636:AAEMBCOsoqaw-JBJ_RuUD_LRilEaKSlKHc0"
ADMIN_ID = int(os.getenv("ADMIN_ID") or 8038053114)   # ضع هنا رقم اليوزر الخاص بالمشرف (رقم)
CHAT_IDS = []  
CHANNEL_ID = -1003214839852
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

POLL_INTERVAL = 3      # seconds between monitor polls
PER_PAGE = 100
FORCE_RESEND_ON_START = True

# Required channels (for subscription check)
REQUIRED_CHANNELS = ["@AlBrAnS_OtP", "@OTP_GROUP_ALBRANS"]

# Patterns considered "garbled" that we will rewrite into friendly Arabic message
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
#$#$
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
#$#$
USERS_FILE = "bot_users.json"
REPLY_MAPPING = {}  # key: admin_message_id, value: user_id
def load_users():
    return load_json(USERS_FILE, {})  # dict

def save_bot_users(users):
    save_json(USERS_FILE, users)

# ------------------ تتبع المستخدمين ------------------
# --- تتبع المستخدمين الجدد ---
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

    # كود إعادة التوجيه
def mask_number(number: str) -> str:
    """
    يخفي 3 أرقام من منتصف الرقم ويظهر آخر 4 أرقام فقط.
    """
    if len(number) <= 7:
        # الرقم قصير جدًا، نتركه كما هو
        return number
    mid = (len(number) - 4) // 2  # نحدد بداية الخفاء بحيث يظهر آخر 4 أرقام
    return number[:mid] + "•••" + number[-4:]
# Small Quran phrases (kept from your original)
QURAN_AYAT = [
    "📖إِنَّ مَعَ الْعُسْرِ يُسْرًا — *Verily, with hardship comes ease.* (94:6)",
    "📖اللَّهُ نُورُ السَّمَاوَاتِ وَالْأَرْضِ — *Allah is the Light of the heavens and the earth.* (24:35)",
    "📖فَاذْكُرُونِي أَذْكُرْكُمْ — *So remember Me; I will remember you.* (2:152)",
    "📖وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ — *And He is over all things.* (5:120)",
    "📖حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ — *Allah is sufficient for us, and He is the best disposer.* (3:173)"
]
#ـ
def html_escape(v):
    import html as html_lib
    try:
        # نحول القيمة أولاً إلى نص قبل تمريرها
        return html_lib.escape(str(v))
    except Exception as e:
        # لو حصل أي خطأ، نحاول بطريقة ثانية آمنة
        return html_lib.escape(repr(v))
#@#
user_numbers = load_users()
# 📁 مجلد تخزين الملفات
NUMBERS_DIR = "numbers"
os.makedirs(NUMBERS_DIR, exist_ok=True)
USER_FILE = "user_numbers.json"
SENT_MESSAGES_FILE = "sent_messages.json"
OTP_EXPIRY_MINUTES = 2  # صلاحية الرقم 2 دقائق


# 🌍 الدول
COUNTRIES = {
    "EG": "🇪🇬 Egypt",
    "YE": "🇾🇪 Yemen",
    "IL": "🇮🇱 Israel",
    "IR": "🇮🇷 Iran",
    "RU": "🇷🇺 Russia",
    "SA": "🇸🇦 Saudi Arabia",
    "TR": "🇹🇷 Turkey",
    "US": "🇺🇸 United States",
    "CN": "🇨🇳 China",
    "FR": "🇫🇷 France",
    "DE": "🇩🇪 Germany",
    "GB": "🇬🇧 United Kingdom",
    "IT": "🇮🇹 Italy",
    "IN": "🇮🇳 India",
    "BR": "🇧🇷 Brazil",
}

# 🔄 حالة كل دولة (True = ظاهرة / False = مخفية)
COUNTRY_VISIBILITY = {code: True for code in COUNTRIES}


# 🧠 أمر دخول المشرف
@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, "❌ لا يمكنك الدخول، هذا الأمر مخصص للمشرف فقط.")
        return
    show_admin_panel(message.chat.id)


# ⚙️ لوحة التحكم (تعديل نفس الرسالة عند الرجوع)
def show_admin_panel(chat_id, message_id=None):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📤 رفع الأرقام", callback_data="choose_country_upload"),
        InlineKeyboardButton("🗑️ حذف الأرقام", callback_data="choose_country_delete"),
    )
    markup.add(InlineKeyboardButton("🌍 إدارة الدول", callback_data="manage_countries"))

    text = "🛠️ لوحة التحكم:"

    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)


# 🧩 اختيار الدولة قبل الرفع أو الحذف
@bot.callback_query_handler(func=lambda call: call.data in ["choose_country_upload", "choose_country_delete"])
def choose_country_action(call):
    action = "upload" if call.data == "choose_country_upload" else "delete"
    markup = InlineKeyboardMarkup(row_width=2)

    for code, name in COUNTRIES.items():
        if COUNTRY_VISIBILITY[code]:
            markup.add(InlineKeyboardButton(name, callback_data=f"{action}_{code}"))

    markup.add(InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_admin"))
    text = "📤 اختر الدولة لرفع الأرقام:" if action == "upload" else "🗑️ اختر الدولة لحذف الأرقام:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


# 📦 رفع أو حذف ملفات الدولة
@bot.callback_query_handler(func=lambda call: call.data.startswith(("upload_", "delete_")))
def handle_country_file_action(call):
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


# 📂 استقبال ملف الأرقام
def receive_numbers_file(message, code):
    if not message.document:
        bot.reply_to(message, "❌ من فضلك أرسل ملف نصي (txt).")
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


# 🌍 إدارة ظهور الدول
@bot.callback_query_handler(func=lambda call: call.data == "manage_countries")
def callback_manage_countries(call):
    markup = InlineKeyboardMarkup(row_width=2)
    for code, name in COUNTRIES.items():
        status = "✅ ظاهرة" if COUNTRY_VISIBILITY[code] else "🚫 مخفية"
        markup.add(InlineKeyboardButton(f"{name} {status}", callback_data=f"toggle_country_{code}"))

    markup.add(InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_admin"))
    bot.edit_message_text("🌍 إدارة ظهور الدول:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# 🔁 تبديل حالة الدولة (إظهار / إخفاء)
@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_country_"))
def callback_toggle_country(call):
    code = call.data.split("_")[-1]
    COUNTRY_VISIBILITY[code] = not COUNTRY_VISIBILITY[code]
    status = "✅ تم إظهار الدولة" if COUNTRY_VISIBILITY[code] else "🚫 تم إخفاء الدولة"
    bot.answer_callback_query(call.id, status)
    callback_manage_countries(call)


# ⬅️ الرجوع إلى لوحة المشرف (يعدل نفس الرسالة)
@bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
def callback_back_to_admin(call):
    show_admin_panel(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "↩️ تم الرجوع إلى لوحة التحكم")
#$#$
SENT_MESSAGES_MEMORY = load_json(SENT_MESSAGES_FILE, [])
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
# 🔢 جلب رقم عشوائي من الدولة
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
    return html.escape(text)
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
    if num.startswith("967"):
        return "Yemen", "🇾🇪"
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
            frame_top = "▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜"
            frame_bottom = "▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟"
        elif msg_len < 300:
            level = "standard"
            frame_top = "▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜"
            frame_bottom = "▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟"
        else:
            level = "minimal"
            frame_top = "╭────────────────────────────╮"
            frame_bottom = "╰────────────────────────────╯"

        # 💎 النص النهائي الفخم
        text = (
            f"{frame_top}\n"
            f"▌<b> New {html_lib.escape(flag)} {html_lib.escape(country_guess)}  {html_lib.escape(service.upper())}   ⟡        </b> \n"
            f"{frame_bottom}\n"
            "╔═•◈•════════════════•◈•═╗\n"
            f"║ 📲 <b>Number</b>: <code>{html_lib.escape(mask_number(number))}</code>\n"
            f"║ 🔐 <b>Code</b>: <code>{html_lib.escape(otp)}</code>\n"
            f"║ 🌍 <b>Country</b>: <b>{html_lib.escape(flag)} {html_lib.escape(country_guess)}</b>\n"
            f"║ 🛰️ <b>Service</b>:<b>{html_lib.escape(service)}</b>\n"
            f"║⏱️ <b>Time</b>: <code>{html_lib.escape(date_str)}</code>\n"
            f"║ <b>💌 Full Message:</b>\n"
            "╚═•◈•════════════════•◈•═╝\n"
            f"<pre><code>{safe_message}</code></pre>\n"
            "•◈•════════════════════•◈•\n"
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
        "/groupadd <group_id> - إضافة مجموعة جديدة لتحويل الرسائل\n"
        "/groups - عرض قائمة المجموعات\n"
        "/groupdel <group_id> - حذف مجموعة من التحويل\n"
        "/ban <user_id> - حظر مستخدم من استخدام البوت\n"
        "/unban <user_id> - فك الحظر\n"
        "/banned - عرض قائمة المحظورين\n"
    )
    # لا نعمل html_escape هنا لنتيح الوسوم الموجودة (نستخدم parse_mode HTML)
    bot.send_message(m.chat.id, html_escape(text), parse_mode="HTML")

@bot.message_handler(commands=['on'])
def cmd_on(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return
    cfg = load_config()
    cfg["monitoring_active"] = True
    save_config(cfg)
    bot.reply_to(m, "✅ تم تفعيل المراقبة.", parse_mode="HTML")
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

@bot.message_handler(commands=['groups'])
def cmd_groups(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ مخصص للمشرف فقط.")
        return
    groups = load_groups()
    if not groups:
        bot.reply_to(m, "📂 لا توجد مجموعات محفوظة.", parse_mode="HTML")
        return
    lines = ["📂 <b>قائمة المجموعات:</b>"]
    for g in groups:
        lines.append(f"- <code>{html_escape(g)}</code>")
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
@bot.message_handler(commands=['start', 'help'])
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
    return html.escape(text)

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
            f"🛰️ الخدمة: {service}\n"
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
        bot.send_message(msg.chat.id, "✅ تم إرسال رسالتك للمطوّر. سيتواصل معك قريباً.")
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
@bot.message_handler(func=lambda m: isinstance(m.text, str) and re.fullmatch(r"\+?\d{7,}", m.text.strip()))
def handle_check(message):
    """
    🔢 عند إرسال رقم هاتف، يتم البحث عن الرسائل المرسلة له اليوم
    سواء في الذاكرة أو من الـ API مع تأثير تحميل جميل.
    """
    if is_banned(message.from_user.id):
        bot.reply_to(message, "⛔ أنت محظور من استخدام البوت.")
        return

    try:
        phone = message.text.strip()
        norm_q = re.sub(r"\D", "", phone)
        chat_id = message.chat.id

        # 🎛️ تأثير التحميل دائمًا قبل أي تحقق
        loading_success = run_loading_effect_for_chat(chat_id, "🔎 جاري البحث عن الكود...")
        if not loading_success:
            bot.reply_to(message, "⚠️ حدث خطأ أثناء التحميل. حاول مرة أخرى.", parse_mode="HTML")
            return

        # 🔍 التحقق أولاً من الذاكرة
        found_in_memory = [
            msg for msg in SENT_MESSAGES_MEMORY
            if re.sub(r"\D", "", msg["phone"]) == norm_q
        ]

        if found_in_memory:
            # ✅ بعد التحميل، أظهر النتيجة مثل الـ API
            if len(found_in_memory) == 1:
                bot.send_message(
                    chat_id,
                    f"📬 تم العثور على الكود بنجاح لرقم\n<code>{html_escape(phone)}</code>",
                    parse_mode="HTML"
                )
            else:
                bot.send_message(
                    chat_id,
                    f"📬 تم العثور على {len(found_in_memory)} أكواد لرقم\n<code>{html_escape(phone)}</code>",
                    parse_mode="HTML"
                )

            # إرسال الرسائل المخزنة
            for msg in found_in_memory:
                bot.send_message(chat_id, msg["text"], parse_mode="HTML")
            return  # لا داعي للبحث في الـ API

        # 🔍 إذا لم يُعثر عليه في الذاكرة → نبحث في الـ API
        found_results = []

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

            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("data") or data.get("items") or []

            for row in items:
                number = str(row.get("destination_addr") or row.get("destination") or "")
                raw_msg = row.get("short_message") or row.get("message") or ""
                msg_text = decode_short_message(raw_msg)
                otp = extract_otp(msg_text)
                if not otp:
                    continue

                norm_num = re.sub(r"\D", "", number)
                if norm_q.endswith(norm_num) or norm_num.endswith(norm_q) or norm_q == norm_num:
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

        # 📨 عرض النتائج النهائية
        if not found_results:
            bot.send_message(
                chat_id,
                f"📭 لا توجد أكواد لهذا الرقم: <code>{html_escape(phone)}</code>",
                parse_mode="HTML"
            )
            return

        if len(found_results) == 1:
            bot.send_message(
                chat_id,
                f"📬 تم العثور على الكود بنجاح لرقم\n<code>{html_escape(phone)}</code>",
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                chat_id,
                f"📬 تم العثور على {len(found_results)} أكواد لرقم\n<code>{html_escape(phone)}</code>",
                parse_mode="HTML"
            )

        # إرسال كل الأكواد
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
            time.sleep(1)  # تأخير 1 ثانية بين كل رسالة
        except Exception as e:
            logger.error("Failed to send message to group %s: %s", gid, e)

# --- إرسال الرسائل إلى المستخدمين مع تأخير ---
def send_to_users(message_text, users):
    for uid in users:
        try:
            bot.send_message(uid, message_text, parse_mode="HTML")
            time.sleep(1)  # تأخير 1 ثانية
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

import os
import random
import telebot
from telebot import types

# إعداد التوكن الخاص بالبوت من متغيرات البيئة
API_TOKEN = os.getenv("7134109462:AAFSa9BRrCYdNGG-ehhcO0VzIOmB65zX0gI")
bot = telebot.TeleBot(API_TOKEN)

# مسارات البيانات المؤقتة
user_data = {}

# دالة لبدء البوت
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "مرحبًا بك في CROZN Tool!\n"
        "يمكنك الآن استخدام ميزات البوت مباشرةً."
    )

# التعامل مع الملفات
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.chat.id

    if user_id not in user_data:
        user_data[user_id] = {"lib": None, "type": None, "cpp": None}

    file_id = message.document.file_id
    file_name = message.document.file_name
    file_path = bot.get_file(file_id).file_path
    downloaded_file = bot.download_file(file_path)

    # التعامل مع ملف C++
    if file_name.endswith(".cpp"):
        user_data[user_id]["cpp"] = file_name
        with open(file_name, 'wb') as f:
            f.write(downloaded_file)
        bot.reply_to(message, f"تم استلام ملف C++: {file_name}\nاكتب /select_type لاختيار نوع الإزاحات.")
    elif file_name.endswith(".so"):
        user_data[user_id]["lib"] = file_name
        with open(file_name, 'wb') as f:
            f.write(downloaded_file)
        bot.reply_to(message, f"تم استلام ملف lib.so: {file_name}\nاكتب /select_type لاختيار نوع الإزاحات.")
    else:
        bot.reply_to(message, "يرجى إرسال ملف C++ (.cpp) أو lib.so فقط.")

# اختيار نوع الإزاحات
@bot.message_handler(commands=['select_type'])
def select_type(message):
    user_id = message.chat.id

    if user_id not in user_data or not user_data[user_id].get("cpp"):
        bot.reply_to(message, "لم يتم تحديد ملف C++ أو lib.so. يرجى إرسال الملف أولاً.")
        return

    markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
    markup.add("قوية", "متوسطة", "ضعيفة")
    bot.reply_to(message, "اختر نوع الإزاحات:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["قوية", "متوسطة", "ضعيفة"])
def set_type(message):
    user_id = message.chat.id

    user_data[user_id]["type"] = message.text
    bot.reply_to(message, f"تم تحديد نوع الإزاحات: {message.text}\nاكتب /add_offsets لإضافة الإزاحات تلقائيًا.")

# إضافة الإزاحات تلقائيًا إلى ملف C++
@bot.message_handler(commands=['add_offsets'])
def add_offsets(message):
    user_id = message.chat.id

    if user_id not in user_data or not user_data[user_id]["cpp"]:
        bot.reply_to(message, "يرجى إرسال ملف C++ أولاً.")
        return

    if user_id not in user_data or not user_data[user_id]["type"]:
        bot.reply_to(message, "يرجى تحديد نوع الإزاحات أولاً باستخدام /select_type.")
        return

    cpp_file = user_data[user_id]["cpp"]
    offsets_type = user_data[user_id]["type"]

    bot.reply_to(message, f"جارٍ إضافة الإزاحات ({offsets_type}) إلى الملف...")

    # توليد الإزاحات بناءً على النوع
    offsets = set()
    if offsets_type == "قوية":
        while len(offsets) < 500:
            offset = f"0x{random.randint(0x1000, 0x1FFF):X}"  # عناوين قريبة
            offsets.add(offset)
    elif offsets_type == "متوسطة":
        while len(offsets) < 10:
            offset = f"0x{random.randint(0x2000, 0x7FFF):X}"  # عناوين متوسطة
            offsets.add(offset)
    elif offsets_type == "ضعيفة":
        while len(offsets) < 10:
            offset = f"0x{random.randint(0x8000, 0xFFFFF0):X}"  # عناوين عشوائية
            offsets.add(offset)

    # قراءة محتوى الملف
    with open(cpp_file, 'r') as f:
        cpp_content = f.read()

    # إضافة الإزاحات داخل الكلمة المحددة
    offset_code = "\n// Added Offsets\n"
    for offset in sorted(offsets):
        offset_code += f'MemoryPatch::createWithHex("libanogs.so", {offset}, "00 20 70 47").Modify();\n'

    # إضافة الإزاحات إلى كلمات Config.LOGOBYPASS أو Config.Bypass
    if 'Config.LOGOBYPASS' in cpp_content:
        cpp_content = cpp_content.replace('Config.LOGOBYPASS', f'Config.LOGOBYPASS {offset_code}')
    elif 'Config.Bypass' in cpp_content:
        cpp_content = cpp_content.replace('Config.Bypass', f'Config.Bypass {offset_code}')

    # حفظ الملف المعدل
    modified_cpp_file = f"modified_{cpp_file}"
    with open(modified_cpp_file, 'w') as f:
        f.write(cpp_content)

    # إرسال الملف المعدل إلى المستخدم
    with open(modified_cpp_file, 'rb') as f:
        bot.send_document(message.chat.id, f)

    # تنظيف الملفات المؤقتة
    os.remove(modified_cpp_file)
    user_data[user_id]["cpp"] = None
    user_data[user_id]["type"] = None  # إعادة تعيين بيانات المستخدم

# تشغيل البوت
bot.polling()

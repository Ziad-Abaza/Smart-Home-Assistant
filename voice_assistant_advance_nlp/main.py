import json
import pyttsx3
import speech_recognition as sr
import datetime
from nltk.tokenize import word_tokenize
from fuzzywuzzy import fuzz

engine = pyttsx3.init()
engine.setProperty('rate', 120)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

#####################################################
#  لضبط الميكروفون للتقليل من الضوضاء المحيطة
#####################################################
def adjust_for_noise(recognizer, source, duration=0.3):
    recognizer.adjust_for_ambient_noise(source, duration)

#####################################################
#  لتقسيم الجملة إلى كلمات
#####################################################
def tokenize_sentence(sentence):
    return word_tokenize(sentence.lower())

#####################################################
#  لاستخراج الأمر من النص الصوتي بناءً على كلمة مفتاحية
#####################################################
def extract_command(speechstring, keyword):
    tokens = word_tokenize(speechstring.lower())
    if keyword.lower() in tokens:
        start_index = tokens.index(keyword.lower())
        command = " ".join(tokens[start_index + 1:])
        return command.strip()
    return None
#####################################################
# - لتنفيذ إجراء محدد بناءً على الأمر المعطى.
# - تتحقق من الإجراء المطلوب في القاموس وتستدعي الفانكشن المقابلة له.
#####################################################
def execute_action(action, r, password, messages):
    actions = {
        "check_password": lambda: check_password(r, password, messages),
        "play_music": lambda: play_music(messages),
        "stop_music": lambda: stop_music(messages),
        "set_alarm": lambda: set_alarm(messages),
        "cancel_alarm": lambda: cancel_alarm(messages),
        "report_time": lambda: report_time(messages),
        "report_date": lambda: report_date(messages),
        "report_name": lambda: report_name(messages),
        "report_today": lambda: report_today(messages)
    }

    if action in actions:
        actions[action]()
    else:
        print(f"Action '{action}' not recognized.")

#####################################################
# - للتحقق من كلمة المرور التي يتم التعرف عليها بالصوت.
# - تقوم بمقارنة كلمة المرور المدخلة بالصوت مع كلمة المرور الفعلية.
#####################################################
def check_password(r, password, messages):
    engine.say(messages['pass_check'])
    engine.runAndWait()
    with sr.Microphone() as source:
        adjust_for_noise(r, source)
        audio = r.listen(source)
        try:
            password_input = r.recognize_google(audio)
            print(password_input)
            if password_input.lower() == password.lower():
                print("access granted")
                engine.say("access granted")
            else:
                print("wrong password")
                engine.say("wrong password, please try again.")
            engine.runAndWait()
        except sr.UnknownValueError:
            print("could not understand audio.")
        except sr.RequestError as e:
            print(f"could not request results; {e}")
# -  للإبلاغ عن اسم المساعد الذكي.
def report_name(messages):
    response = "My name is Alex, your smart home assistant."
    print(response)
    engine.say(response)
    engine.runAndWait()

# -  للإبلاغ عن اليوم الحالي.
def report_today(messages):
    today_date = datetime.datetime.now().strftime("%A")
    response = f"Today is {today_date}."
    print(response)
    engine.say(response)
    engine.runAndWait()

# -  لتشغيل الموسيقى.
def play_music(messages):
    print("Playing music")
    engine.say("Music is now playing")
    engine.runAndWait()

# -  لإيقاف الموسيقى.
def stop_music(messages):
    print("Stopping music")
    engine.say("Music has been stopped")
    engine.runAndWait()

# -  لضبط المنبه.
def set_alarm(messages):
    print("Setting alarm")
    engine.say("Alarm has been set")
    engine.runAndWait()

# -  لإلغاء المنبه.
def cancel_alarm(messages):
    print("Cancelling alarm")
    engine.say("Alarm has been cancelled")
    engine.runAndWait()

# -  للإبلاغ عن الوقت الحالي.
def report_time(messages):
    current_time = datetime.datetime.now().strftime("%H:%M")
    response = f"The current time is {current_time}."
    print(response)
    engine.say(response)
    engine.runAndWait()

# -  للإبلاغ عن تاريخ اليوم.
def report_date(messages):
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    response = f"Today's date is {current_date}."
    print(response)
    engine.say(response)
    engine.runAndWait()

#####################################################
# - دالة لمطابقة الأمر مع قائمة الأسئلة.
# - تعيد True إذا كان أي من الأسئلة موجودًا في الأمر، وإلا تعيد False.
#####################################################
def match_command(command, question_list):
    for question in question_list:
        if question in command:
            return True
    return False

#####################################################
# - دالة لإيجاد السؤال الأكثر تشابهًا مع الأمر المدخل.
# - تستخدم نسبة التشابه لتحديد السؤال الأنسب، وتعيد الجواب المقابل له إذا كانت النسبة أكبر من العتبة المحددة.
#####################################################
def find_similar_question(command, questions_data, threshold=70):
    best_match = 0
    best_action = None

    for item in questions_data:
        for question in item['question']:
            similarity = fuzz.ratio(command.lower(), question.lower())
            if similarity > best_match:
                best_match = similarity
                best_action = item['answer']
    
    if best_match >= threshold:
        return best_action
    return None

def main():
    keyword = "alex"  # Keyword
    password = "open"  # Password
    r = sr.Recognizer()

    # JSON file
    try:
        with open('questions.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("The file 'data.json' was not found.")
        return
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
        return
    #####################################################
    # - تحميل الرسائل والأوامر والأسئلة من البيانات المدخلة.
    messages = data.get('messages', {})
    commands_data = data.get('commands', [])
    questions_data = data.get('questions', [])

    #####################################################
    # - تشغيل صوت ترحيبي للمستخدم.
    engine.say(messages.get('welcome', 'Welcome!'))
    engine.runAndWait()

    while True:
        with sr.Microphone() as source:
            #####################################################
            # - ضبط الميكروفون لتقليل الضوضاء المحيطة.
            adjust_for_noise(r, source)

            #####################################################
            # - حلقة انتظار لتلقي الصوت بعد كلمة مفتاحية.
            while True:
                print("Waiting for the keyword...")
                try:
                    audio = r.listen(source, timeout=1)  # زيادة وقت الانتظار
                    speechstring = r.recognize_google(audio)
                    print(speechstring)
                    command = extract_command(speechstring, keyword)
                    if command:
                        break
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    print("Could not understand audio.")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")

            #####################################################
            # - معالجة الأمر المدخل.
            if command:
                found = False
                #####################################################
                # - البحث عن الأمر في بيانات الأوامر.
                for item in commands_data:
                    if match_command(command.lower(), item['questions']):
                        #####################################################
                        # - تنفيذ الإجراء المقابل للأمر.
                        execute_action(item['action'], r, password, messages)
                        found = True
                        break
                if not found:
                    #####################################################
                    # - محاولة العثور على سؤال مشابه لتقديم إجابة.
                    action = find_similar_question(command, questions_data)
                    if action:
                        engine.say(action[0])  # إرجاع الإجابة الأولى
                        engine.runAndWait()
                    else:
                        print("Access denied")
                        engine.say(messages.get('pass_denied', 'Access denied.'))
                        engine.runAndWait()


if __name__ == "__main__":
    main()

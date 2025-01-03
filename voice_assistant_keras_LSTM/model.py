import json
import pyttsx3
import speech_recognition as sr
import datetime
import numpy as np
import pickle
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from fuzzywuzzy import fuzz
from nltk import pos_tag
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

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

####################################################
# - دالة get_synonyms للحصول على جميع المرادفات لكلمة معينة باستخدام WordNet
####################################################
def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)

####################################################
# - دالة generate_variations لتوليد تنويعات مختلفة للسؤال الأساسي 
# - باستخدام المرادفات والأزمنة المختلفة للأفعال
####################################################
def generate_variations(base_question):
    variations = []
    tokens = word_tokenize(base_question)
    tagged = pos_tag(tokens)
    ####################################################
    # - المرور على الكلمات وتحليلها لغويًا للحصول على الفعل من الجملة
    # - في حال كان الكلمة فعلًا، نضيف التنوّعات التي تحتوي على الأزمنة المختلفة
    # - إضافة السؤال مع do, did, will لتغيير الزمن
    ####################################################
    for word, tag in tagged:
        if tag.startswith('VB'):  
            variations.append(base_question.replace(word, f"do {word}")) 
            variations.append(base_question.replace(word, f"did {word}")) 
            variations.append(base_question.replace(word, f"will {word}"))  

        ####################################################
        # - الحصول على مرادفات للكلمة باستخدام دالة get_synonyms
        # - إضافة كل تنويع باستخدام المرادف الذي تم الحصول عليه
        ####################################################
        synonyms = get_synonyms(word)
        for synonym in synonyms:
            variations.append(base_question.replace(word, synonym))
    ####################################################
    # - إضافة بعض الأسئلة الشائعة كتنويعات للسؤال الأساسي
    ####################################################
    variations.append(f"What is {base_question}?")  
    variations.append(f"Can you tell me about {base_question}?")
    variations.append(f"Could you show me {base_question}?")
    return list(set(variations))  

####################################################
# - دالة find_similar_question للبحث عن السؤال الأقرب من السؤال المعطى من
# - المستخدم بناءً على التشابه باستخدام Fuzzy Matching
####################################################
def find_similar_question(command, questions_data, threshold=70):
    best_match = 0
    best_action = None
    best_type = None

    ####################################################
    # - توليد تنويعات مختلفة للسؤال المعطى باستخدام دالة generate_variations
    ####################################################
    variations = generate_variations(command)

    ####################################################
    # - المرور على جميع الأسئلة في البيانات والبحث عن التشابه بينها وبين الأمر المدخل
    ####################################################
    for item in questions_data:
        # - المرور على جميع الأسئلة المتاحة داخل السؤال الحالي
        for question in item['question']:  
            # - حساب نسبة التشابه بين السؤال المدخل والسؤال الحالي
            similarity = fuzz.ratio(command.lower(), question.lower())
            # - في حال كانت نسبة التشابه أعلى من أعلى تطابق تم العثور عليه حتى الآن
            if similarity > best_match:
                # - تحديث أفضل نسبة تطابق
                best_match = similarity
                # - تحديث أفضل إجابة متطابقة مع السؤال
                best_action = item['answer']
                # - حفظ نوع السؤال المتطابق
                best_type = item['type']

            # - المرور على جميع التنويعات التي تم إنشاؤها للسؤال المدخل
            for variation in variations:
                # حساب نسبة التشابه بين التنويع الحالي والسؤال
                similarity = fuzz.ratio(variation.lower(), question.lower())
                if similarity > best_match:
                    best_match = similarity
                    best_action = item['answer']
                    best_type = item['type']
                    
    ####################################################
    # - إذا كانت أفضل نسبة تطابق أكبر من العتبة المحددة، نعيد الإجابة ونوع السؤال
    ####################################################
    if best_match >= threshold:
        return best_action, best_type
    return None, None


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
                print("Access granted")
                engine.say("Access granted")
            else:
                print("Wrong password")
                engine.say("Wrong password, please try again.")
            engine.runAndWait()
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
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

######################################################
# - دالة classify_input لتصنيف المدخل إلى أمر أو سؤال أو غير معروف
######################################################
def classify_input(input_text):
    # قائمة تحتوي على كلمات تدل على أن النص المدخل سؤال
    question_words = ['what', 'how', 'when', 'where', 'who', 'why', 'is', 'are', 'can', 'could', 'do', 'does']
    # قائمة تحتوي على كلمات تدل على أن النص المدخل أمر
    command_keywords = ['open', 'play', 'stop', 'set', 'cancel', 'turn', 'activate', 'deactivate', 'report', 'tell', 'show', 'give', 'time', 'date']
    
    # تقسيم النص المدخل إلى كلمات صغيرة (tokens) وتحويله إلى أحرف صغيرة
    tokens = word_tokenize(input_text.lower())
    
    ######################################################
    # - التحقق مما إذا كان النص المدخل يحتوي على أي كلمة من كلمات الأوامر
    ######################################################
    if any(word in tokens for word in command_keywords):
        return 'command'
    
    ######################################################
    # - التحقق مما إذا كان النص المدخل يحتوي على أي كلمة من كلمات الأسئلة
    ######################################################
    if any(word in tokens for word in question_words):
        return 'question'
    
    ######################################################
    # - إرجاع 'unknown' إذا لم يكن المدخل أمراً ولا سؤالاً
    ######################################################
    return 'unknown'

##########################################################
#  -  دالة execute_command لتنفيذ الأوامر
##########################################################
def main():
    keyword = "alex"  # كلمة المفتاح
    password = "open"  # كلمة المرور
    r = sr.Recognizer()

    # تحميل WordNet
    import nltk
    nltk.download('wordnet')

    # ملف JSON
    try:
        with open('questions.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("The file 'data.json' was not found.")
        return
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
        return

    messages = data.get('messages', {})
    commands_data = data.get('commands', [])
    questions_data = data.get('questions', [])

    model = load_model('voice_command_model.h5')

    with open('tokenizer.pkl', 'rb') as f:
        tokenizer = pickle.load(f)

    with open('label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)

    engine.say(messages.get('welcome', 'Welcome!'))
    engine.runAndWait()
    while True:
        with sr.Microphone() as source:
            ##########################################################
            # - إعداد الميكروفون وضبطه لإزالة الضوضاء
            ##########################################################
            adjust_for_noise(r, source)

            ##########################################################
            # - الانتظار للكلمة المفتاحية لبدء الاستماع
            ##########################################################
            while True:
                print("Waiting for the keyword...")
                try:
                    # الاستماع للصوت مع تحديد المهلة
                    audio = r.listen(source, timeout=1)
                    # تحويل الصوت إلى نص باستخدام Google Speech Recognition
                    speechstring = r.recognize_google(audio)
                    print(speechstring)
                    # استخراج الأمر من النص المحوّل
                    command = extract_command(speechstring, keyword)
                    if command:
                        break
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    print("Could not understand audio.")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")

            ##########################################################
            # - معالجة الأمر المستخرج
            ##########################################################
            if command:
                # - تحويل الأمر الجديد إلى تسلسل رقمي
                X_new = tokenizer.texts_to_sequences([command])
                # - تعبئة التسلسل ليطابق طول المدخلات المتوقعة للنموذج
                X_new = pad_sequences(X_new, maxlen=model.input_shape[1])
                # - استخدام النموذج للتنبؤ بتصنيف الأمر
                predicted_label = model.predict(X_new)
                # - الحصول على مؤشر الفعل المتوقع
                action_index = np.argmax(predicted_label, axis=1)
                # - تحويل المؤشر إلى نص الفعل
                action = label_encoder.inverse_transform(action_index)

                # - تصنيف نوع الإدخال (أمر أو سؤال)
                input_type = classify_input(command)
                if input_type == 'command':
                    # - تنفيذ الإجراء المحدد في الأمر
                    execute_action(action[0], r, password, messages)
                elif input_type == 'question':
                    # - البحث عن سؤال مشابه
                    action, action_type = find_similar_question(command, questions_data)
                    if action:
                        engine.say(action[0])  # قراءة الإجابة
                        engine.runAndWait()
                    else:
                        print("No matching question found.")
                else:
                    print("Input type is unknown.")

if __name__ == "__main__":
    main()

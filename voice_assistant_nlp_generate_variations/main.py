import json
import pyttsx3
import speech_recognition as sr
import datetime
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from fuzzywuzzy import fuzz
from nltk import pos_tag



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
# - دالة للحصول على مرادفات كلمة
#####################################################
def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)

#####################################################
# - دالة لتوليد تنويعات السؤال
#####################################################
def generate_variations(base_question):
    variations = []
    tokens = word_tokenize(base_question)
    tagged = pos_tag(tokens)

    for word, tag in tagged:
        #####################################################
        # - إذا كان الكلمة فعلًا، يتم إنشاء تنويعات بإضافة أفعال مساعدة.
        # - استخدام "do" لتوليد سؤال في الحاضر.
        # - استخدام "did" لتوليد سؤال في الماضي.
        # - استخدام "will" لتوليد سؤال في المستقبل.
        if tag.startswith('VB'): 
            variations.append(base_question.replace(word, f"do {word}"))  
            variations.append(base_question.replace(word, f"did {word}"))  
            variations.append(base_question.replace(word, f"will {word}"))  

        #####################################################
        # - توليد تنويعات باستخدام مرادفات الكلمة.
        synonyms = get_synonyms(word)
        for synonym in synonyms:
            variations.append(base_question.replace(word, synonym))
    #####################################################
    # - إضافة تنويعات أخرى للسؤال باستخدام عبارات استفسارية شائعة.
    # - هذه الأسئلة تقدم طرقًا مختلفة للسؤال عن نفس الشيء.
    variations.append(f"What is {base_question}?") 
    variations.append(f"Can you tell me about {base_question}?")
    variations.append(f"Could you show me {base_question}?")
    return list(set(variations))  # إزالة التكرارات


###############################################################
# - دالة للبحث عن السؤال الأكثر تشابهًا مع الأمر المدخل، بناءً على العتبة المحددة.
###############################################################
def find_similar_question(command, questions_data, threshold=70):
    best_match = 0
    best_action = None
    best_type = None
    #######################################################
    # - توليد تنويعات للأمر المدخل باستخدام دالة generate_variations.
    variations = generate_variations(command)
    ########################################################
    # - البحث في قائمة الأسئلة المتاحة للعثور على التشابه بين الأمر المدخل والأسئلة.
    for item in questions_data:
        for question in item['question']:  # هنا تم تعديل 'questions' إلى 'question'
            ################################################
            # - حساب نسبة التشابه بين الأمر المدخل والسؤال الحالي باستخدام FuzzyWuzzy.
            similarity = fuzz.ratio(command.lower(), question.lower())
            # - تحديث أفضل نتيجة إذا كانت نسبة التشابه الحالية أعلى من أفضل نسبة سابقة.
            if similarity > best_match:
                best_match = similarity
                best_action = item['answer']
                best_type = item['type']

            #################################################
            # - البحث عن التشابه بين التنويعات والأسئلة المتاحة لتحسين نتائج المطابقة.
            for variation in variations:
                similarity = fuzz.ratio(variation.lower(), question.lower())
                if similarity > best_match:
                    best_match = similarity
                    best_action = item['answer']
                    best_type = item['type']
    ##################################
    # - إذا كانت أفضل نسبة تشابه أكبر من أو تساوي العتبة، يتم إرجاع الجواب والنوع.
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

#####################################################
# - دالة لتصنيف المدخلات النصية إلى أنواع مثل أوامر أو أسئلة أو غير معروف.
# - تعتمد على كلمات مفتاحية مميزة للأوامر والأسئلة.
#####################################################
def classify_input(input_text):
    question_words = ['what', 'how', 'when', 'where', 'who', 'why', 'is', 'are', 'can', 'could', 'do', 'does']
    command_keywords = ['open', 'play', 'stop', 'set', 'cancel', 'turn', 'activate', 'deactivate', 'report', 'tell', 'show', 'give', 'time', 'date']
    
    #################################################
    # - تقسيم النص المدخل إلى كلمات مفردة (tokens) وتحويل النص إلى أحرف صغيرة.
    tokens = word_tokenize(input_text.lower())
    
    #################################################
    # - التحقق إذا كانت الكلمات المفردة تحتوي على أي كلمة مفتاحية من الأوامر.
    if any(word in tokens for word in command_keywords):
        return 'command'
    
    #################################################
    # - التحقق إذا كانت الكلمات المفردة تحتوي على أي كلمة من كلمات الأسئلة.
    if any(word in tokens for word in question_words):
        return 'question'
    
    #################################################
    # - إذا لم يكن النص المدخل يتطابق مع أي أوامر أو أسئلة، يتم إرجاع 'unknown'.
    return 'unknown'


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
    ##################################################
    # - جلب الرسائل، الأوامر، والأسئلة من البيانات التي تم تحميلها من ملف JSON.
    ##################################################
    messages = data.get('messages', {})
    commands_data = data.get('commands', [])
    questions_data = data.get('questions', [])

    ##################################################
    # - نطق رسالة الترحيب إذا كانت موجودة في الملف، أو استخدام الرسالة الافتراضية "Welcome".
    engine.say(messages.get('welcome', 'Welcome!'))
    engine.runAndWait()

    while True:
        with sr.Microphone() as source:
            # - ضبط التعرف على الصوت وفقًا للضوضاء البيئية باستخدام دالة adjust_for_noise.
            adjust_for_noise(r, source)

            # - الاستماع باستمرار حتى يتم اكتشاف كلمة المفتاح أو حدوث خطأ في الإدخال الصوتي.
            while True:
                print("Waiting for the keyword...")
                try:
                    audio = r.listen(source, timeout=1)  
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

            # - التحقق من نوع الإدخال (أمر أو سؤال) باستخدام دالة classify_input.
            if command:
                input_type = classify_input(command)
                if input_type == 'command':
                    found = False
                    for item in commands_data:
                        # - التحقق مما إذا كان الأمر يتطابق مع الأوامر في البيانات باستخدام match_command.
                        if match_command(command.lower(), item['questions']):
                            # - تنفيذ الأمر المطابق باستخدام execute_action.
                            execute_action(item['action'], r, password, messages)
                            found = True
                            break
                    if not found:
                        print("Access denied")
                        engine.say(messages.get('pass_denied', 'Access denied.'))
                        engine.runAndWait()
                elif input_type == 'question':
                    # - البحث عن سؤال مشابه باستخدام find_similar_question.
                    action, action_type = find_similar_question(command, questions_data)
                    if action:
                        engine.say(action[0]) 
                        engine.runAndWait()
                    else:
                        print("No matching question found.")
                else:
                    print("Input type is unknown.")

if __name__ == "__main__":
    main()

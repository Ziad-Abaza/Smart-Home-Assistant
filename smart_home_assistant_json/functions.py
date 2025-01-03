import pyttsx3
import speech_recognition as sr
import datetime
from nltk.tokenize import word_tokenize
from fuzzywuzzy import fuzz

# Voice Assistant Settings
engine = pyttsx3.init()
engine.setProperty('rate', 120)  # Set speech rate
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Set voice (Female)

# Improve speech recognition for noise
def adjust_for_noise(recognizer, source, duration=0.3):
    recognizer.adjust_for_ambient_noise(source, duration)

# Function to tokenize a sentence into words
def tokenize_sentence(sentence):
    return word_tokenize(sentence.lower())

# Function to extract the main command from the speech input
def extract_command(speechstring, keyword):
    tokens = word_tokenize(speechstring.lower())
    if keyword.lower() in tokens:
        start_index = tokens.index(keyword.lower())
        command = " ".join(tokens[start_index + 1:])
        return command.strip()  # Return the command without leading/trailing spaces
    return None

# Function to execute different actions based on the command
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

    # Execute the action
    if action in actions:
        actions[action]()
    else:
        print(f"Action '{action}' not recognized.")

# Function to check the password
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

def report_name(messages):
    response = "My name is Alex, your smart home assistant."
    print(response)
    engine.say(response)
    engine.runAndWait()

def report_today(messages):
    today_date = datetime.datetime.now().strftime("%A")
    response = f"Today is {today_date}."
    print(response)
    engine.say(response)
    engine.runAndWait()

def play_music(messages):
    print("Playing music")
    engine.say("Music is now playing")
    engine.runAndWait()

def stop_music(messages):
    print("Stopping music")
    engine.say("Music has been stopped")
    engine.runAndWait()

def set_alarm(messages):
    print("Setting alarm")
    engine.say("Alarm has been set")
    engine.runAndWait()

def cancel_alarm(messages):
    print("Cancelling alarm")
    engine.say("Alarm has been cancelled")
    engine.runAndWait()

def report_time(messages):
    current_time = datetime.datetime.now().strftime("%H:%M")
    response = f"The current time is {current_time}."
    print(response)
    engine.say(response)
    engine.runAndWait()

def report_date(messages):
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    response = f"Today's date is {current_date}."
    print(response)
    engine.say(response)
    engine.runAndWait()

# دالة للتحقق مما إذا كان أي من الأوامر المعروفة موجودًا في النص
def match_command(command, question_list):
    for question in question_list:
        if question in command:
            return True
    return False

# دالة للبحث عن الكلمات في الأسئلة وإعادة الإجابة باستخدام التشابه
def find_similar_question(command, questions_data, threshold=70):
    best_match = 0
    best_action = None

    for item in questions_data:
        for question in item['questions']:
            similarity = fuzz.ratio(command.lower(), question.lower())
            if similarity > best_match:
                best_match = similarity
                best_action = item['action']
    
    if best_match >= threshold:
        return best_action
    return None

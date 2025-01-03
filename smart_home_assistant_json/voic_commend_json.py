import json
import pyttsx3
import speech_recognition as sr
from functions import *

def main():
    keyword = "alex"  # Keyword
    password = "open"  # Password
    r = sr.Recognizer()

    # JSON file
    with open('questions.json', 'r') as file:
        data = json.load(file)

    messages = data['messages']
    questions_data = data['questions']

    # Initialize and speak welcome message
    engine = pyttsx3.init()
    engine.say(messages['welcome'])
    engine.runAndWait()

    while True:
        with sr.Microphone() as source:
            # Adjust for ambient noise for better recognition
            adjust_for_noise(r, source)

            # Wait for keyword
            while True:
                print("Waiting for the keyword...")
                try:
                    audio = r.listen(source, timeout=0.2)
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

            # Handle commands after hearing the keyword
            if command:
                found = False
                for item in questions_data:
                    if match_command(command.lower(), item['questions']):
                        execute_action(item['action'], r, password, messages)
                        found = True
                        break
                if not found:
                    # محاولة البحث باستخدام التشابه
                    action = find_similar_question(command, questions_data)
                    if action:
                        execute_action(action, r, password, messages)
                    else:
                        print("Access denied")
                        engine.say(messages['pass_denied'])
                        engine.runAndWait()

if __name__ == "__main__":
    main()

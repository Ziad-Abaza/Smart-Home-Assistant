# Smart Home Assistant

This repository contains a **Smart Home Assistant** project featuring a voice-controlled assistant that can interact with users, execute tasks, and provide real-time responses. The assistant is designed to help manage and control home automation systems through voice commands.

## Features

- **Voice Recognition**: Uses `speech_recognition` to capture voice input.
- **Natural Language Processing (NLP)**: Integrated NLP for parsing and understanding voice commands.
- **Voice Output**: Uses `pyttsx3` for text-to-speech to respond to commands.
- **Home Automation Tasks**: Includes commands like playing music, checking the time and date, setting alarms, and more.
- **Password Protection**: Voice-commanded password verification for added security.
- **Fuzzy Matching**: Uses `fuzzywuzzy` to handle command similarity and ensure accurate responses.

## Project Structure

- **functions.py**: Contains the logic for voice interaction and actions.
- **questions.json**: Holds predefined questions and actions.
- **voice_commend_json.py**: Main script to run the assistant with voice command matching.
- **requirements.txt**: List of required Python libraries.

## How to Run

1. Clone the repository:

    ```bash
    git clone https://github.com/Ziad-Abaza/Smart-Home-Assistant.git
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the main script:

    ```bash
    python voice_commend_json.py
    ```

4. The assistant will wait for the keyword "alex" and respond to voice commands such as checking the time, playing music, setting alarms, and more.

## Commands

The assistant can handle the following voice commands:

- **Play Music**: "Play music", "Start music", "Music on"
- **Stop Music**: "Stop music", "Turn off music", "Music off"
- **Set Alarm**: "Set alarm", "Set an alarm", "Alarm on"
- **Cancel Alarm**: "Cancel alarm", "Turn off alarm", "Alarm off"
- **Report Time**: "What is the time?", "Current time", "Time please"
- **Report Date**: "What is the date?", "Current date", "Date please"
- **Get Name**: "What is your name?", "Who are you?", "Tell me your name"
- **Get Today’s Date**: "What is today?", "Today’s date", "Today’s day"
- **Unlock Door**: "Open the door", "Unlock the door", "Please open the door"

## Requirements

- Python 3.x
- Libraries:
  - pyttsx3
  - speech_recognition
  - nltk
  - fuzzywuzzy
  - datetime

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

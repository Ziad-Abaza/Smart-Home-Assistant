import json
import numpy as np
import pickle
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, Embedding, LSTM, Bidirectional
from nltk.tokenize import word_tokenize
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences


with open('questions.json', 'r') as file:
    data = json.load(file)

###################################################
# - تحميل بيانات الأوامر والأسئلة من ملف JSON.
###################################################
commands_data = data.get('commands', [])
questions_data = data.get('questions', [])

###################################################
# - إنشاء قوائم لتخزين جميع الأسئلة والتسميات المقابلة لها.
###################################################
all_sentences = []
all_labels = []

###################################################
# - المرور على كل أمر والأسئلة المقابلة له لإضافتها 
# - إلى قائمة الأسئلة وربطها بالتسمية المقابلة (الفعل).
###################################################
for item in commands_data:
    for question in item['questions']:
        all_sentences.append(question)
        all_labels.append(item['action'])

###################################################
# - تهيئة Tokenizer لتحويل النصوص إلى تسلسل رقمي.
###################################################
tokenizer = Tokenizer()
tokenizer.fit_on_texts(all_sentences)
X = tokenizer.texts_to_sequences(all_sentences)
# - تطبيق pad_sequences لضبط طول التسلسل ليتناسب مع شبكة LSTM.
X = pad_sequences(X)  

###################################################
# - استخدام LabelEncoder لترميز التسميات (الأفعال) كقيم عددية.
###################################################
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(all_labels)


###################################################
# - بناء نموذج الشبكة العصبية.
###################################################
model = Sequential()
###################################################
# - إضافة طبقة Embedding لتوليد تمثيل كثيف للكلمات.
model.add(Embedding(10000, 64, input_length=X.shape[1]))
###################################################
# - إضافة طبقات LSTM ثنائية الاتجاه للتعامل مع السياقات الزمنية للنصوص.
model.add(Bidirectional(LSTM(64, return_sequences=True)))
model.add(Bidirectional(LSTM(64)))
model.add(Dropout(0.2))
###################################################
# - إضافة طبقات Dense لتحسين التعلم وتصنيف التسميات.
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(len(np.unique(y)), activation='softmax'))

###################################################
# - تجميع النموذج باستخدام sparse_categorical_crossentropy كخسارة، وآدم كالمُحسّن.
###################################################
model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

###################################################
# - تدريب النموذج باستخدام البيانات وإجراء 2000 دورة تدريبية مع حجم دفعة 20.
###################################################
model.fit(X, y, epochs=2000, batch_size=20)
model.save('voice_command_model.h5')

###################################################
# - حفظ الـ tokenizer المستخدم في تحويل النصوص إلى أرقام.
###################################################
with open('tokenizer.pkl', 'wb') as f:
    pickle.dump(tokenizer, f)

###################################################
# - حفظ LabelEncoder المستخدم في ترميز التسميات كقيم عددية.
###################################################
with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(label_encoder, f)

# - تقييم النموذج على بيانات التدريب وعرض الخسارة والدقة.
loss, accuracy = model.evaluate(X, y, verbose=0)

print(f"Loss: {loss:.4f}")  
print(f"Accuracy: {accuracy * 100:.2f}%")  

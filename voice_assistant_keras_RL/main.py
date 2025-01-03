import random
import numpy as np
import json
import pickle
from collections import deque
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# تحميل بيانات الأسئلة من ملف JSON
with open('questions.json', 'r') as file:
    data = json.load(file)

# استخراج بيانات الأوامر
commands_data = data.get('commands', [])

# قائمة لتخزين الجمل والتسميات
all_sentences = []
all_labels = []

##############################################
# - تجميع الجمل والتسميات من بيانات الأوامر
##############################################
for item in commands_data:
    for question in item['questions']:
        all_sentences.append(question)  # إضافة السؤال إلى القائمة
        all_labels.append(item['action'])  # إضافة الإجراء المرتبط بالسؤال

##############################################
# - تحويل الجمل إلى تسلسلات رقمية
##############################################
tokenizer = Tokenizer()
tokenizer.fit_on_texts(all_sentences)  # تدريب المحلل اللغوي على الجمل
X = tokenizer.texts_to_sequences(all_sentences)  # تحويل الجمل إلى تسلسلات
X = pad_sequences(X)  # تعبئة التسلسلات لتوحيد الطول

##############################################
# - تحويل التسميات إلى قيم عددية
##############################################
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(all_labels)  # ترميز التسميات إلى أرقام
num_actions = len(np.unique(y))  # عدد الإجراءات الفريدة

##############################################
# تعريف بيئة الأوامر الصوتية
##############################################
class VoiceCommandEnv:
    def __init__(self):
        ##############################################
        # - تهيئة المتغيرات اللازمة
        self.current_step = 0  # تعقب الخطوة الحالية
        self.max_steps = len(X)  # عدد الخطوات الكلي

    ##############################################
    # - إعادة تعيين البيئة لبدء جديد
    ##############################################
    def reset(self):
        self.current_step = 0  # إعادة تعيين الخطوة الحالية
        return X[self.current_step]  # إعادة الحالة الأولية

    ##############################################
    # - تنفيذ خطوة في البيئة بناءً على الإجراء المحدد
    ##############################################
    def step(self, action):
        correct_action = y[self.current_step]  # الإجراء الصحيح للخطوة الحالية
        reward = 1 if action == correct_action else -1  # تحديد المكافأة
        self.current_step += 1  # الانتقال إلى الخطوة التالية
        done = self.current_step >= self.max_steps  # التحقق مما إذا كانت التجربة انتهت
        next_state = X[self.current_step] if not done else None  # الحصول على الحالة التالية
        return next_state, reward, done  # إرجاع الحالة التالية، المكافأة، وحالة الانتهاء

##############################################
# تعريف وكيل التعلم المعزز (DQNAgent)
##############################################
class DQNAgent:
    def __init__(self, state_size, action_size):
        ##############################################
        # - تهيئة المتغيرات اللازمة
        self.state_size = state_size  # حجم الحالة
        self.action_size = action_size  # عدد الإجراءات الممكنة
        self.memory = deque(maxlen=2000)  # ذاكرة لتخزين التجارب
        self.gamma = 0.95  # عامل التخفيض
        self.epsilon = 1.0  # احتمال الاستكشاف
        self.epsilon_min = 0.01  # الحد الأدنى للاحتمال
        self.epsilon_decay = 0.995  # معدل انخفاض الاستكشاف
        self.learning_rate = 0.001  # معدل التعلم
        self.model = self._build_model()  # بناء النموذج

    ##############################################
    # - بناء نموذج الشبكة العصبية
    ##############################################
    def _build_model(self):
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))  # الطبقة الأولى
        model.add(Dense(24, activation='relu'))  # الطبقة الثانية
        model.add(Dense(self.action_size, activation='linear'))  # طبقة الإخراج
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))  # تجميع النموذج
        return model

    ##############################################
    # - تخزين التجارب في الذاكرة
    ##############################################
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))  # إضافة التجربة إلى الذاكرة

    ##############################################
    # - اتخاذ إجراء بناءً على الحالة الحالية
    ##############################################
    def act(self, state):
        if np.random.rand() <= self.epsilon:  # استكشاف
            return random.randrange(self.action_size)  # اختيار إجراء عشوائي
        act_values = self.model.predict(state)  # التنبؤ بالقيم
        return np.argmax(act_values[0])  # اختيار الإجراء الأفضل

    ##############################################
    # - تدريب النموذج باستخدام التجارب المخزنة
    ##############################################
    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)  # عينة عشوائية من الذاكرة
        for state, action, reward, next_state, done in minibatch:
            target = reward  # المكافأة الحالية
            if not done:
                target = (reward + self.gamma * np.amax(self.model.predict(next_state)[0]))  # حساب الهدف
            target_f = self.model.predict(state)  # توقع القيم الحالية
            target_f[0][action] = target  # تحديث الهدف
            self.model.fit(state, target_f, epochs=1, verbose=0)  # تدريب النموذج
        if self.epsilon > self.epsilon_min:  # تقليل احتمال الاستكشاف
            self.epsilon *= self.epsilon_decay

##############################################
# - تهيئة البيئة والوكيل
##############################################
env = VoiceCommandEnv()  # إنشاء بيئة الأوامر الصوتية
state_size = X.shape[1]  # حجم الحالة
agent = DQNAgent(state_size, num_actions)  # إنشاء الوكيل

##############################################
# - بدء عملية التدريب
##############################################
batch_size = 32  # حجم الدفعة
for e in range(1000):  # حلقات التدريب
    ##############################################
    # - إعادة تعيين البيئة والحصول على الحالة الأولية
    state = env.reset()
    state = np.reshape(state, [1, state_size])  # إعادة تشكيل الحالة

    ##############################################
    # - تنفيذ الخطوات في البيئة
    for time in range(env.max_steps):
        action = agent.act(state)  # اتخاذ إجراء
        ##############################################
        # - تنفيذ الخطوة في البيئة والحصول على الحالة التالية
        next_state, reward, done = env.step(action)
        next_state = np.reshape(next_state, [1, state_size]) if next_state is not None else None  # إعادة تشكيل الحالة التالية
        ##############################################
        # - تخزين التجربة في الذاكرة
        agent.remember(state, action, reward, next_state, done)
        state = next_state  # تحديث الحالة الحالية

        ##############################################
        # - إنهاء الحلقة إذا انتهت التجربة
        if done:
            print(f"episode: {e}/{1000}, score: {time}, e: {agent.epsilon:.2}")  # طباعة التقدم
            break
    if len(agent.memory) > batch_size:  # إذا كانت الذاكرة تحتوي على تجارب كافية
        agent.replay(batch_size)  # تدريب النموذج

##############################################
# - حفظ النموذج المدرب
##############################################
agent.model.save('dqn_voice_command_model.h5')  # حفظ النموذج في ملف

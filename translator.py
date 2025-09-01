# --- 终极胜利版 V11 (神圣咒语归位) ---

# --- 【【【最终的、绝对的、神圣的咒语！必须是第一行！】】】 ---
from multiprocessing import freeze_support
if __name__ == '__main__':
    freeze_support()
# -----------------------------------------------------------------

import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import pyqtSignal, QObject
import speech_recognition as sr
import simpleaudio as sa
import google.generativeai as genai
from gtts import gTTS
import io
from pydub import AudioSegment
import logging

# ... [后面所有的代码，都和我们之前的V8/V9/V10版本一模一样！] ...
log_file_path = 'translator_log.txt'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_file_path, mode='w'), logging.StreamHandler(sys.stdout)])
logging.info("程序启动...")
LANGUAGES = {"中文 (简体)": "zh-CN", "English (US)": "en-US", "日本語": "ja", "한국어": "ko", "Français": "fr", "Español": "es"}
LANG_MAP_TO_ENGLISH = {"zh-CN": "Simplified Chinese", "en-US": "English", "ja": "Japanese", "ko": "Korean", "fr": "French", "es": "Spanish"}
GEMINI_API_KEY = 'AIzaSyCDcQUjyDZgWb0IASHq9jsCLOX1-hPqp2E'
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

def call_google_gemini_api(text, target_lang_code):
    try:
        target_lang_name = LANG_MAP_TO_ENGLISH.get(target_lang_code, "the target language")
        logging.info(f"发送请求到Gemini: '{text}' -> {target_lang_name}")
        prompt = f"Please translate the following text into {target_lang_name}. Provide only the translated text, without any additional explanations, introductory phrases, or quotation marks.\n\nText to translate: \"{text}\""
        response = gemini_model.generate_content(prompt)
        translated_text = response.text
        logging.info(f"收到Gemini响应: '{translated_text}'")
        return translated_text.strip()
    except Exception as e:
        logging.error(f"调用Gemini API失败: {e}")
        return None

def text_to_speech_and_play(text, lang_code):
    if not text: return
    try:
        logging.info(f"正在生成语音: {text}")
        tts = gTTS(text=text, lang=lang_code)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio = AudioSegment.from_file(mp3_fp, format="mp3")
        logging.info("正在播放语音...")
        play_obj = sa.play_buffer(audio.raw_data, audio.channels, audio.sample_width, audio.frame_rate)
        play_obj.wait_done()
        logging.info("播放完成。")
    except Exception as e:
        logging.error(f"TTS或播放失败: {e}")

class WorkerSignals(QObject):
    update_status = pyqtSignal(str)
    update_recognized = pyqtSignal(str)
    update_translated = pyqtSignal(str)
    finished = pyqtSignal()

class TranslationWorker(threading.Thread):
    def __init__(self, source_lang, target_lang):
        super().__init__()
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.signals = WorkerSignals()
        self.is_running = True

    def run(self):
        try:
            r = sr.Recognizer()
            mic = sr.Microphone()
            with mic as source: r.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_running:
                try:
                    self.signals.update_status.emit("正在聆听...")
                    with mic as source: audio = r.listen(source)
                    
                    wav_data = audio.get_wav_data()
                    audio_segment = AudioSegment.from_file(io.BytesIO(wav_data), format="wav")
                    boosted_audio = audio_segment + 15
                    boosted_wav_data = boosted_audio.export(format="wav").read()
                    audio = sr.AudioData(boosted_wav_data, mic.SAMPLE_RATE, mic.SAMPLE_WIDTH)
                    
                    self.signals.update_status.emit("识别中...")
                    recognized_text = r.recognize_google(audio, language=self.source_lang)
                    self.signals.update_recognized.emit(recognized_text)

                    self.signals.update_status.emit("翻译中 (Gemini)...")
                    translated_text = call_google_gemini_api(recognized_text, self.target_lang)
                    
                    if translated_text:
                        self.signals.update_translated.emit(translated_text)
                        self.signals.update_status.emit("正在播放...")
                        text_to_speech_and_play(translated_text, self.target_lang)
                    else:
                        self.signals.update_status.emit("翻译失败")
                
                except sr.UnknownValueError: continue
                except Exception as e:
                    logging.error(f"翻译循环中发生错误: {e}")
                    self.signals.update_status.emit(f"发生错误!")
                    break
        finally:
            self.signals.finished.emit()

class TranslatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('多语言实时翻译器 V11.0 (最终圣战版)')
        self.setGeometry(300, 300, 450, 300)
        layout = QVBoxLayout()
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(LANGUAGES.keys())
        self.source_lang_combo.setCurrentText("中文 (简体)")
        layout.addWidget(QLabel("我说的语言:"))
        layout.addWidget(self.source_lang_combo)
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(LANGUAGES.keys())
        self.target_lang_combo.setCurrentText("日本語")
        layout.addWidget(QLabel("翻译的语言:"))
        layout.addWidget(self.target_lang_combo)
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)
        self.recognized_label = QLabel("识别内容: ")
        self.recognized_label.setWordWrap(True)
        layout.addWidget(self.recognized_label)
        self.translated_label = QLabel("翻译结果: ")
        self.translated_label.setWordWrap(True)
        layout.addWidget(self.translated_label)
        self.toggle_button = QPushButton("开始翻译")
        self.toggle_button.clicked.connect(self.toggle_translation)
        layout.addWidget(self.toggle_button)
        self.setLayout(layout)

    def toggle_translation(self):
        if self.worker and self.worker.is_running:
            self.worker.is_running = False
        else:
            source_lang = LANGUAGES[self.source_lang_combo.currentText()]
            target_lang = LANGUAGES[self.target_lang_combo.currentText()]
            if source_lang == target_lang:
                self.status_label.setText("错误: 源语言和目标语言不能相同！")
                return
            self.worker = TranslationWorker(source_lang, target_lang)
            self.worker.signals.update_status.connect(self.status_label.setText)
            self.worker.signals.update_recognized.connect(lambda text: self.recognized_label.setText(f"识别内容: {text}"))
            self.worker.signals.update_translated.connect(lambda text: self.translated_label.setText(f"翻译结果: {text}"))
            self.worker.signals.finished.connect(self.on_worker_finished)
            self.worker.start()
            self.toggle_button.setText("停止翻译")
            self.source_lang_combo.setEnabled(False)
            self.target_lang_combo.setEnabled(False)

    def on_worker_finished(self):
        self.toggle_button.setText("开始翻译")
        self.source_lang_combo.setEnabled(True)
        self.target_lang_combo.setEnabled(True)
        self.status_label.setText("已停止")

# --- 主程序入口被移到了神圣咒语之后 ---
app = QApplication(sys.argv)
ex = TranslatorApp()
ex.show()
sys.exit(app.exec())

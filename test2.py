from flask import Flask, jsonify, render_template
import sounddevice as sd
import numpy as np
import pandas as pd
import os
from datetime import datetime
from scipy.signal import butter, lfilter

app = Flask(__name__)

# Konfigurasi Audio
CHUNK = 1024
RATE = 44100
USB_MIC_INDEX = 2  # Ganti dengan indeks mikrofon USB Anda
REF_PRESSURE = 20e-6  # Referensi tekanan suara 20 µPa

current_log_file = None


# Filter Butterworth (Low-pass)
def butter_lowpass(cutoff=2000, fs=RATE, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def apply_lowpass_filter(data, cutoff=2000):
    b, a = butter_lowpass(cutoff)
    return lfilter(b, a, data)


# Fungsi untuk mendapatkan nilai desibel
def get_decible():
    audio_data = sd.rec(CHUNK, samplerate=RATE, channels=1, dtype='float32', device=USB_MIC_INDEX)
    sd.wait()  # Tunggu sampai perekaman selesai
    audio_data = audio_data.flatten()  # Ubah ke 1D array

    filtered_data = apply_lowpass_filter(audio_data)

    rms = np.sqrt(np.mean(np.square(filtered_data)))
    db_spl = 30 * np.log10(rms / REF_PRESSURE) if rms > 0 else -np.inf
    return round(db_spl, 2)


# Membuat file log baru
def create_new_log_file():
    global current_log_file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"log_{timestamp}.xlsx"
    df = pd.DataFrame(columns=["Timestamp", "Decibel"])
    df.to_excel(filename, index=False)
    current_log_file = filename
    print(f"[INFO] Created new log file: {filename}")


# Menyimpan data ke file Excel
def log_to_excel(decibel_value):
    if not current_log_file:
        return
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df = pd.read_excel(current_log_file)
    new_entry = pd.DataFrame([[timestamp, decibel_value]], columns=["Timestamp", "Decibel"])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_excel(current_log_file, index=False)


# ROUTES
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start')
def start():
    create_new_log_file()
    return jsonify({"status": "started"})


@app.route('/decibel')
def decibel():
    db = get_decible()
    log_to_excel(db)
    return jsonify({"decibel": db})


# Jalankan aplikasi Flask
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, jsonify, render_template
import pyaudio
import numpy as np
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

CHUNK = 1024
RATE = 44100

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

current_log_file = None


def get_decible():
    data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
    rms = np.sqrt(np.mean(np.square(data)))
    db = 20 * np.log10(rms) if rms > 0 else 0
    return round(db, 2)


def create_new_log_file():
    global current_log_file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"log_{timestamp}.xlsx"
    df = pd.DataFrame(columns=["Timestamp", "Decibel"])
    df.to_excel(filename, index=False)
    current_log_file = filename
    print(f"[INFO] Created new log file: {filename}")


def log_to_excel(decibel_value):
    if not current_log_file:
        return
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df = pd.read_excel(current_log_file)
    new_entry = pd.DataFrame([[timestamp, decibel_value]], columns=["Timestamp", "Decibel"])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_excel(current_log_file, index=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start')
def start():
    create_new_log_file()
    return jsonify({"status": "started"})


@app.route('/decibel')
def decible():
    db = get_decible()
    log_to_excel(db)
    return jsonify({"decibel": db})


if __name__ == '__main__':
    app.run(debug=True)

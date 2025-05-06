import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

# Konfigurasi Audio
RATE = 44100  # Sampling rate
CHUNK = 1024  # Ukuran buffer
USB_MIC_INDEX = 2  # Ganti dengan indeks mikrofon USB Anda
REF_PRESSURE = 20e-6  # Referensi tekanan suara 20 µPa


# Filter Butterworth (Low-pass)
def butter_lowpass(cutoff=2000, fs=RATE, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def apply_lowpass_filter(data, cutoff=2000):
    b, a = butter_lowpass(cutoff)
    return lfilter(b, a, data)


# Callback untuk menangkap audio dan hitung dB
def audio_callback(indata, frames, time, status):
    if status:
        print(status)

    audio_data = indata[:, 0]  # Ambil satu channel (mono)
    audio_data = apply_lowpass_filter(audio_data)  # Terapkan filter

    # Hitung RMS
    rms = np.sqrt(np.mean(np.square(audio_data)))

    # Hitung dB SPL
    db_spl = 30 * np.log10(rms / REF_PRESSURE) if rms > 0 else -np.inf

    print(f"Tingkat suara: {db_spl:.2f} dB")


# Jalankan pengukuran suara
with sd.InputStream(device=USB_MIC_INDEX, channels=1, samplerate=RATE, blocksize=CHUNK, callback=audio_callback):
    print("Mendeteksi suara... Tekan Ctrl+C untuk berhenti.")
    while True:
        try:
            sd.sleep(100)
        except KeyboardInterrupt:
            print("\nPengukuran selesai.")
            break

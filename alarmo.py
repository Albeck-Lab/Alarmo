from discord_webhook import DiscordWebhook
from datetime import datetime,timedelta
import numpy as np
import sounddevice as sd

"""CONSTANTS"""
TARGET_FREQS = [3175, 6350, 9500] #Frequencies of the alarm tone
AMPLITUDE_THRESHOLDS = [0.05,0.02,0.02] #Amplitude of that frequency above which to send notification
RATE = 44100
CHANNELS = 1
BLOCK_SIZE = 1024*4
alarm_duration_threshold = 20 #20 seconds
reset_timer = 20

URL = "https://discord.com/api/webhooks/1240034509597052990/5qLJb4YvovYAnHrMG9ZThSNfbjU9F0lk0MuBB8CDSbmj4zSLGXNNTzlvS_YvytirmF8W"

freq_bins = np.fft.fftfreq(BLOCK_SIZE) * RATE #FFT frequencies map
target_indices = []
for freq in TARGET_FREQS:
    target_indices.append(np.abs(freq_bins - freq).argmin()) #Index of the target frequency
event_start_time = None
notification_sent = False
last_event_detection_time = None

def notify_discord(message):
    webhook = DiscordWebhook(url=URL,content=message)
    response = webhook.execute()

def handle_event(amplitudes):
    global event_start_time, notification_sent, last_event_detection_time
    
    if np.all(amplitudes >= AMPLITUDE_THRESHOLDS):
        print("Alarm heard")
        print(amplitudes)
        #Handle the event
        if event_start_time is None:
            print("Setting event start")
            event_start_time = datetime.now()
        
        event_duration = datetime.now() - event_start_time
        
        if event_duration >= timedelta(seconds=alarm_duration_threshold):
            print("Event duration threshold met")
            if not notification_sent:
                notify_discord(f"Freezer Alarm Detected - {datetime.now()}")
                notification_sent = True
        else:
            notification_sent = False
            
        last_event_detection_time = datetime.now()
    else:
        if last_event_detection_time:
            if datetime.now() - last_event_detection_time >= timedelta(seconds = reset_timer):
                print("Reset time threshold met. Resetting timers.")
                event_start_time = None
                notification_sent = False
                last_event_detection_time = None
                notify_discord(f"Freezer Alarm Has Stopped - {datetime.now()}")

def audio_callback(indata, frames, time, status):
    fft_result = np.fft.fft(indata)
    amplitudes = []
    for idx in target_indices:
        amplitudes.append(np.mean(np.abs(fft_result[idx-1:idx+2].real))) #Mean of the absolute value of the target index and its neighboring frequencies
    handle_event(amplitudes)
            
with sd.InputStream(channels=CHANNELS, 
                    callback=audio_callback,
                    samplerate=RATE,
                    blocksize=BLOCK_SIZE,
                    device = 0):
    while True:
        pass
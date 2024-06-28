from discord_webhook import DiscordWebhook
from datetime import datetime,timedelta,time
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt

"""CONSTANTS"""
TARGET_FREQS = [3175, 6350, 9500] #Frequencies of the alarm tone
AMPLITUDE_THRESHOLDS = [0.09, 0.06,0.06] #Amplitude of that frequency above which to send notification
RATE = 44100
CHANNELS = 1
reset_timer = 20
zscore_thresh = 1

fig_name = "specgram.jpg"

hours_inactive_1 = time(17,0,0) # 5:00:00 PM
hours_inactive_2 = time(7,59,59) # 7:59:59 AM

hours_active_1 = time(8,0,0) # 8:00:00 AM
hours_active_2 = time(16,59,59) # 4:59:59 PM

def get_alarm_duration_threshold():
    now = datetime.now().time()
    if now >= hours_inactive_1 or now <= hours_inactive_2:
        alarm_duration_threshold = 20
    elif now <= hours_active_1 and now <= hours_active_2:
        alarm_duration_threshold = 300
    else:
        alarm_duration_threshold = 20
    return alarm_duration_threshold


URL = "https://discord.com/api/webhooks/1240034509597052990/5qLJb4YvovYAnHrMG9ZThSNfbjU9F0lk0MuBB8CDSbmj4zSLGXNNTzlvS_YvytirmF8W"

freq_bins = np.fft.fftfreq(RATE,1/RATE) #FFT frequencies map

target_indices = []
for freq in TARGET_FREQS:
    target_indices.append(np.abs(freq_bins - freq).argmin()) #Index of the target frequency
event_start_time = None
notification_sent = False
last_event_detection_time = None

device = sd.query_devices("USB PnP Sound Device: Audio (hw:1,0)")['index']

window = np.abs(freq_bins) >= 2000
window[target_indices] = 0 #[x+1 for x in my_list]
window[[x+1 for x in target_indices]] = 0
window[[x-1 for x in target_indices]] = 0

hamming= np.hamming(RATE)
def zscore(x,mu,sigma):
    return (x-mu)/sigma

def notify_discord(message,image=False):
    webhook = DiscordWebhook(url=URL,content=message)
    if image:
        with open(fig_name, "rb") as f:
            webhook.add_file(file=f.read(), filename=fig_name)
    response = webhook.execute()

def plot_specgram(signal):
    global freq_bins
    plt.clf()
    plt.plot(np.abs(freq_bins),np.abs(signal.real))
    plt.savefig(fig_name)

def handle_event(amplitudes,fft_result,indata):
    global event_start_time, notification_sent, last_event_detection_time
    
    fft_mean = np.abs(np.mean(fft_result[window]).real)
    fft_std = np.abs(np.std(fft_result[window]).real)
    zscores = zscore(amplitudes,fft_mean,fft_std)
    if np.all(zscores >= zscore_thresh): #np.all(amplitudes >= AMPLITUDE_THRESHOLDS) and
        print("Alarm heard")
        print(f"Amplitudes: {amplitudes}")
        print(f"Z Scores: {zscores}")
        print(f"Mean: {fft_mean}, Std: {fft_std}")
        #Handle the event
        if event_start_time is None:
            print("Setting event start")
            event_start_time = datetime.now()
        
        event_duration = datetime.now() - event_start_time
        
        if event_duration >= timedelta(seconds=get_alarm_duration_threshold()):
            print("Event duration threshold met")
            if not notification_sent:
                plot_specgram(indata)
                notify_discord(f"Freezer Alarm Detected - {datetime.now()}",True)
                notification_sent = True
        else:
            notification_sent = False
            
        last_event_detection_time = datetime.now()
    else:
        if last_event_detection_time:
            if datetime.now() - last_event_detection_time >= timedelta(seconds = reset_timer) and notification_sent:
                print("Reset time threshold met. Resetting timers.")
                event_start_time = None
                notification_sent = False
                last_event_detection_time = None
                notify_discord(f"Freezer Alarm Has Stopped - {datetime.now()}")

def audio_callback(indata, frames, time, status):
    indata *= hamming
    fft_result = np.fft.fft(indata)
    amplitudes_of_targets = []
    for idx in target_indices:
        amplitudes_of_targets.append(np.mean(np.abs(fft_result[idx-1:idx+2].real))) #Mean of the absolute value of the target index and its neighboring frequencies
    handle_event(amplitudes_of_targets,fft_result,indata)
        

with sd.InputStream(channels=CHANNELS, 
                    callback=audio_callback,
                    samplerate=RATE,
                    blocksize=RATE,
                    device = device):
    while True:
        pass
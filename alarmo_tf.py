from discord_webhook import DiscordWebhook
from datetime import datetime,timedelta,time
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import tflite_runtime.interpreter as tflite

"""CONSTANTS"""
RATE = 44100
CHANNELS = 1
BLOCK_SIZE = 44032
reset_timer = 20
confidence_thresh = 0.8

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

event_start_time = None
notification_sent = False
last_event_detection_time = None

device = sd.query_devices("USB PnP Sound Device: Audio (hw:1,0)")['index']

model_path = 'soundclassifier_with_metadata.tflite'
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

def notify_discord(message):
    webhook = DiscordWebhook(url=URL,content=message)
    response = webhook.execute()

def handle_event(class_index,confidence):
    global event_start_time, notification_sent, last_event_detection_time
    
    if class_index == 0 and confidence >= confidence_thresh:
        #Handle the event
        
        if event_start_time is None:
            print(f"Setting event start\nPredicted Class: {class_index}, Confidence: {confidence}")
            event_start_time = datetime.now()
        
        event_duration = datetime.now() - event_start_time
        
        if event_duration >= timedelta(seconds=get_alarm_duration_threshold()):
            print("Event duration threshold met")
            if not notification_sent:
                #plot_specgram(indata)
                notify_discord(f"Freezer Alarm Detected - {datetime.now()} - Confidence: {confidence}")
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
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.set_tensor(input_details[0]['index'], indata.transpose())
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    class_index = np.argmax(output_data)
    confidence = output_data[0][class_index]
    handle_event(class_index,confidence)
        
with sd.InputStream(channels=CHANNELS, 
                    callback=audio_callback,
                    samplerate=RATE,
                    blocksize=BLOCK_SIZE,
                    device = device):
    while True:
        pass
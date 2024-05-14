# Alarmo
A simple alarm detector in Python

## Requirements
- [Discord Webhook](https://pypi.org/project/discord-webhook/): `pip install discord_webhook`
- [SoundDevice](https://pypi.org/project/sounddevice/): `pip install sounddevice`
- [PnP USB microphone](https://www.amazon.com/dp/B01MQ2AA0X?psc=1&ref=ppx_yo2ov_dt_b_product_details)

### On a Raspberry Pi
If running on a Raspberry Pi you may also need to install PortAudio
`sudo apt-get install libportaudio2`


## Webhook Setup
1. Right click your Discord server.
2. Click "Server Settings"
3. Go to the "Apps" section and click "Integrations"
4. Click "View Webhooks" in the Webhooks section
5. Click "New Webhook"
6. Open the newly created Webhook. It'll have a cheeky randomly generated name.
7. Rename the webhook "Alarmo" or whatever you want.
8. Set the webhook channel to the channel where you want to receive notifications.
9. Click "Copy Webhook URL"
10. Paste the webhook into the `URL` parameter of `alarmo.py` (line 15)
11. (Optional): Set the webhook icon to the provided alarm icon.


## Parameters
- `TARGET_FREQS`: The alarm frequencies (Hz) to listen for. 
- `AMPLITUDE_THRESHOLDS`: The amplitude of the target frequencies above which Alarmo considers the alarm is going off. Every frequency in `TARGET_FREQS` *must* have its own threshold.
- `RATE`: Sample rate (Hz). 44100 is fine.
- `CHANNELS`: Number of audio channels to use. 1 (mono) is fine
- `BLOCK_SIZE`: Number of audio samples at a time to assay. Just leave this alone
- `alarm_duration_threshold`: Duration (in seconds) the alarm has to be going off before a notification can be sent. Not recommended to set this below 5 seconds.
- `reset_timer`: When the alarm isn't heard for this number of seconds the alert timers are reset
- `URL`: The Discord Webhook URL


## Testing
The default target frequencies and amplitude thresholds are set up to detect the alarm in the included audio sample `Alarm Sample.mp3`.


## Under the hood
Alarmo takes audio input from the microphone and returns samples of length = `BLOCK_SIZE`.
Fast Fourier Transform of the audio data yields amplitudes for n frequencies where n also = `BLOCK_SIZE`
It then indexes into the resulting array, grabbing the average amplitudes for the specific frequencies specified in `TARGET_FREQS` and the frequencies on either side of them. For example if the target frequency was 5000 Hz it'd average the amplitudes of 4999 Hz, 5000 Hz and 5001 Hz. Why do this? Just because you've asked for the amplitude of 5000 Hz doesn't mean the FFT will have returned the amplitude for that specific frequency. It might instead yield the amplitude for 5002 Hz or 4998 Hz depending on how `RATE` and `BLOCK_SIZE` are set. Taking the mean of the amplitude of surrounding frequencies gives us a pretty good approximation of their amplitudes even if the actual frequency bins given by `np.fft.fftfreq` are a little off. Next, the amplitudes are compared to the thresholds specified by `AMPLITUDE_THRESHOLDS`. Only when *all* the amplitudes are above their respective threshold will the alarm be considered "on".

## Acknowledgements
Thanks to [Pierre Dubouilh](https://github.com/pldubouilh) for the [idea](https://github.com/pldubouilh/alarm).
Icon sourced from [here](https://www.iconfinder.com/icons/2542103/alarm_alert_emergency_light_icon).
`Alarm Sample.mp3` provided by [Elijah Kofke](https://www.linkedin.com/in/elijah-kofke-97a61b73/).
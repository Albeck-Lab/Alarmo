import numpy as np
from scipy.io import wavfile

import matplotlib.pyplot as plt

AMPLITUDE_THRESHOLDS = [0.09, 0.06,0.06] #Amplitude of that frequency above which to send notification
RATE = 32000
zscore_thresh = 1


freq_bins = np.fft.rfftfreq(RATE,1/RATE) #FFT frequencies map

TARGET_FREQS = [3175, 6350, 9500] #Frequencies of the alarm tone
target_indices = []
for freq in TARGET_FREQS:
    target_indices.append(np.abs(freq_bins - freq).argmin()) #Index of the target frequency

target_indices = np.array(target_indices)



def zscore(x,mu,sigma):
    return (x-mu)/sigma


hamming = np.hamming(RATE)

_, indata = wavfile.read('Alarm Sample.wav')
nseg = int(len(indata)/RATE)
segs = np.linspace(0,RATE * nseg,nseg+1,dtype=int)
for i in range(len(segs)-1):

    segment = indata[segs[i]:segs[i+1]] #Get the nth segment of 44100 samples (1 second)
    segment *= hamming #Apply hamming window
    fft_result = np.fft.rfft(segment).real #FFT it
    plt.plot(fft_result)
    print(f"{np.abs(fft_result[target_indices])}")
    amplitudes = [] 
    for idx in target_indices:
        amplitudes.append(np.mean(np.abs((fft_result[idx])))) #Mean of the absolute value of the target index and its neighboring frequencies

    fft_mean = np.mean(fft_result)
    fft_std = np.std(fft_result)
    zscores = zscore(amplitudes,fft_mean, fft_std)
    if np.any(zscores > 2):#np.all(amplitudes >= AMPLITUDE_THRESHOLDS):
        print("Alarm heard")
        print(f"Amplitudes: {amplitudes}")
        #Handle the event

#!/usr/bin/env frameworkpython

import pyaudio
import wave
import struct
import math
import matplotlib.pyplot as plt
import numpy as np
import pdb

CHUNK = 1024

class SpeechFinder:
  def __init__(self, fname):
    self.wf = wave.open(fname, 'rb')
    self.p = pyaudio.PyAudio()

    self.width = self.wf.getsampwidth()
    self.format = self.p.get_format_from_width(self.width)
    self.channels = self.wf.getnchannels()
    self.rate = self.wf.getframerate()
    print "rate: %s, width: %s, format: %s, channels: %s" % (self.rate, self.width, self.format, self.channels)
    self.starts = []
    self.stops = []
    self.backgrounds = []
    self.a_decibels = []

  @classmethod
  def rms(cls, data):
    count = len(data)/2
    format = "%dh"%(count)
    shorts = struct.unpack(format, data)
    sum_squares = 0.0
    for sample in shorts:
      n = sample * (1.0/32768)
      sum_squares += n*n
    return math.sqrt(sum_squares / count)

  @classmethod
  def decibels(cls, data):
    return 20 * math.log10(cls.rms(data))

  def markSpeech(self):
    forgetfactor = 2
    threshold = 15

    #stream = self.p.open(format=self.format, channels=self.channels, rate=self.rate, output=True)

    data = self.wf.readframes(CHUNK)
    framenum = 0
    current = self.decibels(data)
    level = current
    background = current
    adjustment = 0.05
    isSpeech = False

    while len(data) > 0:
      self.a_decibels.append(current)
      framenum += len(data)
      time = framenum / (4 * float(self.rate))
      current = self.decibels(data)
      level = ((level * forgetfactor) + current) / (forgetfactor + 1)
      #print level - background, background
      if (current < background):
        background = current
        if isSpeech:
          isSpeech = False
          print "speech stop %s" % time
          self.stops.append(time)
      else:
        background += (current - background) * adjustment
      if (level < background):
        level = background
      if (level - background > threshold):
        if not isSpeech:
          print "speech start %s" % time
          self.starts.append(time)
        isSpeech = True
      #print self.decibels(data)
      #stream.write(data)
      data = self.wf.readframes(CHUNK)
      self.backgrounds.append(background)

    #stream.stop_stream()
    #stream.close()

    self.p.terminate()

  def plotData(self):
    self.wf.rewind()
    signal = self.wf.readframes(-1)
    signal = np.fromstring(signal, 'Int16')
    signal = signal[::2]

    Time = np.linspace(0, len(signal)/float(self.rate), num=len(signal))

    plt.figure(1)
    plt.title('Signal Wave...')
    plt.subplot(211)
    plt.plot(Time, signal)
    plt.subplot(212)
    step = float(len(self.backgrounds)) / len(signal)
    plt.plot(Time, [self.backgrounds[int(i * step)] for i in xrange(len(signal))])
    plt.plot(Time, [self.a_decibels[int(i * step)] for i in xrange(len(signal))])
    plt.show()

sf = SpeechFinder('output.wav')
sf.markSpeech()
sf.plotData()

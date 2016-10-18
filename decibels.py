#!/usr/bin/env python

import pyaudio
import wave
import struct
import math

CHUNK = 1024

class SpeechFinder:
  def __init__(self, fname):
    self.wf = wave.open(fname, 'rb')
    self.p = pyaudio.PyAudio()

    self.width = self.wf.getsampwidth()
    self.format = self.p.get_format_from_width(self.width)
    self.channels = self.wf.getnchannels()
    self.rate = self.wf.getframerate()

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

    stream = self.p.open(format=self.format, channels=self.channels, rate=self.rate, output=True)

    data = self.wf.readframes(CHUNK)
    current = self.decibels(data)
    level = current
    background = current
    adjustment = 0.05
    isSpeech = False

    while len(data) > 0:
      current = self.decibels(data)
      level = ((level * forgetfactor) + current) / (forgetfactor + 1)
      #print level - background, background
      if (current < background):
        background = current
        if isSpeech:
          isSpeech = False
          print "speech stop"
      else:
        background += (current - background) * adjustment
      if (level < background):
        level = background
      if (level - background > threshold):
        if not isSpeech:
          print "speech start"
        isSpeech = True
      #print self.decibels(data)
      stream.write(data)
      data = self.wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()

    self.p.terminate()

sf = SpeechFinder('output.wav')
sf.markSpeech()

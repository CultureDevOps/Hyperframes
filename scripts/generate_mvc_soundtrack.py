#!/usr/bin/env python3
"""Original gentle educational electronic soundtrack for 35s MVC explainer."""
import math,struct,sys,wave
rate=22050;seconds=35;n=rate*seconds;data=[0.0]*n
def note(start,dur,f,vol=.1):
 lo=int(start*rate)
 for j in range(min(int(dur*rate),n-lo)):
  t=j/rate;env=max(0,min(1,t/.045,(dur-t)/.18))
  data[lo+j]+=vol*env*(math.sin(2*math.pi*f*t)+.18*math.sin(4*math.pi*f*t))
chords=[(261.63,329.63,392),(220,261.63,329.63),(174.61,261.63,349.23),(196,293.66,392)]
for beat in range(70):
 t=beat*.5
 chord=chords[(beat//8)%4]
 note(t,.3,chord[0]/2,.06)
 if beat%2==0:
  note(t,.23,chord[beat//2%3]*2,.08)
for t in [0,5,10,14,19,24,30]:
 note(t,.5,880,.1);note(t+.12,.42,1174.66,.08)
peak=max(1,max(abs(x) for x in data))
with wave.open(sys.argv[1],'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
 for i in range(0,n,4096):
  w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,v/peak*.85))*32767)) for v in data[i:i+4096]))

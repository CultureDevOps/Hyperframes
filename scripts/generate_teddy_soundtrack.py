#!/usr/bin/env python3
import wave, math, struct, random, sys
rate=22050;n=rate*10;data=[0.0]*n;random.seed(3)
def note(t,d,f,vol=.22):
 for j in range(int(d*rate)):
  idx=int(t*rate)+j
  if idx>=n:break
  x=j/rate; env=min(1,x/.025,(d-x)/.08)
  data[idx]+=vol*max(0,env)*(math.sin(2*math.pi*f*x)+.22*math.sin(4*math.pi*f*x))
# A cheerful toy-box melody, wave swooshes and a confetti flourish.
for t,f in [(0,392),(.4,494),(.8,587),(1.2,784),(1.8,587),(2.2,659),(2.6,784),(3.2,880),(3.6,784),(4.0,659),(4.4,587),(4.8,784),(5.2,988),(5.6,784),(6.0,880),(6.4,988),(7.1,784),(7.45,988),(7.8,1175),(8.3,988),(8.7,784),(9.1,587)]:
 note(t,.3,f)
for t in [2.4,3.1,3.8,4.5,5.2,5.9]:
 for k in range(10):note(t+k*.015,.035,350+k*48,.012)
for t in [7.0,7.12,7.24,7.36,7.48]:
 note(t,.18,1100,.09)
peak=max(1,max(map(abs,data)))
with wave.open(sys.argv[1],'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
 for i in range(0,n,4096):
  w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,v/peak*.8))*32767)) for v in data[i:i+4096]))

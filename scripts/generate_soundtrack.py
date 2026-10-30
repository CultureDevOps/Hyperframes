#!/usr/bin/env python3
"""Generate original 10-second synth soundtrack, no external audio assets."""
import math, random, struct, wave, sys
RATE=22050
N=RATE*10
audio=[0.0]*N
random.seed(17)
def tone(start,duration,freq,volume=.2,kind='sine',sweep=0):
    lo=int(start*RATE); count=min(int(duration*RATE),N-lo)
    for j in range(max(0,count)):
        t=j/RATE
        f=freq+sweep*t/max(duration,.001)
        phase=2*math.pi*(freq*t+sweep*t*t/(2*max(duration,.001)))
        waveval=math.sin(phase)
        if kind=='square': waveval=math.tanh(waveval*4)
        if kind=='noise': waveval=random.uniform(-1,1)
        attack=min(1,t/.025); release=min(1,(duration-t)/.13)
        audio[lo+j]+=volume*waveval*max(0,min(attack,release))
# Quiet ominous pulse grows faster, then a ridiculous emergency siren.
for k in range(13):
    t=.5+k*.46
    tone(t,.18,85+k*8,.10+k*.007,'square')
    tone(t,.08,400+k*30,.055)
for t in [2.9,3.7,4.4,5.1]:
    tone(t,.16,880,.15,'square',-250)
for k in range(8):
    t=5.45+k*.21
    tone(t,.18,560 if k%2==0 else 760,.21,'square')
# Massive comic impact at 7.15 seconds, then victory fanfare.
tone(7.12,.85,90,.55,'noise')
tone(7.13,1.0,65,.6,'sine',-42)
for i,f in enumerate([392,494,587,784]):
    tone(7.35+i*.22,.42,f,.19,'square')
# Sad descending rollback trombone.
for i,f in enumerate([330,294,247,165]):
    tone(8.7+i*.28,.37,f,.23,'square',-35)
peak=max(1,max(abs(x) for x in audio))
with wave.open(sys.argv[1] if len(sys.argv)>1 else 'soundtrack.wav','wb') as out:
    out.setnchannels(1);out.setsampwidth(2);out.setframerate(RATE)
    for i in range(0,N,4096):
        out.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,v/peak*.84))*32767)) for v in audio[i:i+4096]))

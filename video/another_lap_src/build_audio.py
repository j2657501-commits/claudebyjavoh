import numpy as np, wave, json
w=wave.open('orig_audio.wav');sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2).astype(float)/32768
A,B,END,K=2.9,9.05,12.0,5
a0,b0=int(A*sr),int(B*sr)
mono=x.mean(1)
N=int(0.05*sr);best=(-9,0)
for dlt in range(-int(0.015*sr),int(0.015*sr)):
    p=mono[b0:b0+N];q=mono[a0+dlt:a0+dlt+N]
    c=np.dot(p,q)/np.sqrt(np.dot(p,p)*np.dot(q,q)+1e-12)
    if c>best[0]:best=(c,dlt)
print('corr',best)
a0+=best[1]
XF=int(0.06*sr);fade=np.sin(np.linspace(0,np.pi/2,XF))[:,None]
out=x[:b0].copy();joins=[b0/sr]
segs=[(a0,b0)]*K+[(a0,int(END*sr))]
for s,e in segs:
    tail=x[out.shape[0]-0:0] if False else None
    # crossfade: blend last XF of out with continuation of original after b0, into new segment start
    cont=x[b0:b0+XF] if b0+XF<len(x) else np.zeros((XF,2))
    head=x[s:s+XF]
    out=np.concatenate([out, cont*fade[::-1]+head*fade, x[s+XF:e]])
    joins.append((out.shape[0]-(e-s))/sr)
# fade out last 2.5 s
F=int(2.5*sr);out[-F:]*=np.linspace(1,0,F)[:,None]**1.5
out/=max(1,np.abs(out).max()/0.97)
with wave.open('track.wav','wb') as o:
    o.setnchannels(2);o.setsampwidth(2);o.setframerate(sr);o.writeframes((out*32767).astype('<i2').tobytes())
print('duration',out.shape[0]/sr,'joins',[round(j,3) for j in joins])
json.dump({'dur':out.shape[0]/sr,'joins':joins,'loopStart':A,'loopEnd':B},open('track.json','w'))

import numpy as np, wave, sys

SR = 44100
DUR = 48.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def fft_filter(x, lo=None, hi=None, tilt=0.0):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** 4)
    if lo:
        g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if tilt:
        g *= (np.maximum(f, 20) / 1000) ** tilt
    return np.fft.irfft(X * g, len(x))


def norm(x, peak=1.0):
    return x / (np.max(np.abs(x)) + 1e-9) * peak


def env_adsr(n, a, r):
    e = np.ones(n)
    ai, ri = int(a * SR), int(r * SR)
    e[:ai] = np.linspace(0, 1, ai) ** 2
    e[-ri:] *= np.linspace(1, 0, ri) ** 2
    return e


def reverb(x, secs=3.5, mix=0.45, seed=1):
    r = np.random.default_rng(seed)
    n = int(secs * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR * 6.5 / secs)
    ir = fft_filter(ir, hi=4500)
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[: len(x)]
    return (1 - mix) * x + mix * norm(wet, np.max(np.abs(x)))


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# --- Pad: slow minor progression, 4 chords x 12 s ---
chords = [[45, 52, 57, 60, 64],   # Am
          [41, 48, 53, 57, 60],   # F
          [43, 50, 55, 59, 62],   # G
          [40, 47, 52, 56, 59]]   # E (tension)
pad = np.zeros(N)
seg = 12.0
for i, ch in enumerate(chords):
    s0 = max(0, int((i * seg - 1.5) * SR))
    s1 = min(N, int(((i + 1) * seg + 1.5) * SR))
    tt = t[s0:s1]
    e = env_adsr(s1 - s0, 2.5, 2.5)
    for k, m in enumerate(ch):
        for det in (-0.12, 0.0, 0.11):
            f = midi(m) * (1 + det / 100)
            ph = rng.uniform(0, 2 * np.pi)
            w = np.sin(2 * np.pi * f * tt + ph) + 0.25 * np.sin(4 * np.pi * f * tt + ph)
            pad[s0:s1] += w * e / (1 + k * 0.35)
pad = fft_filter(pad, hi=1400)
pad *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t)
pad = norm(pad, 0.33)

# --- Sub drone (engine idle rumble) ---
sub = np.sin(2 * np.pi * 41.2 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t + 1.0)
rumble = fft_filter(rng.standard_normal(N), lo=25, hi=120)
sub = norm(sub, 1) * 0.6 + norm(rumble, 1) * 0.4
sub *= (0.8 + 0.2 * np.sin(2 * np.pi * 0.37 * t)) * (0.9 + 0.1 * np.sin(2 * np.pi * 7.1 * t))
sub = norm(sub, 0.22)

# --- Wind / fog air ---
wind = fft_filter(rng.standard_normal(N), lo=180, hi=2200, tilt=-0.4)
gust = 0.55 + 0.45 * fft_filter(rng.standard_normal(N), hi=0.25) / 0.002
gust = np.clip(norm(gust - gust.mean(), 0.45) + 0.6, 0.15, 1.1)
wind = norm(wind * gust, 0.13)

# --- Soft pulse (heartbeat-like low kick), starts at 12 s, intensifies ---
pulse = np.zeros(N)
klen = int(0.45 * SR)
kt = np.arange(klen) / SR
kick = np.sin(2 * np.pi * (48 + 60 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 7)
beat = 60 / 70.0
tb = 12.0
while tb < 45.5:
    for off, amp in ((0, 1.0), (0.28, 0.55)):
        i0 = int((tb + off) * SR)
        if i0 + klen < N:
            lvl = amp * (0.45 + 0.55 * min(1, (tb - 12) / 24))
            pulse[i0:i0 + klen] += kick * lvl
    tb += beat * 2
pulse = norm(pulse, 0.42)

# --- Sparse distant piano-ish notes ---
notes = [(3.0, 69), (8.0, 72), (15.0, 76), (20.5, 74), (27.0, 72), (32.0, 69), (38.5, 71), (43.0, 64)]
bell = np.zeros(N)
for st, m in notes:
    i0 = int(st * SR)
    n = int(4 * SR)
    tt = np.arange(n) / SR
    f = midi(m)
    w = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt) + 0.1 * np.sin(2 * np.pi * 3.01 * f * tt))
    w *= np.exp(-tt * 1.4) * (1 - np.exp(-tt * 200))
    bell[i0:i0 + n] += w[: N - i0]
bell = norm(reverb(bell, 4.5, 0.65, 3), 0.17)

mix_mono = pad + sub + pulse
mix_mono = reverb(mix_mono, 2.5, 0.25, 5)

# stereo: decorrelate wind & bells a bit
wind_r = np.roll(wind, int(0.013 * SR))
bell_r = np.roll(bell, int(0.009 * SR))
L = mix_mono + wind + bell
R = mix_mono + wind_r + bell_r

master = env_adsr(N, 2.5, 3.5)
L *= master
R *= master
st = np.stack([L, R], 1)
st = np.tanh(st * 1.4) / np.tanh(1.4)
st = norm(st, 0.89)

out = sys.argv[1]
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
print("wrote", out)

// timeline.js — deterministic physics/timing of the domino chain (shared by the page and node checks).
(function (G) {
  const D2R = Math.PI / 180;
  const R = 20000;                    // toy planet radius (domino h = 1)
  const GROW = 1.45;
  const TYPES = [];
  for (let i = 0; i < 7; i++) TYPES.push("domino");
  TYPES.push("book", "book", "book", "fridge", "booth", "car", "van", "bus", "container", "container", "house");
  for (let i = 0; i < 6; i++) TYPES.push("tower");
  const DIM = { // thickness w (along chain), width b, relative to h
    domino: [0.2, 0.5], book: [0.17, 0.72], fridge: [0.42, 0.5], booth: [0.36, 0.36], car: [0.34, 0.44],
    van: [0.38, 0.4], bus: [0.3, 0.26], container: [0.24, 0.24], house: [0.5, 0.62], tower: [0.2, 0.22],
  };
  const N = TYPES.length;
  const items = [];
  for (let i = 0; i < N; i++) {
    const h = Math.pow(GROW, i), [wk, bk] = DIM[TYPES[i]];
    items.push({ i, type: TYPES[i], h, w: wk * h, b: bk * h, gap: 0.56 * h });
  }
  // front-edge arc positions
  items[0].s = 0;
  for (let i = 0; i + 1 < N; i++) items[i + 1].s = items[i].s + items[i].gap + items[i + 1].w;
  for (const it of items) it.phi = it.s / R;
  const sMax = items[N - 1].s;

  // 2D geometry in the (y,z) plane, planet centre (0,-R)
  const slotO = phi => [R * Math.cos(phi) - R, R * Math.sin(phi)];
  const toWorld = (phi, ly, lz) => { const [oy, oz] = slotO(phi), c = Math.cos(phi), s = Math.sin(phi); return [oy + ly * c - lz * s, oz + ly * s + lz * c]; };
  const toLocal = (phi, wy, wz) => { const [oy, oz] = slotO(phi), c = Math.cos(phi), s = Math.sin(phi), dy = wy - oy, dz = wz - oz; return [dy * c + dz * s, -dy * s + dz * c]; };
  const tipW = (it, th) => toWorld(it.phi, it.h * Math.cos(th), it.h * Math.sin(th));

  // contact angle with the next item's back face, and ground-rest angle
  for (let i = 0; i < N; i++) {
    const it = items[i], nx = items[i + 1];
    let thc = null, thg = 88 * D2R;
    for (let a = 0; a < 89.9; a += 0.05) {
      const th = a * D2R, [wy, wz] = tipW(it, th);
      if (nx && thc === null) { const [ly, lz] = toLocal(nx.phi, wy, wz); if (lz >= -nx.w && ly >= 0 && ly <= nx.h * 1.02) thc = th; }
      if (Math.hypot(wy, wz + 0) > 0 && Math.hypot(wy + R, wz) < R + it.w * 0.5) { thg = th; break; }
    }
    it.thc = thc; it.thg = thg;
    it.thf = nx ? Math.min(thg, Math.max(thc + 25 * D2R, Math.acos(Math.min(0.95, nx.w * 1.05 / it.h)))) : thg;
  }

  // free-fall timing: theta'' = sin(theta)/tau^2 ; tau grows with size (grandeur)
  const T0 = 0.56, TK = 1.088;
  const DT = 1 / 600;
  const START = 0.35;             // finger contact
  let ts = START, kick = 1.9;
  for (let i = 0; i < N; i++) {
    const it = items[i]; it.tau = T0 * Math.pow(TK, i); it.t0 = ts;
    // integrate until contact (or ground for the last one)
    let th = 0.015, om = kick / it.tau; const tab = [th]; const stop = (it.thc != null ? it.thc : it.thg);
    let tc = null;
    for (let k = 0; k < 200000; k++) {
      const f = (x) => Math.sin(x) / (it.tau * it.tau);
      // RK4
      const k1v = f(th), k1x = om, k2v = f(th + k1x * DT / 2), k2x = om + k1v * DT / 2, k3v = f(th + k2x * DT / 2), k3x = om + k2v * DT / 2, k4v = f(th + k3x * DT), k4x = om + k3v * DT;
      th += (k1x + 2 * k2x + 2 * k3x + k4x) * DT / 6; om += (k1v + 2 * k2v + 2 * k3v + k4v) * DT / 6;
      it.moonHit && 0;
      tab.push(th);
      if (th >= stop) { tc = (k + 1) * DT; break; }
    }
    it.tab = tab; it.tc = ts + tc; it.omC = om;
    ts = it.tc; kick = 1.3;
  }
  // last tower: hits the Moon at MOON_TH, slows, then falls to the ground
  const L = items[N - 1];
  const MOON_TH = 46 * D2R;
  { // re-integrate the last one with a moon collision
    let th = 0.015, om = 1.3 / L.tau, tab = [th], hit = null, k = 0;
    for (; k < 400000; k++) {
      const a = Math.sin(th) / (L.tau * L.tau); om += a * DT; th += om * DT;
      if (hit === null && th >= MOON_TH) { hit = (k + 1) * DT; om *= 0.42; }
      tab.push(Math.min(th, L.thg)); if (th >= L.thg) break;
    }
    L.tab = tab; L.tHit = L.t0 + hit; L.tc = L.t0 + (k + 1) * DT;
  }
  const moonR = 0.3 * L.h;
  const [hy, hz] = tipW(L, MOON_TH);
  // moon centre: just beyond the tip along the swing direction
  const sw = [-Math.sin(L.phi + MOON_TH), Math.cos(L.phi + MOON_TH)]; // direction of tip motion (perp to tower)
  const MOON0 = [hy + sw[0] * moonR * 0.98 + 0, hz + sw[1] * moonR * 0.98];
  const T_CRASH = L.tHit + 2.6;
  const CRASH_PHI = L.phi + 0.62;
  const T_END = 30;
  // reset wave: from crash back to the start, logarithmic in arc length
  const T_W0 = T_CRASH + 0.35, T_W1 = 28.75;
  const sCr = CRASH_PHI * R;
  const lg = s => Math.log(s + 2);
  const waveS = t => { const u = Math.min(1, Math.max(0, (t - T_W0) / (T_W1 - T_W0))); const e = 1 - Math.pow(1 - u, 1.6); return Math.exp(lg(sCr) + (lg(0) - lg(sCr)) * e) - 2; };
  const waveT = s => { // inverse of waveS
    const target = (lg(s) - lg(sCr)) / (lg(0) - lg(sCr)); const e = Math.min(1, Math.max(0, target)); const u = 1 - Math.pow(1 - e, 1 / 1.6); return T_W0 + u * (T_W1 - T_W0); };
  for (const it of items) it.tr = waveT(it.s - it.w * 0.5);

  function freeTh(it, t) {
    const x = (t - it.t0) / DT; if (x <= 0) return 0; const k = Math.floor(x), tab = it.tab;
    if (k >= tab.length - 1) return tab[tab.length - 1];
    return tab[k] + (tab[k + 1] - tab[k]) * (x - k);
  }
  const memo = new Map();
  function fallTh(i, t) { // without reset
    const key = i; if (memo.has(key)) return memo.get(key);
    const it = items[i]; let th;
    if (i === N - 1) th = freeTh(it, t);
    else if (t < it.tc) th = freeTh(it, t);
    else { const nx = items[i + 1], q = Math.min(1, fallTh(i + 1, t) / nx.thf); th = it.thc + (it.thf - it.thc) * (1 - Math.pow(1 - q, 1.4)); }
    memo.set(key, th); return th;
  }
  function theta(i, t) { // full state incl. reset wave (springs back up with a wobble)
    const it = items[i]; let th = fallTh(i, t);
    if (t > it.tr) {
      const thr = fallTh(i, it.tr), sc = 0.42 * Math.pow(1.06, i), u = (t - it.tr) / sc;
      const k = 5.2, w = 9.5; th = thr * Math.exp(-k * u) * (Math.cos(w * u) + (k / w) * Math.sin(w * u));
    }
    return th;
  }
  function frame(t) { memo.clear(); const th = []; for (let i = N - 1; i >= 0; i--) th[i] = theta(i, t); return th; }
  G.TL = { R, items, N, frame, tipW, toWorld, slotO, MOON0, moonR, MOON_TH, T_CRASH, CRASH_PHI, T_W0, T_W1, waveS, waveT, START, T_END, sMax, D2R, L };
})(typeof window !== "undefined" ? window : globalThis);

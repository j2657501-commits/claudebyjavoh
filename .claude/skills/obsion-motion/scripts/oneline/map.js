/* map.js — paper maps for the line. Data comes as JS globals (window.GEO_*), never fetched (file:// safe).
 *   const M = MAP.make({ cx: 15, cy: 52, scale: 52, ox: 20000, oy: 600 });   // lon/lat centre → world origin; px per degree
 *   M.p(lon, lat) → [x, y];  M.d(geometry) → SVG path d;  M.line([[lon,lat],...]) → d (smooth)
 *   MAP.tear(g, pts, t0, t1, opts) → a paper tear that opens along pts (world coords) between t0..t1
 *   MAP.hatch(g, polygonD, opts) → pencil hatching inside a polygon (clip), revealed left→right
 */
(function (G) {
  const { el, EASE, prog, clamp, mul, on } = G.E;
  function make(o) {
    const k = Math.cos((o.lat0 || o.cy) * Math.PI / 180), S = o.scale;
    const p = (lon, lat) => [o.ox + (lon - o.cx) * S * k, o.oy - (lat - o.cy) * S];
    const ring = r => r.map(([lo, la], i) => (i ? "L" : "M") + p(lo, la).map(v => v.toFixed(1)).join(" ")).join("") + "Z";
    const d = gm => {
      if (!gm) return "";
      if (gm.type === "Polygon") return gm.coordinates.map(ring).join("");
      if (gm.type === "MultiPolygon") return gm.coordinates.map(pg => pg.map(ring).join("")).join("");
      if (gm.type === "LineString") return gm.coordinates.map(([lo, la], i) => (i ? "L" : "M") + p(lo, la).map(v => v.toFixed(1)).join(" ")).join("");
      if (gm.type === "MultiLineString") return gm.coordinates.map(c => d({ type: "LineString", coordinates: c })).join("");
      return "";
    };
    const line = (pts) => smooth(pts.map(([lo, la]) => p(lo, la)));
    return { p, d, line, k, S, o };
  }
  // Catmull-Rom → cubic Bézier through world points
  function smooth(Q) {
    let s = `M${Q[0][0].toFixed(1)} ${Q[0][1].toFixed(1)}`;
    for (let i = 0; i < Q.length - 1; i++) {
      const p0 = Q[i - 1] || Q[i], p1 = Q[i], p2 = Q[i + 1], p3 = Q[i + 2] || p2;
      s += `C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)} ${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)} ${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)} ${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
    }
    return s;
  }
  // resample a polyline to equal steps
  function resample(pts, step) {
    const out = [pts[0]]; let acc = 0;
    for (let i = 1; i < pts.length; i++) {
      const [ax, ay] = pts[i - 1], [bx, by] = pts[i], L = Math.hypot(bx - ax, by - ay);
      let s = step - acc;
      while (s <= L) { out.push([ax + (bx - ax) * s / L, ay + (by - ay) * s / L]); s += step; }
      acc = (acc + L) % step;
    }
    out.push(pts[pts.length - 1]); return out;
  }
  // a paper tear along a polyline: dark gap with jagged lips, opens progressively and widens
  function tear(g, pts, t0, t1, o) {
    o = o || {}; const R = mul(o.seed || 9), P = resample(pts, 14), N = P.length, wMax = o.w || 26;
    const jag = P.map(() => [R() * 0.8 + 0.4, R() * 0.8 + 0.4]);
    const gap = el("path", { fill: o.dark || "#1F1E1D" }, g), lipA = el("path", { fill: "none", stroke: "#FFFDF7", "stroke-width": 3, "stroke-linejoin": "round" }, g), lipB = el("path", { fill: "none", stroke: "#FFFDF7", "stroke-width": 3 }, g);
    on(t => {
      const q = EASE.io2(prog(t, t0, t1)), n = Math.max(2, Math.floor(q * N)); const vis = t >= t0;
      gap.style.display = lipA.style.display = lipB.style.display = vis ? "" : "none"; if (!vis) return;
      const widen = 0.35 + 0.65 * EASE.o(prog(t, t0, t1 + (o.settle || 1.5)));
      const A = [], B = [];
      for (let i = 0; i < n; i++) {
        const [x, y] = P[i], [x2, y2] = P[Math.min(N - 1, i + 1)], ang = Math.atan2(y2 - y, x2 - x) + Math.PI / 2;
        const head = clamp((n - i) / 6), w = wMax * widen * head;
        A.push([x + Math.cos(ang) * w * jag[i][0], y + Math.sin(ang) * w * jag[i][0]]); B.push([x - Math.cos(ang) * w * jag[i][1], y - Math.sin(ang) * w * jag[i][1]]);
      }
      const f = a => a.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join("");
      gap.setAttribute("d", f(A) + B.slice().reverse().map(p => "L" + p[0].toFixed(1) + " " + p[1].toFixed(1)).join("") + "Z");
      lipA.setAttribute("d", f(A)); lipB.setAttribute("d", f(B));
    });
    return { P };
  }
  // pencil hatching inside polygon d: parallel strokes at angle, clipped, revealed by sweep
  function hatch(g, d, o) {
    o = o || {}; const id = "h" + Math.random().toString(36).slice(2, 8), cp = el("clipPath", { id }, G.E.defs); el("path", { d }, cp);
    const gg = el("g", { "clip-path": `url(#${id})` }, g), R = mul(o.seed || 2), b = o.box, gapp = o.gap || 9, ang = (o.angle || -35) * Math.PI / 180;
    let s = ""; const diag = Math.hypot(b[2], b[3]);
    for (let k = -diag; k < diag; k += gapp) {
      const cx = b[0] + b[2] / 2 + Math.cos(ang + Math.PI / 2) * k, cy = b[1] + b[3] / 2 + Math.sin(ang + Math.PI / 2) * k, j = (R() - .5) * 4;
      s += `M${(cx - Math.cos(ang) * diag + j).toFixed(1)} ${(cy - Math.sin(ang) * diag).toFixed(1)}L${(cx + Math.cos(ang) * diag).toFixed(1)} ${(cy + Math.sin(ang) * diag + j).toFixed(1)}`;
    }
    const hp = el("path", { d: s, stroke: o.color || "var(--olive)", "stroke-width": o.w || 2.2, opacity: o.op || 0.55, fill: "none", "stroke-linecap": "round" }, gg);
    if (o.t0 != null) {
      const rid = "r" + id, cp2 = el("clipPath", { id: rid }, G.E.defs), rr = el("rect", { x: b[0], y: b[1] - 50, width: 0, height: b[3] + 100 }, cp2);
      hp.setAttribute("clip-path", `url(#${rid})`);
      on(t => { const q = EASE.io2(prog(t, o.t0, o.t1 || o.t0 + 1.2)); rr.setAttribute("width", (b[2] * q).toFixed(1)); gg.style.opacity = 1 - EASE.io2(prog(t, o.out || 1e9, (o.out || 1e9) + .6)); });
    }
    return gg;
  }
  G.MAP = { make, smooth, resample, tear, hatch };
})(window);

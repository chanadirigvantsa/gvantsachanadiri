// "The Prize Call": a short 3D cartoon. Everything is driven by renderAt(t),
// so playback and frame-by-frame export show exactly the same picture.
import * as THREE from './vendor/three.module.min.js';
import { M, LINES, FPS } from './timeline.js';

export const W = 1920, H = 1080;
export const DURATION = M.end;

// ---------------------------------------------------------------- helpers
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const smooth = k => { k = clamp(k); return k * k * (3 - 2 * k); };
const seg = (t, a, b) => smooth((t - a) / (b - a));
const backOut = k => { k = clamp(k); const c = 2.2; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);
function track(t, keys) { // keys: [[time, value], ...] smooth between neighbours
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t < keys[i][0]) {
    const [t0, a] = keys[i - 1], [t1, b] = keys[i], k = smooth((t - t0) / (t1 - t0));
    return typeof a === 'number' ? lerp(a, b, k) : lerpV(a, b, k);
  }
  return keys[keys.length - 1][1];
}
function rng(seed) { return () => ((seed = (seed * 16807) % 2147483647) / 2147483647); }

const gradient = (() => {
  const d = new Uint8Array([90, 170, 255]);
  const tex = new THREE.DataTexture(d, 3, 1, THREE.RedFormat);
  tex.minFilter = tex.magFilter = THREE.NearestFilter; tex.needsUpdate = true;
  return tex;
})();
const matCache = new Map();
function toon(color, extra = {}) {
  const key = color + JSON.stringify(extra);
  if (!extra.map && matCache.has(key)) return matCache.get(key);
  const m = new THREE.MeshToonMaterial({ color, gradientMap: gradient, ...extra });
  if (!extra.map) matCache.set(key, m);
  return m;
}
const flat = (color, extra = {}) => new THREE.MeshBasicMaterial({ color, ...extra });
const outlineMat = new THREE.MeshBasicMaterial({ color: 0x2a1a14, side: THREE.BackSide });

function mesh(geo, mat, opts = {}) {
  const m = new THREE.Mesh(geo, typeof mat === 'number' ? toon(mat) : mat);
  m.castShadow = opts.cast !== false; m.receiveShadow = opts.receive !== false;
  if (opts.outline) {
    const o = new THREE.Mesh(geo, outlineMat);
    o.scale.setScalar(1 + opts.outline); o.castShadow = false; o.receiveShadow = false;
    m.add(o);
  }
  return m;
}
const sph = (r, c, o) => mesh(new THREE.SphereGeometry(r, 32, 20), c, o);
const cyl = (rt, rb, h, c, o) => mesh(new THREE.CylinderGeometry(rt, rb, h, 28), c, o);
const box = (w, h, d, c, o) => mesh(new THREE.BoxGeometry(w, h, d), c, o);
const cap = (r, len, c, o) => mesh(new THREE.CapsuleGeometry(r, len, 8, 20), c, o);
function at(obj, x, y, z, parent) { obj.position.set(x, y, z); if (parent) parent.add(obj); return obj; }
function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}
const KA = '"Noto Sans Georgian", "DejaVu Sans", sans-serif';

// ---------------------------------------------------------------- renderer
export const canvas = document.createElement('canvas');
canvas.width = W; canvas.height = H;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 100);

// ---------------------------------------------------------------- characters
// A chunky cartoon person with a rig the timeline can pose: IK arms, FK legs,
// face controls (eyes, lids, brows, mouth) and a squash-and-stretch root.
function makePerson(o) {
  const P = { o };
  P.root = new THREE.Group();
  P.body = at(new THREE.Group(), 0, 0, 0, P.root); // squash/stretch pivot at feet
  P.hips = at(new THREE.Group(), 0, 0.56, 0, P.body);
  const ol = { outline: 0.03 };

  // legs
  P.legs = [1, -1].map(s => {
    const thigh = at(new THREE.Group(), s * 0.11, -0.02, 0, P.hips);
    at(cap(0.075, 0.2, o.legs, ol), 0, -0.14, 0, thigh);
    const knee = at(new THREE.Group(), 0, -0.28, 0, thigh);
    at(cap(0.062, 0.2, o.legs, ol), 0, -0.13, 0, knee);
    const foot = at(new THREE.Group(), 0, -0.27, 0, knee);
    const shoe = at(sph(0.085, o.shoes, ol), 0, -0.01, 0.05, foot); shoe.scale.set(1, 0.55, 1.6);
    if (o.pompom) at(sph(0.04, o.pompom), 0, 0.04, 0.15, foot);
    return { thigh, knee, foot, s };
  });

  // skirt / trousers top + torso
  if (o.skirt) { const sk = at(cyl(0.2, 0.32, 0.3, o.skirt, ol), 0, -0.1, 0, P.hips); }
  P.spine = at(new THREE.Group(), 0, 0.04, 0, P.hips);
  const torso = at(sph(0.27, o.top, ol), 0, 0.22, 0, P.spine); torso.scale.set(1, 1.18, 0.82);
  if (o.cardigan) {
    // open cardigan over the dress: two front panels and buttons
    const front = at(sph(0.255, o.dress, { outline: 0 }), 0, 0.24, 0.035, P.spine); front.scale.set(0.42, 1.08, 0.82);
    for (let i = 0; i < 3; i++) at(sph(0.018, 0xf3d36b), 0.075, 0.13 + i * 0.1, 0.215 - Math.abs(i - 1) * 0.004, P.spine);
    P.pocket = at(box(0.11, 0.08, 0.02, o.top), -0.15, 0.08, 0.19, P.spine);
    P.pocket.rotation.y = -0.4;
  }
  if (o.chain) { const ch = at(mesh(new THREE.TorusGeometry(0.13, 0.014, 8, 32), 0xf5c542), 0, 0.38, 0.13, P.spine); ch.rotation.x = 1.25; }
  if (o.collar) { const c = at(cyl(0.16, 0.2, 0.08, o.collar, ol), 0, 0.5, 0, P.spine); }
  P.chest = at(new THREE.Group(), 0, 0.46, 0, P.spine);
  at(cyl(0.07, 0.08, 0.12, o.skin), 0, 0.04, 0, P.chest);

  // head
  P.neck = at(new THREE.Group(), 0, 0.08, 0, P.chest);
  P.head = at(new THREE.Group(), 0, 0.27, 0, P.neck);
  const skull = at(sph(0.3, o.skin, ol), 0, 0, 0, P.head); skull.scale.set(1, 0.98, 0.95);
  [1, -1].forEach(s => {
    at(sph(0.06, o.skin, ol), s * 0.29, -0.01, -0.01, P.head).scale.set(0.6, 1, 1);
    if (o.earrings) at(mesh(new THREE.TorusGeometry(0.03, 0.008, 8, 20), 0xf5c542), s * 0.3, -0.09, 0.0, P.head);
  });
  const nose = at(sph(o.nose || 0.05, o.noseColor || o.skin, ol), 0, -0.03, 0.29, P.head); nose.scale.set(1, 0.9, 0.9);
  if (o.blush) [1, -1].forEach(s => {
    const b = at(mesh(new THREE.CircleGeometry(0.05, 24), flat(o.blush, { transparent: true, opacity: 0.55 })), s * 0.17, -0.07, 0.245, P.head);
    b.rotation.y = s * 0.6; b.rotation.x = 0.25;
  });

  // eyes
  P.eyes = [1, -1].map(s => {
    const g = at(new THREE.Group(), s * 0.105, 0.04, 0.235, P.head);
    g.rotation.y = s * 0.28;
    g.scale.set(1, 1.18, 0.6);
    at(sph(0.078, 0xffffff), 0, 0, 0, g);
    const pupil = at(new THREE.Group(), 0, 0, 0.068, g);
    at(sph(0.043, 0x2b1a12, { cast: false }), 0, 0, 0, pupil).scale.set(1, 1, 0.45);
    at(sph(0.014, 0xffffff, { cast: false }), 0.014, 0.016, 0.02, pupil);
    const star = at(mesh(starGeo(0.055, 0.024), flat(0xffd52e)), 0, 0, 0.03, g);
    star.visible = false;
    const lid = at(mesh(new THREE.SphereGeometry(0.085, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), o.skin), 0, 0, 0, g);
    const lidLow = at(mesh(new THREE.SphereGeometry(0.084, 24, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), o.skin), 0, 0, 0, g);
    const brow = at(box(0.11, 0.024, 0.03, o.brows || 0x3a2418), s * 0.105, 0.17, 0.262, P.head);
    if (o.lashes) at(box(0.12, 0.012, 0.012, 0x2a1a14), 0, 0.085, 0.01, lid).rotation.x = 0.0;
    return { g, pupil, star, lid, lidLow, brow, s };
  });
  if (o.shades) {
    const sh = at(new THREE.Group(), 0, 0.05, 0.27, P.head);
    [1, -1].forEach(s => {
      const lens = at(cyl(0.085, 0.085, 0.02, toon(0x111118, { emissive: 0x0d0d22 }), { outline: 0.06 }), s * 0.11, 0, 0, sh);
      lens.rotation.x = Math.PI / 2; lens.rotation.z = 0; lens.scale.set(1.15, 1, 0.8); lens.rotation.y = s * 0.25;
      const glint = at(mesh(new THREE.PlaneGeometry(0.03, 0.09), flat(0xffffff, { transparent: true, opacity: 0.7 })), s * 0.11 + 0.03, 0.01, 0.015, sh);
      glint.rotation.z = -0.6;
    });
    at(box(0.06, 0.018, 0.02, 0x111118), 0, 0.02, 0, sh);
    P.shades = sh;
  }

  // mouth: dark cavity + teeth + tongue, and a lip arc that bends for smile/frown
  P.mouth = at(new THREE.Group(), 0, -0.135, 0.258, P.head);
  P.mouth.rotation.x = 0.45;
  P.cavity = at(mesh(new THREE.CircleGeometry(1, 32), flat(0x5a1414)), 0, 0, 0.006, P.mouth);
  P.teeth = at(mesh(new THREE.PlaneGeometry(1, 1), flat(0xffffff)), 0, 0, 0.008, P.mouth);
  P.tongue = at(mesh(new THREE.CircleGeometry(1, 24), flat(0xd8636a)), 0, 0, 0.007, P.mouth);
  if (o.goldTooth) P.gold = at(mesh(new THREE.PlaneGeometry(1, 1), flat(0xf5c542)), 0, 0, 0.009, P.mouth);
  P.lip = at(mesh(new THREE.TorusGeometry(0.075, 0.013, 8, 24, Math.PI), flat(o.lipColor || 0x6b2a22)), 0, 0, 0.01, P.mouth);
  P.lip.rotation.z = Math.PI;
  if (o.mustache) {
    P.stache = at(new THREE.Group(), 0, -0.085, 0.285, P.head);
    [1, -1].forEach(s => {
      const m = at(sph(0.055, 0x1c1410, { outline: 0.04 }), s * 0.055, 0, 0, P.stache);
      m.scale.set(1.5, 0.55, 0.6); m.rotation.z = s * -0.35;
    });
  }

  // hair
  if (o.hair === 'bun') {
    const hc = at(mesh(new THREE.SphereGeometry(0.318, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.52), o.hairColor, ol), 0, 0.0, -0.02, P.head);
    hc.rotation.x = -0.42;
    at(sph(0.15, o.hairColor, ol), 0, 0.3, -0.16, P.head);
    const band = at(mesh(new THREE.TorusGeometry(0.1, 0.025, 8, 24), 0xc0392b), 0, 0.27, -0.12, P.head); band.rotation.x = 1.0;
    [1, -1].forEach(s => { const sd = at(sph(0.09, o.hairColor, ol), s * 0.26, 0.06, -0.06, P.head); sd.scale.set(0.6, 1.3, 1); });
    // grey streak
    const st = at(mesh(new THREE.SphereGeometry(0.321, 16, 8, -0.15, 0.3, 0.18, 0.5), 0xd9d4cc), 0, 0, -0.02, P.head); st.rotation.x = -0.42;
  }
  if (o.hair === 'cap') {
    const c = at(mesh(new THREE.SphereGeometry(0.32, 32, 12, 0, Math.PI * 2, 0, Math.PI * 0.42), o.capColor, ol), 0, 0.03, -0.01, P.head);
    c.scale.set(1.05, 0.8, 1.08); c.rotation.x = -0.15;
    const brim = at(cyl(0.2, 0.22, 0.03, o.capColor, ol), 0, 0.17, 0.22, P.head); brim.scale.set(1.1, 1, 0.55); brim.rotation.x = 0.35;
    [1, -1].forEach(s => { const sb = at(sph(0.08, 0x1c1410), s * 0.27, 0.0, -0.08, P.head); sb.scale.set(0.5, 1, 1.2); });
  }

  // arms (two-bone IK; hand targets are given in chest space)
  P.arms = [1, -1].map(s => {
    const sh = at(new THREE.Group(), s * 0.27, -0.04, 0, P.chest);
    at(sph(0.085, o.sleeve, ol), 0, 0, 0, sh);
    at(cap(0.07, 0.12, o.sleeve, ol), 0, -0.11, 0, sh);
    const el = at(new THREE.Group(), 0, -0.24, 0, sh);
    at(cap(0.06, 0.12, o.forearm || o.sleeve, ol), 0, -0.1, 0, el);
    const hand = at(new THREE.Group(), 0, -0.22, 0, el);
    const palm = at(sph(0.068, o.skin, ol), 0, -0.02, 0, hand); palm.scale.set(1, 1.05, 0.8);
    const thumb = at(sph(0.03, o.skin, ol), -s * 0.05, -0.0, 0.03, hand); thumb.scale.set(1, 1.4, 1);
    if (o.cuff) at(cyl(0.07, 0.07, 0.04, o.cuff), 0, 0.02, 0, hand);
    return { sh, el, hand, s, a: 0.24, b: 0.22 };
  });
  return P;
}

function starGeo(R, r) {
  const s = new THREE.Shape();
  for (let i = 0; i < 10; i++) {
    const a = Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r : R;
    i ? s.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : s.moveTo(Math.cos(a) * rr, Math.sin(a) * rr);
  }
  return new THREE.ShapeGeometry(s);
}

const _d = new THREE.Vector3(), _p = new THREE.Vector3(), _u = new THREE.Vector3(), _f = new THREE.Vector3(),
  _x = new THREE.Vector3(), _y = new THREE.Vector3(), _z = new THREE.Vector3(), _e = new THREE.Vector3(), _m = new THREE.Matrix4();
function solveArm(arm, target, pole) {
  const { sh, el, a, b } = arm;
  _d.copy(target).sub(sh.position);
  const L = clamp(_d.length(), 0.05, a + b - 0.002);
  _d.normalize();
  const alpha = Math.acos(clamp((a * a + L * L - b * b) / (2 * a * L), -1, 1));
  const beta = Math.acos(clamp((a * a + b * b - L * L) / (2 * a * b), -1, 1));
  _p.copy(pole).addScaledVector(_d, -pole.dot(_d)).normalize();
  _u.copy(_d).multiplyScalar(Math.cos(alpha)).addScaledVector(_p, Math.sin(alpha));
  _e.copy(sh.position).addScaledVector(_u, a);
  _f.copy(sh.position).addScaledVector(_d, L).sub(_e).normalize();
  _y.copy(_u).negate();
  _z.copy(_f).addScaledVector(_u, -_f.dot(_u));
  if (_z.lengthSq() < 1e-6) _z.copy(_p).negate();
  _z.normalize();
  _x.crossVectors(_y, _z).normalize();
  _m.makeBasis(_x, _y, _z);
  sh.quaternion.setFromRotationMatrix(_m);
  el.rotation.set(-(Math.PI - beta), 0, 0);
}

// default face state
const FACE = { eye: 1, pupil: 1, lid: 0.15, lidLow: 0, brow: 0, browTilt: 0, smile: 0.4, open: 0, wide: 1, lookX: 0, lookY: 0, stars: 0 };
function poseFace(P, f) {
  f = { ...FACE, ...f };
  for (const e of P.eyes) {
    e.g.scale.set(f.eye, 1.18 * f.eye, 0.6);
    e.pupil.scale.setScalar(f.pupil);
    e.pupil.position.set(f.lookX * 0.03, f.lookY * 0.03, 0.068);
    e.pupil.visible = f.stars < 0.5;
    e.star.visible = f.stars >= 0.5;
    e.star.scale.setScalar(0.8 + 0.3 * Math.sin(f.t * 12));
    e.star.rotation.z = f.t * 2;
    e.lid.rotation.x = lerp(-0.55, 1.62, f.lid);
    e.lidLow.rotation.x = lerp(0.35, -0.6, f.lidLow);
    e.brow.position.y = 0.17 + f.brow * 0.05 + (f.eye - 1) * 0.08;
    e.brow.rotation.z = e.s * f.browTilt * 0.5;
  }
  const open = clamp(f.open, 0, 1.4);
  const w = 0.06 * f.wide * (1 + 0.25 * Math.max(0, f.smile)) * (1 - 0.15 * open);
  const h = 0.008 + open * 0.065;
  const cy = -h * 0.9 + 0.01 * Math.max(0, f.smile);
  P.cavity.scale.set(w, h, 1); P.cavity.position.y = cy;
  P.cavity.visible = open > 0.04;
  P.teeth.visible = P.tongue.visible = open > 0.12;
  P.teeth.scale.set(w * 1.5, Math.min(h * 0.45, 0.022), 1); P.teeth.position.y = cy + h - Math.min(h * 0.45, 0.022) / 2 - 0.003;
  P.tongue.scale.set(w * 0.6, h * 0.35, 1); P.tongue.position.y = cy - h * 0.55;
  if (P.gold) { P.gold.visible = open > 0.12; P.gold.scale.set(0.016, Math.min(h * 0.45, 0.022) * 0.95, 1); P.gold.position.set(w * 0.35, P.teeth.position.y, 0.009); }
  P.lip.scale.set(w / 0.075 * 1.05, f.smile * (1 - 0.5 * clamp(open)) + (f.smile >= 0 ? 0.02 : -0.02), 1);
  P.lip.position.y = cy + h * 0.15 + 0.012 * Math.max(0, f.smile);
}

// ---------------------------------------------------------------- the apartment
const home = new THREE.Group(); scene.add(home);
const RNG = rng(42);

const wallpaper = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#f4dcb0'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#ebcb98';
  for (let x = 0; x < w; x += 64) g.fillRect(x, 0, 22, h);
  g.fillStyle = '#d99a5b';
  for (let y = 32; y < h; y += 96) for (let x = 43; x < w; x += 128) {
    g.beginPath(); g.arc(x, y, 7, 0, 7); g.fill();
    g.beginPath(); g.arc(x + 64, y + 48, 7, 0, 7); g.fill();
  }
});
wallpaper.wrapS = wallpaper.wrapT = THREE.RepeatWrapping; wallpaper.repeat.set(4, 2);
const parquet = canvasTex(512, 512, (g, w, h) => {
  const r = rng(5);
  for (let y = 0; y < h; y += 32) for (let x = 0; x < w; x += 128) {
    const off = (y / 32) % 2 ? 64 : 0, v = 150 + r() * 40;
    g.fillStyle = `rgb(${v + 25},${v - 25},${v - 75})`;
    g.fillRect(x + off - 128, y, 126, 30); g.fillRect(x + off, y, 126, 30);
  }
});
parquet.wrapS = parquet.wrapT = THREE.RepeatWrapping; parquet.repeat.set(3, 3);

const floor = at(mesh(new THREE.PlaneGeometry(9, 8), toon(0xffffff, { map: parquet }), { cast: false }), 0, 0, 0.5, home);
floor.rotation.x = -Math.PI / 2;
const backWall = at(mesh(new THREE.PlaneGeometry(9, 3.4), toon(0xffffff, { map: wallpaper }), { cast: false }), 0, 1.7, -3, home);
const leftWall = at(mesh(new THREE.PlaneGeometry(8, 3.4), toon(0xffffff, { map: wallpaper }), { cast: false }), -4.5, 1.7, 0.5, home);
leftWall.rotation.y = Math.PI / 2;
const rightWall = at(mesh(new THREE.PlaneGeometry(8, 3.4), toon(0xffffff, { map: wallpaper }), { cast: false }), 4.5, 1.7, 0.5, home);
rightWall.rotation.y = -Math.PI / 2;
at(box(9, 0.12, 0.04, 0x8a5a33), 0, 0.06, -2.98, home);
at(box(0.04, 0.12, 8, 0x8a5a33), -4.48, 0.06, 0.5, home);

// Caucasian carpet on the wall above the sofa
const carpetTex = canvasTex(600, 400, (g, w, h) => {
  g.fillStyle = '#8f1d1d'; g.fillRect(0, 0, w, h);
  g.strokeStyle = '#e9c46a'; g.lineWidth = 16; g.strokeRect(16, 16, w - 32, h - 32);
  g.strokeStyle = '#1d3557'; g.lineWidth = 10; g.strokeRect(40, 40, w - 80, h - 80);
  g.fillStyle = '#f1e3c4';
  for (let x = 30; x < w; x += 36) { g.beginPath(); g.moveTo(x, 16); g.lineTo(x + 9, 26); g.lineTo(x, 36); g.lineTo(x - 9, 26); g.fill(); }
  const med = (cx, cy, s, c1, c2) => {
    g.fillStyle = c1; g.beginPath(); g.moveTo(cx, cy - s); g.lineTo(cx + s * 1.2, cy); g.lineTo(cx, cy + s); g.lineTo(cx - s * 1.2, cy); g.fill();
    g.fillStyle = c2; g.beginPath(); g.moveTo(cx, cy - s * 0.55); g.lineTo(cx + s * 0.66, cy); g.lineTo(cx, cy + s * 0.55); g.lineTo(cx - s * 0.66, cy); g.fill();
    g.fillStyle = '#f1e3c4'; g.fillRect(cx - s * 0.12, cy - s * 0.12, s * 0.24, s * 0.24);
  };
  med(w / 2, h / 2, 110, '#1d3557', '#e9c46a');
  med(w / 2 - 190, h / 2, 60, '#2a9d8f', '#8f1d1d');
  med(w / 2 + 190, h / 2, 60, '#2a9d8f', '#8f1d1d');
  g.fillStyle = '#e9c46a';
  for (const [x, y] of [[90, 90], [w - 90, 90], [90, h - 90], [w - 90, h - 90]]) { g.beginPath(); g.arc(x, y, 18, 0, 7); g.fill(); }
});
at(mesh(new THREE.PlaneGeometry(2.6, 1.7), toon(0xffffff, { map: carpetTex }), { cast: false }), 0, 1.95, -2.97, home);

// window with grapevine outside
const windowTex = canvasTex(256, 320, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#7ec8f0'); gr.addColorStop(1, '#cdeffd');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  g.fillStyle = '#c9a27c'; g.fillRect(0, h * 0.7, w, h * 0.3);
  const r = rng(9);
  for (let i = 0; i < 40; i++) {
    g.fillStyle = ['#4f9d3a', '#3d8a2c', '#69b04a'][i % 3];
    const x = r() * w, y = r() * h * 0.45;
    g.beginPath(); g.arc(x, y, 14 + r() * 10, 0, 7); g.fill();
  }
  g.fillStyle = '#5b2a6e';
  for (let i = 0; i < 3; i++) for (let k = 0; k < 9; k++) { g.beginPath(); g.arc(50 + i * 75 + (k % 3) * 7, 70 + Math.floor(k / 3) * 9, 5, 0, 7); g.fill(); }
});
const win = at(new THREE.Group(), -2.8, 1.75, -2.97, home);
at(mesh(new THREE.PlaneGeometry(1.1, 1.35), flat(0xffffff, { map: windowTex })), 0, 0, 0.01, win);
for (const [x, y, w, h] of [[0, 0.7, 1.25, 0.08], [0, -0.7, 1.35, 0.1], [-0.59, 0, 0.08, 1.4], [0.59, 0, 0.08, 1.4], [0, 0, 0.05, 1.35], [0, 0.1, 1.1, 0.05]])
  at(box(w, h, 0.06, 0xfaf3e6), x, y, 0.03, win);
for (const s of [-1, 1]) { const c = at(box(0.35, 1.7, 0.04, 0xd4566a), s * 0.82, 0.05, 0.06, win); }

// sofa
const sofa = at(new THREE.Group(), 0, 0, -2.35, home);
const sofaC = 0x2f7f86;
at(box(2.3, 0.32, 0.85, sofaC, { outline: 0.01 }), 0, 0.3, 0.05, sofa);
at(box(2.3, 0.62, 0.25, sofaC, { outline: 0.01 }), 0, 0.72, -0.28, sofa);
for (const s of [-1, 1]) at(box(0.22, 0.5, 0.9, sofaC, { outline: 0.01 }), s * 1.2, 0.45, 0.05, sofa);
for (const s of [-1, 1]) { const c = at(box(1.0, 0.12, 0.7, 0x3a959d), s * 0.52, 0.51, 0.08, sofa); }
const lace = at(box(0.9, 0.3, 0.02, 0xfdfbf5), 0, 0.92, -0.15, sofa);
const pillow = at(sph(0.2, 0xe9c46a, { outline: 0.03 }), -0.88, 0.7, -0.08, sofa); pillow.scale.set(1, 0.9, 0.4); pillow.rotation.z = 0.3;

// coffee table + tea + churchkhela
const table = at(new THREE.Group(), 0.15, 0, -1.05, home);
at(cyl(0.5, 0.5, 0.06, 0x8a5a33, { outline: 0.02 }), 0, 0.42, 0, table);
at(cyl(0.05, 0.08, 0.4, 0x6e4426), 0, 0.2, 0, table);
at(cyl(0.25, 0.3, 0.03, 0x6e4426), 0, 0.015, 0, table);
const doily = at(cyl(0.38, 0.38, 0.005, 0xfdfbf5), 0, 0.455, 0, table);
const plate = at(cyl(0.16, 0.12, 0.03, 0xffffff, { outline: 0.03 }), -0.2, 0.47, 0.1, table);
for (let i = 0; i < 3; i++) {
  const ch = at(new THREE.Group(), -0.28 + i * 0.07, 0.52, 0.1, table);
  ch.rotation.z = Math.PI / 2; ch.rotation.y = 0.4;
  for (let k = 0; k < 6; k++) at(sph(0.032, [0x7a2e1f, 0x8e3b22, 0x5e2a17][i]), 0, -0.13 + k * 0.05, 0, ch);
}
// tea glass in a metal holder
function makeTea() {
  const g = new THREE.Group();
  at(cyl(0.045, 0.04, 0.12, toon(0xb5651d, { transparent: true, opacity: 0.85 })), 0, 0.06, 0, g);
  at(cyl(0.05, 0.045, 0.06, 0xc9ccd1, { outline: 0.04 }), 0, 0.03, 0, g);
  const h = at(mesh(new THREE.TorusGeometry(0.035, 0.008, 8, 16, Math.PI), 0xc9ccd1), 0.06, 0.05, 0, g); h.rotation.z = -Math.PI / 2;
  return g;
}
const tea = makeTea(); home.add(tea);

// old TV on a stand, showing static
const staticCanvas = document.createElement('canvas'); staticCanvas.width = 96; staticCanvas.height = 72;
const staticTex = new THREE.CanvasTexture(staticCanvas); staticTex.magFilter = THREE.NearestFilter;
const oldTV = at(new THREE.Group(), 2.7, 0, 0.3, home);
oldTV.rotation.y = -2.25;
at(box(0.7, 0.55, 0.45, 0x8a5a33, { outline: 0.01 }), 0, 0.28, 0, oldTV);
const tvBody = at(box(0.6, 0.48, 0.45, 0x5a4636, { outline: 0.02 }), 0, 0.8, 0, oldTV);
at(mesh(new THREE.PlaneGeometry(0.42, 0.34), flat(0xffffff, { map: staticTex })), -0.04, 0.82, 0.23, oldTV);
for (const s of [-1, 1]) { const an = at(cyl(0.006, 0.006, 0.45, 0x333333), s * 0.12, 1.2, -0.05, oldTV); an.rotation.z = s * 0.5; }
for (let i = 0; i < 2; i++) at(cyl(0.025, 0.025, 0.02, 0xd8c3a5), 0.24, 0.9 - i * 0.1, 0.23, oldTV).rotation.x = Math.PI / 2;

// sekcia cabinet with crystal
const cab = at(new THREE.Group(), 3.4, 0, -2.75, home);
at(box(1.6, 2.2, 0.45, 0x7a4a2a, { outline: 0.01 }), 0, 1.1, 0, cab);
at(box(1.4, 0.8, 0.02, toon(0xbfe3f0, { transparent: true, opacity: 0.5 })), 0, 1.55, 0.23, cab);
for (let i = 0; i < 6; i++) at(cyl(0.05, 0.035, 0.18, toon(0xdff6ff, { transparent: true, opacity: 0.8 })), -0.55 + i * 0.22, 1.35, 0.1, cab);
for (let i = 0; i < 4; i++) at(sph(0.08, [0xe76f51, 0x2a9d8f, 0xe9c46a, 0x8f1d1d][i]), -0.45 + i * 0.3, 1.75, 0.1, cab);
at(box(1.4, 0.04, 0.4, 0x6a3f22), 0, 1.2, 0, cab);
const vase = at(cyl(0.12, 0.08, 0.35, 0x1d3557, { outline: 0.03 }), 0.45, 2.38, 0, cab);
for (let i = 0; i < 4; i++) at(sph(0.08, [0xe63946, 0xf4a261, 0xffffff, 0xe63946][i]), 0.4 + Math.cos(i * 1.6) * 0.1, 2.62 + (i % 2) * 0.06, Math.sin(i * 1.6) * 0.08, cab);

// floor lamp
const lamp = at(new THREE.Group(), -1.75, 0, -2.4, home);
at(cyl(0.2, 0.22, 0.04, 0x3b3b3b), 0, 0.02, 0, lamp);
at(cyl(0.02, 0.02, 1.5, 0x3b3b3b), 0, 0.77, 0, lamp);
at(cyl(0.18, 0.3, 0.32, toon(0xffe9b0, { emissive: 0x6b5520 }), { outline: 0.02 }), 0, 1.6, 0, lamp);

// rug, wall clock, family photo, door
const rugTex = canvasTex(400, 260, (g, w, h) => {
  g.fillStyle = '#b5372c'; g.fillRect(0, 0, w, h);
  g.strokeStyle = '#f1e3c4'; g.lineWidth = 12; g.strokeRect(14, 14, w - 28, h - 28);
  g.fillStyle = '#264653';
  for (let i = 0; i < 4; i++) { const x = 70 + i * 87; g.beginPath(); g.moveTo(x, h / 2 - 50); g.lineTo(x + 34, h / 2); g.lineTo(x, h / 2 + 50); g.lineTo(x - 34, h / 2); g.fill(); }
});
const rug = at(mesh(new THREE.PlaneGeometry(3.2, 2.1), toon(0xffffff, { map: rugTex }), { cast: false }), 0.2, 0.006, -0.9, home); rug.rotation.x = -Math.PI / 2;
const clock = at(new THREE.Group(), -1.75, 2.45, -2.95, home);
at(cyl(0.2, 0.2, 0.05, 0xfaf3e6, { outline: 0.06 }), 0, 0, 0, clock).rotation.x = Math.PI / 2;
const hourHand = at(new THREE.Group(), 0, 0, 0.04, clock); at(box(0.02, 0.11, 0.01, 0x222222), 0, 0.05, 0, hourHand);
const minHand = at(new THREE.Group(), 0, 0, 0.045, clock); at(box(0.014, 0.16, 0.01, 0x222222), 0, 0.075, 0, minHand);
const photo = at(new THREE.Group(), 2.0, 2.0, -2.97, home);
at(box(0.5, 0.62, 0.03, 0xc29a5b, { outline: 0.03 }), 0, 0, 0, photo);
at(mesh(new THREE.PlaneGeometry(0.4, 0.52), flat(0xffffff, { map: canvasTex(100, 130, (g) => {
  g.fillStyle = '#d9c7a4'; g.fillRect(0, 0, 100, 130);
  g.fillStyle = '#6b4a3a'; g.beginPath(); g.arc(35, 55, 14, 0, 7); g.fill(); g.beginPath(); g.arc(65, 50, 14, 0, 7); g.fill();
  g.fillRect(20, 70, 30, 50); g.fillRect(50, 66, 30, 54);
}) })), 0, 0, 0.02, photo);
const door = at(new THREE.Group(), -4.47, 0, 1.6, home); door.rotation.y = Math.PI / 2;
at(box(1.0, 2.1, 0.05, 0xa0663a, { outline: 0.01 }), 0, 1.05, 0, door);
for (const [x, y] of [[-0.2, 1.5], [0.2, 1.5], [-0.2, 0.6], [0.2, 0.6]]) at(box(0.32, 0.6, 0.02, 0x8a5530), x, y, 0.035, door);
at(sph(0.04, 0xf5c542), 0.38, 1.0, 0.06, door);

// the "TV goes here" tape outline (only in the final scene)
const tvSpot = at(new THREE.Group(), -4.46, 1.45, -0.9, home); tvSpot.rotation.y = Math.PI / 2;
const tape = 0xf2c84b;
for (const [x, y, w, h] of [[0, 0.62, 2.3, 0.07], [0, -0.62, 2.3, 0.07], [-1.15, 0, 0.07, 1.31], [1.15, 0, 0.07, 1.31]]) at(box(w, h, 0.01, tape), x, y, 0, tvSpot);
const cobweb = at(new THREE.Group(), 0, 0, 0, home);

// lights
const hemi = new THREE.HemisphereLight(0xfff3dc, 0x7a5a40, 1.4); home.add(hemi);
const sun = new THREE.DirectionalLight(0xffe2b5, 2.4);
sun.position.set(-3, 5, 4); sun.target.position.set(0, 0.5, -1.5);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -5, right: 5, top: 5, bottom: -3, near: 0.5, far: 15 });
sun.shadow.bias = -0.0008; sun.shadow.normalBias = 0.02;
home.add(sun, sun.target);
const lampLight = new THREE.PointLight(0xffc977, 3, 6, 1.5); lampLight.position.set(-1.75, 1.6, -2.3); home.add(lampLight);
const fill = new THREE.DirectionalLight(0xc7dcff, 0.6); fill.position.set(4, 3, 3); home.add(fill);

// Nana
const nana = makePerson({
  skin: 0xf2c4a0, legs: 0x9b6b55, shoes: 0xc0392b, pompom: 0xffffff, skirt: 0x1d3557, top: 0xc0392b, dress: 0x264f8a,
  sleeve: 0xc0392b, cuff: 0xffffff, cardigan: true, hair: 'bun', hairColor: 0x3b2418, brows: 0x3b2418, blush: 0xff7f7f,
  earrings: true, lashes: true, lipColor: 0x9e2a2b, nose: 0.052,
});
home.add(nana.root);

// her phone (a generic smartphone) and bank card (no real brand)
const phoneCanvas = document.createElement('canvas'); phoneCanvas.width = 360; phoneCanvas.height = 720;
const phoneTex = new THREE.CanvasTexture(phoneCanvas); phoneTex.colorSpace = THREE.SRGBColorSpace; phoneTex.anisotropy = 8;
const phone = new THREE.Group();
at(box(0.085, 0.17, 0.012, 0xe85d75, { outline: 0.04 }), 0, 0, -0.002, phone);
const phoneScreen = at(mesh(new THREE.PlaneGeometry(0.076, 0.152), flat(0xffffff, { map: phoneTex })), 0, 0, 0.0045, phone);
home.add(phone);
const card = new THREE.Group();
const cardTex = canvasTex(476, 300, (g, w, h) => {
  // in the style of the classic Georgian "Mono" phone card: black, lilac letters, orange circles
  const lilac = '#b9a7d6', orange = '#f0662b';
  g.fillStyle = '#111111'; g.beginPath(); g.roundRect(0, 0, w, h, 22); g.fill();
  g.textBaseline = 'alphabetic';
  g.fillStyle = orange;
  for (const [x, y, r] of [[46, 62, 36], [158, 66, 32]]) { g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); }
  g.globalCompositeOperation = 'source-over';
  g.fillStyle = lilac; g.font = `900 80px ${KA}`; g.fillText('მონო', 10, 100);
  g.fillStyle = orange; g.globalAlpha = 0.85;
  for (const [x, y, r] of [[46, 62, 36], [158, 66, 32]]) { g.beginPath(); g.arc(x, y, r, Math.PI * 0.95, Math.PI * 1.9); g.fill(); }
  g.globalAlpha = 1;
  g.fillStyle = lilac; g.font = '900 120px "DejaVu Sans", sans-serif'; g.textAlign = 'right'; g.fillText('30', w - 18, 112);
  g.textAlign = 'center'; g.font = `700 19px ${KA}`; g.fillText('ისარგებლეთ საერთაშორისო კავშირით - 00', w / 2, 158);
  g.textAlign = 'left'; g.font = '900 112px "DejaVu Sans", sans-serif';
  // MONO with orange-filled O's
  let x = 10; const y = 278;
  for (const ch of 'MONO') {
    const cw = g.measureText(ch).width;
    if (ch === 'O') { g.fillStyle = orange; g.beginPath(); g.arc(x + cw / 2, y - 40, 40, 0, 7); g.fill(); g.fillStyle = '#111'; g.beginPath(); g.arc(x + cw / 2, y - 40, 14, 0, 7); g.fill(); }
    else { g.fillStyle = lilac; g.fillText(ch, x, y); }
    x += cw - 6;
  }
});
at(mesh(new THREE.PlaneGeometry(0.17, 0.107), flat(0xffffff, { map: cardTex, side: THREE.DoubleSide })), 0, 0, 0, card);
home.add(card);

// thought bubble with the dream TV
const dream = new THREE.Group(); home.add(dream);
const cloudMat = toon(0xffffff);
for (const [x, y, r] of [[0, 0, 0.55], [0.55, 0.1, 0.42], [-0.55, 0.05, 0.45], [0.25, 0.4, 0.42], [-0.3, 0.38, 0.4], [0.05, -0.3, 0.38], [0.6, -0.25, 0.3], [-0.6, -0.28, 0.32]]) {
  const c = at(mesh(new THREE.SphereGeometry(r, 24, 16), cloudMat, { outline: 0.03, cast: false }), x, y, 0, dream); c.scale.z = 0.35;
}
const dreamPuffs = [0.09, 0.13].map((r, i) => at(mesh(new THREE.SphereGeometry(r, 20, 12), cloudMat, { outline: 0.05, cast: false }), -0.9 + i * 0.25, -0.75 + i * 0.25, 0, dream));
const rainbowCanvas = document.createElement('canvas'); rainbowCanvas.width = 256; rainbowCanvas.height = 144;
const rainbowTex = new THREE.CanvasTexture(rainbowCanvas); rainbowTex.colorSpace = THREE.SRGBColorSpace;
const bigTV = at(new THREE.Group(), 0, 0.05, 0.25, dream);
at(box(1.1, 0.66, 0.05, 0x1a1a1a, { outline: 0.03, cast: false }), 0, 0, 0, bigTV);
at(mesh(new THREE.PlaneGeometry(1.0, 0.56), flat(0xffffff, { map: rainbowTex })), 0, 0, 0.03, bigTV);
at(box(0.3, 0.04, 0.12, 0x1a1a1a, { cast: false }), 0, -0.38, 0, bigTV);
for (let i = 0; i < 5; i++) {
  const s = at(mesh(starGeo(0.07, 0.03), flat(0xffd52e)), Math.cos(i * 1.26) * 0.75, Math.sin(i * 1.26) * 0.45, 0.3, dream);
  s.userData.k = i;
}

// confetti
const confetti = new THREE.Group(); home.add(confetti);
const confR = rng(3);
const confColors = [0xe63946, 0xf4a261, 0x2a9d8f, 0xe9c46a, 0x6a4c93, 0x48cae4];
for (let i = 0; i < 90; i++) {
  const c = at(mesh(new THREE.PlaneGeometry(0.05, 0.03), flat(confColors[i % 6], { side: THREE.DoubleSide })), 0, 0, 0, confetti);
  c.userData = { x: (confR() - 0.5) * 3.2, z: (confR() - 0.5) * 1.6, d: confR() * 1.2, v: 0.6 + confR() * 0.5, s: confR() * 6, w: 1 + confR() * 3 };
}

// ---------------------------------------------------------------- the caller's prison cell
// The "prize centre" is a jail cell: concrete walls, black iron bars, a cot
// with a grey blanket and a white pillow. The caller phones from in there.
const den = new THREE.Group(); scene.add(den); den.position.set(0, 0, 40);
const concrete = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#6f6a63'; g.fillRect(0, 0, w, h);
  const r = rng(11);
  for (let i = 0; i < 260; i++) { const v = 80 + r() * 50; g.fillStyle = `rgba(${v},${v - 4},${v - 10},${0.15 + r() * 0.25})`; g.beginPath(); g.arc(r() * w, r() * h, 2 + r() * 22, 0, 7); g.fill(); }
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(0,0,0,0.35)'); gr.addColorStop(0.5, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.3)');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  // tally marks scratched into the wall
  g.strokeStyle = 'rgba(30,28,25,0.75)'; g.lineWidth = 3;
  for (let k = 0; k < 6; k++) { const x0 = 330 + (k % 3) * 52, y0 = 250 + Math.floor(k / 3) * 60;
    for (let i = 0; i < 4; i++) { g.beginPath(); g.moveTo(x0 + i * 9, y0); g.lineTo(x0 + i * 9 + 2, y0 + 38); g.stroke(); }
    g.beginPath(); g.moveTo(x0 - 6, y0 + 30); g.lineTo(x0 + 34, y0 + 6); g.stroke(); }
});
const backCell = at(mesh(new THREE.PlaneGeometry(3.6, 3.2), toon(0xffffff, { map: concrete }), { cast: false }), 0, 1.6, -1.6, den);
const darkMat = toon(0x24221f);
at(mesh(new THREE.PlaneGeometry(10, 3.4), darkMat, { cast: false }), 0, 1.7, -3.5, den); // corridor beyond the side bars
const denFloor = at(mesh(new THREE.PlaneGeometry(10, 8), toon(0x55524d), { cast: false }), 0, 0, 0.5, den); denFloor.rotation.x = -Math.PI / 2;
// iron bars: front wall with a door, and side walls, like a classic cell block
const barMat = toon(0x1e1c1a);
function barWall(len, h, vertical) {
  const g = new THREE.Group();
  for (let x = -len / 2; x <= len / 2 + 1e-6; x += 0.19) at(cyl(0.017, 0.017, h, barMat), x, h / 2, 0, g);
  for (const y of [0.05, 0.95, 1.85, h - 0.05]) at(box(len + 0.06, 0.05, 0.035, barMat), 0, y, 0, g);
  return g;
}
const frontBars = at(barWall(3.4, 2.6), 0, 0, 1.15, den);
const doorG = at(new THREE.Group(), 0.38, 0, 1.17, den); // the cell door, a heavier frame
for (const [x, y, w, h] of [[0, 1.3, 0.06, 2.55], [0.86, 1.3, 0.06, 2.55], [0.43, 2.55, 0.92, 0.07], [0.43, 1.45, 0.92, 0.06], [0.43, 0.75, 0.92, 0.05]]) at(box(w, h, 0.05, barMat), x, y, 0, doorG);
at(box(0.22, 0.2, 0.06, barMat), 0.8, 1.15, 0.01, doorG); // lock plate
const sideL = at(barWall(2.75, 2.6), -1.7, 0, -0.22, den); sideL.rotation.y = Math.PI / 2;
const sideR = at(barWall(2.75, 2.6), 1.7, 0, -0.22, den); sideR.rotation.y = Math.PI / 2;
at(box(3.5, 0.08, 2.9, barMat), 0, 2.62, -0.22, den); // ceiling frame
// the cot: steel frame, grey striped blanket, white pillow
const cot = at(new THREE.Group(), -0.25, 0, -0.62, den);
at(box(1.95, 0.05, 0.72, 0x3a3835, { outline: 0.01 }), 0, 0.36, 0, cot);
for (const [x, z] of [[-0.95, -0.33], [0.95, -0.33], [-0.95, 0.33], [0.95, 0.33]]) at(box(0.05, 0.36, 0.05, 0x3a3835), x, 0.18, z, cot);
const blanketTex = canvasTex(256, 128, (g, w, h) => {
  g.fillStyle = '#8d8a84'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#5f5c57'; g.fillRect(0, 34, w, 6); g.fillRect(0, 88, w, 6);
});
at(box(1.9, 0.1, 0.7, toon(0xffffff, { map: blanketTex }), { outline: 0.01 }), 0, 0.44, 0, cot);
const cotPillow = at(sph(0.2, 0xf4f4f0, { outline: 0.03 }), -0.72, 0.55, 0, cot); cotPillow.scale.set(1.2, 0.4, 1.4);
// high barred window with moonlight
const winG = at(new THREE.Group(), 0.95, 2.25, -1.58, den);
at(mesh(new THREE.PlaneGeometry(0.6, 0.4), flat(0x2b3a66)), 0, 0, 0, winG);
at(sph(0.06, flat(0xfff8c4)), 0.15, 0.08, 0.01, winG);
for (let i = 0; i < 5; i++) at(cyl(0.012, 0.012, 0.4, barMat), -0.24 + i * 0.12, 0, 0.02, winG);
// tin mug and a small stash of cash on the cot
at(cyl(0.05, 0.045, 0.1, 0x9aa0a6, { outline: 0.04 }), 0.55, 0.05, -1.3, den);
const cash = at(new THREE.Group(), 0.55, 0.5, -0.75, den);
for (let i = 0; i < 4; i++) at(box(0.2, 0.025, 0.1, 0x6ab04c, { outline: 0.03 }), (i % 2) * 0.03, 0.013 + i * 0.026, (i % 3) * 0.01, cash).rotation.y = i * 0.15;
// caged bulb overhead
const bulbG = at(new THREE.Group(), 0, 2.45, 0.1, den);
at(cyl(0.12, 0.12, 0.04, barMat), 0, 0.1, 0, bulbG);
at(sph(0.07, flat(0xfff2b0)), 0, 0, 0, bulbG);
for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; at(cyl(0.006, 0.006, 0.18, barMat), Math.cos(a) * 0.1, 0, Math.sin(a) * 0.1, bulbG); }
const denLight = new THREE.SpotLight(0xffe2b0, 16, 7, 0.95, 0.55, 1.3);
denLight.position.set(0, 2.4, 40.4); denLight.target.position.set(0, 0.6, 39.8);
denLight.castShadow = true; denLight.shadow.mapSize.set(2048, 2048);
scene.add(denLight, denLight.target);
const denHemi = new THREE.HemisphereLight(0xb8c4d6, 0x2a2622, 0.9); den.add(denHemi);
const denRim = new THREE.DirectionalLight(0x8fa8ff, 0.9); denRim.position.set(3, 2, -2); den.add(denRim);
const denFill = new THREE.DirectionalLight(0xffe0c0, 1.1); denFill.position.set(-1, 1.6, 4); den.add(denFill);
// money rain
const moneyRain = new THREE.Group(); den.add(moneyRain);
const mr = rng(77);
for (let i = 0; i < 40; i++) {
  const b = at(mesh(new THREE.PlaneGeometry(0.16, 0.08), toon(0x6ab04c, { side: THREE.DoubleSide })), 0, 0, 0, moneyRain);
  b.userData = { x: (mr() - 0.5) * 2.6, z: -0.6 + mr() * 1.4, d: mr() * 1.6, s: mr() * 6 };
}

// Gogi, the caller, in an orange prison jumpsuit with inmate number
const gogi = makePerson({
  skin: 0xe0a882, legs: 0xe8711c, shoes: 0x2b2b2b, top: 0xe8711c, sleeve: 0xe8711c, collar: 0xe8711c,
  hair: 'none', brows: 0x1c1410, mustache: true, shades: true, chain: true, goldTooth: true,
  lipColor: 0x5a2a20, nose: 0.065, noseColor: 0xd99676,
});
const numTex = canvasTex(160, 64, (g, w, h) => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.fillStyle = '#111'; g.font = '900 40px "DejaVu Sans", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('№ 777', w / 2, h / 2 + 2); });
const patch = at(mesh(new THREE.PlaneGeometry(0.17, 0.068), flat(0xffffff, { map: numTex })), 0.11, 0.3, 0.222, gogi.spine); patch.rotation.y = 0.35;
// stubble on the shaved head
const stubble = at(mesh(new THREE.SphereGeometry(0.312, 32, 12, 0, Math.PI * 2, 0, Math.PI * 0.42), toon(0x6b5446)), 0, 0.0, -0.025, gogi.head); stubble.rotation.x = -0.4;
gogi.root.position.set(0, 0, 0);
den.add(gogi.root);
// a cheap smuggled mobile phone
const handset = new THREE.Group();
at(box(0.06, 0.12, 0.018, 0x222222, { outline: 0.05 }), 0, 0, 0, handset);
at(mesh(new THREE.PlaneGeometry(0.045, 0.05), flat(0x7fd1ff)), 0, 0.025, 0.0095, handset);
scene.add(handset);

// ---------------------------------------------------------------- phone close-up insert
// A separate little set: her hand holding the phone, card in the other hand,
// against a soft, out-of-focus version of the living room.
const insert = new THREE.Group(); insert.position.set(0, 0, -40); scene.add(insert);
const bokeh = canvasTex(640, 360, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#f2d3a2'); gr.addColorStop(0.55, '#c0392b'); gr.addColorStop(1, '#2f7f86');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  const r = rng(21);
  for (let i = 0; i < 26; i++) { g.fillStyle = `rgba(255,${200 + r() * 55},${120 + r() * 80},${0.15 + r() * 0.25})`; g.beginPath(); g.arc(r() * w, r() * h, 20 + r() * 50, 0, 7); g.fill(); }
});
at(mesh(new THREE.PlaneGeometry(4, 2.25), flat(0xffffff, { map: bokeh })), 0, 0, -1.2, insert);
const insPhone = at(new THREE.Group(), 0.02, -0.01, 0, insert);
at(box(0.085, 0.17, 0.012, 0xe85d75, { outline: 0.04 }), 0, 0, -0.002, insPhone);
at(mesh(new THREE.PlaneGeometry(0.076, 0.152), flat(0xffffff, { map: phoneTex })), 0, 0, 0.0045, insPhone);
const skinI = 0xf2c4a0;
const insHand = at(new THREE.Group(), 0, 0, 0, insPhone);
for (const [x, y, z, sx, sy, sz] of [[0.0, -0.06, -0.03, 0.075, 0.07, 0.035], [-0.05, 0.0, -0.015, 0.018, 0.075, 0.02], [0.05, 0.02, -0.015, 0.02, 0.06, 0.02], [0.05, -0.03, -0.012, 0.02, 0.05, 0.02]]) {
  const m = at(sph(1, skinI, { outline: 0.06 }), x, y, z, insHand); m.scale.set(sx, sy, sz);
}
at(cap(0.065, 0.1, 0xc0392b, { outline: 0.03 }), 0.0, -0.17, -0.06, insHand).rotation.x = 0.5;
at(cyl(0.068, 0.068, 0.03, 0xffffff), 0, -0.115, -0.04, insHand).rotation.x = 0.5;
const insThumb = at(new THREE.Group(), -0.055, -0.07, 0.01, insPhone);
const th = at(sph(1, skinI, { outline: 0.06 }), 0, 0.035, 0.0, insThumb); th.scale.set(0.017, 0.045, 0.017);
const insCard = at(new THREE.Group(), -0.17, -0.02, -0.08, insert);
at(mesh(new THREE.PlaneGeometry(0.17, 0.107), flat(0xffffff, { map: cardTex, side: THREE.DoubleSide })), 0, 0, 0, insCard);
const cardHand = at(sph(1, skinI, { outline: 0.06 }), -0.1, -0.005, -0.01, insCard); cardHand.scale.set(0.035, 0.045, 0.03);
insCard.rotation.set(-0.1, 0.45, 0.2);
const insLight = new THREE.DirectionalLight(0xfff0d8, 2.2); insLight.position.set(1, 2, 3); insert.add(insLight, insLight.target);
insert.add(new THREE.HemisphereLight(0xfff3dc, 0x7a5a40, 1.2));

function poseInsert(t) {
  // thumb hovers over the keypad area, taps the digits, then the big button
  const keys = [0, 1, 2].map(i => M.bank + 0.9 + i * 0.32);
  let tx = 0.0, ty = -0.0, press = 0;
  for (const k of keys) { const d = t - k; if (d > -0.15 && d < 0.15) press = Math.max(press, 1 - Math.abs(d) / 0.15); }
  const toBtn = seg(t, M.bank + 1.9, M.tap - 0.2);
  tx = lerp(0.03 + Math.sin(t * 7) * 0.01, 0.055, toBtn); ty = lerp(0.04, 0.06, toBtn);
  const dp = t - M.tap; if (dp > -0.15 && dp < 0.2) press = Math.max(press, 1 - Math.abs(dp) / 0.18);
  if (t > M.paid + 0.2) { tx = 0.0; ty = -0.02; press = 0; }
  // thumb hinge sits at bottom-left of the phone; button is lower half, keypad digits mid
  insThumb.rotation.set(0, 0, t > M.paid + 0.2 ? lerp(-0.9, -2.3, seg(t, M.paid + 0.2, M.paid + 0.5)) : -0.9 + tx * 8 - ty * 2);
  insThumb.position.z = 0.012 + (1 - press) * 0.025;
  insThumb.visible = t < M.paid + 0.3;
  insPhone.rotation.set(0.05 + Math.sin(t * 1.1) * 0.03, -0.1, 0.04 + Math.sin(t * 0.8) * 0.02);
  insPhone.position.y = -0.01 - press * 0.003 + (t > M.paid ? Math.sin(clamp((t - M.paid) / 0.4) * Math.PI) * 0.01 : 0);
  insCard.position.y = -0.02 + Math.sin(t * 1.3) * 0.005;
}

// ---------------------------------------------------------------- posing
const _w = new THREE.Vector3(), _q = new THREE.Quaternion();
function placeOnHand(obj, P, i, offset, quat) {
  P.arms[i].hand.updateWorldMatrix(true, false);
  P.arms[i].hand.getWorldPosition(_w);
  obj.position.copy(_w).add(offset || v3(0, 0, 0));
  if (quat) obj.quaternion.copy(quat);
}
function lookQuat(from, to, up = v3(0, 1, 0)) {
  _m.lookAt(from, to, up); return new THREE.Quaternion().setFromRotationMatrix(_m);
}
function blink(t, seedOffset = 0) {
  const period = 3.1 + (seedOffset % 1.3);
  const ph = (t + seedOffset) % period;
  return ph < 0.14 ? Math.sin(ph / 0.14 * Math.PI) : 0;
}
function talk(who, t) { // lip-sync opening from the voice envelope
  for (const l of LINES) if (l.who === who && t >= l.start && t < l.start + l.dur) {
    const x = (t - l.start) * FPS, i = Math.floor(x), f = x - i;
    const a = l.env[i] || 0, b = l.env[i + 1] || 0;
    return lerp(a, b, f);
  }
  return 0;
}
const isTalking = (who, t) => talk(who, t) > 0.05;

// chest-space hand targets for Nana
const NT = {
  restL: v3(0.24, -0.38, 0.12), restR: v3(-0.24, -0.38, 0.12),
  lapL: v3(0.12, -0.36, 0.3), lapR: v3(-0.12, -0.36, 0.3),
  sipL: v3(0.06, 0.14, 0.27),
  earR: v3(-0.36, 0.3, 0.04),
  cheekL: v3(0.2, 0.25, 0.22), cheekR: v3(-0.2, 0.25, 0.22),
  upL: v3(0.42, 0.5, 0.1), upR: v3(-0.42, 0.5, 0.1),
  holdR: v3(-0.06, -0.06, 0.36), holdL: v3(0.1, -0.08, 0.36),
  cardShowL: v3(0.24, 0.18, 0.36), pocketL: v3(-0.12, -0.32, 0.22),
  hipL: v3(0.36, -0.36, -0.02), hipR: v3(-0.36, -0.36, -0.02),
};
const poleL = v3(0.6, -0.4, -0.8), poleR = v3(-0.6, -0.4, -0.8);

function poseLegs(P, sit) {
  for (const L of P.legs) {
    L.thigh.rotation.set(-1.45 * sit, 0, L.s * 0.05 * (1 - sit));
    L.knee.rotation.set(1.45 * sit, 0, 0);
    L.foot.rotation.set(0, 0, 0);
  }
}

const tvSpotWorld = v3(-4.4, 1.45, -0.9);

function poseNana(t) {
  const P = nana;
  P.root.visible = true;
  const final = t >= M.final;
  // --- where she is and how she sits/stands
  let sit = 1 - seg(t, M.vaime + 0.15, M.vaime + 0.6);
  let pos = v3(0, 0, -2.0), rotY = 0;
  if (final) { sit = 0; pos = v3(-3.25, 0, -0.35); rotY = 0.95; }
  const sitDrop = 0.56 - 0.47; // hips at seat height when seated
  P.root.position.copy(pos);
  P.root.rotation.y = rotY;
  P.hips.position.y = 0.56 - sit * 0.05;
  P.root.position.y = sit * (0.47 + 0.05 - 0.56 + 0.56) - sit * 0.56 + sit * sitDrop * 0;
  // seated: hips at ~0.5 above the seat cushion (y 0.57)
  P.root.position.y = sit * 0.02;
  if (sit > 0) P.root.position.z = lerp(-2.0, -1.85, 1 - sit);
  poseLegs(P, sit);

  // squash & stretch + jumps
  let sq = 1, jump = 0, sway = 0, lean = 0, twist = 0;
  // startle hop when the phone rings
  const st = t - M.startle;
  if (st > 0 && st < 0.7) { jump += Math.sin(clamp(st / 0.45) * Math.PI) * 0.28; sq += st < 0.08 ? -0.12 : Math.sin(clamp(st / 0.45) * Math.PI) * 0.1; }
  // lean forward to grab the phone
  lean += Math.sin(clamp((t - M.grab + 0.4) / 1.2) * Math.PI) * 0.35;
  // reaction freeze -> spring up
  if (t > M.reaction && t < M.vaime) lean -= seg(t, M.reaction, M.reaction + 0.2) * 0.12;
  const vj = t - (M.vaime + 0.15);
  if (vj > 0 && vj < 1.0) { jump += Math.sin(clamp(vj / 0.8) * Math.PI) * 0.55; sq += vj < 0.1 ? -0.15 : 0.08 * Math.sin(clamp(vj / 0.8) * Math.PI); }
  // happy dance
  const dt = t - (M.vaime + 1.0);
  if (dt > 0 && t < M.pay + 0.4) {
    const k = Math.min(1, dt * 2) * (1 - seg(t, M.pay, M.pay + 0.4));
    jump += Math.abs(Math.sin(dt * Math.PI * 2.1)) * 0.16 * k;
    sq += Math.cos(dt * Math.PI * 4.2) * 0.05 * k;
    sway += Math.sin(dt * Math.PI * 2.1) * 0.22 * k;
    twist += Math.sin(dt * Math.PI * 1.05) * 0.5 * k;
  }
  // eager nodding while the caller explains
  if (t > M.pay + 2.5 && t < M.now) lean += Math.abs(Math.sin((t - M.pay) * 9)) * 0.12;
  // proud bounce at the end of the payment
  const pb = t - M.paid;
  if (pb > 0 && pb < 0.8 && t < M.thanks) { jump += Math.sin(clamp(pb / 0.5) * Math.PI) * 0.12; }
  // final: tapping foot, patient sway
  if (final) { sway += Math.sin(t * 1.4) * 0.05; }
  P.body.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq));
  P.root.position.y += jump;
  P.spine.rotation.set(lean + (sit ? 0.05 : 0), twist * 0.3, sway);
  P.hips.rotation.y = twist * 0.4;

  // --- head direction
  let headY = 0, headX = 0, headZ = 0;
  if (t < M.ring) { headY = -0.75 + Math.sin(t * 0.8) * 0.03; headX = 0.05; } // watching the old TV
  else if (t < M.grab) { headY = track(t, [[M.ring, -0.75], [M.ring + 0.3, 0], [M.grab, 0.15]]); headX = track(t, [[M.ring, 0], [M.ring + 0.4, 0.35]]); }
  else if (t < M.answer + 0.2) { headX = 0.35 * (1 - seg(t, M.grab + 0.4, M.answer)); }
  if (t > M.answer && t < M.reaction) { headZ = 0.12; headY = 0.1; }
  if (t > M.vaime && t < M.pay) { headZ = Math.sin(t * 5) * 0.12; headX = -0.15; }
  if (t > M.now && t < M.thanks) { headX = track(t, [[M.now, 0], [M.card, -0.05], [M.card + 0.9, 0.0], [M.bank, 0.45]]); headZ = 0; }
  if (t > M.paid && t < M.later) { headX = 0.3; headY = 0; headZ = 0.12 * seg(t, M.paid, M.paid + 0.5); }
  if (t > M.luck) { headX = track(t, [[M.luck, 0.3], [M.luck + 0.8, -0.05]]); headZ = 0.1; headY = Math.sin(t * 1.6) * 0.1; }
  if (final) { headY = track(t, [[M.final, 0.3], [M.final + 2, 0.3], [M.final + 2.5, -0.65], [M.final + 4.6, -0.65], [M.final + 5.1, 0.3]]); headX = -0.05; headZ = 0.1; }
  P.neck.rotation.set(headX, headY, headZ);

  // --- arms
  let L = NT.lapL, R = NT.lapR;
  if (t < M.ring) {
    const sip = seg(t, 0.9, 1.4) * (1 - seg(t, 2.1, 2.6));
    L = lerpV(NT.lapL, NT.sipL, sip);
  }
  // startle: arms fly up
  const ar = Math.sin(clamp((t - M.startle) / 0.6) * Math.PI);
  if (t > M.startle && t < M.startle + 0.6) { L = lerpV(L, NT.upL, ar * 0.8); R = lerpV(R, NT.upR, ar * 0.8); }
  // reach for the phone on the table, then bring it to the ear
  const phoneTable = v3(0.42, 0.48, -0.95);
  if (t >= M.grab - 0.6 && t < M.answer + 0.4) {
    const reach = seg(t, M.grab - 0.6, M.grab) * (1 - seg(t, M.grab + 0.15, M.answer));
    const tgt = toChest(P, phoneTable.clone().add(v3(0, 0.03, 0)));
    R = lerpV(NT.lapR, tgt, reach);
    if (t > M.grab + 0.15) R = lerpV(tgt, NT.earR, seg(t, M.grab + 0.15, M.answer));
    L = lerpV(NT.lapL, toChest(P, v3(-0.05, 0.5, -1.0)), seg(t, M.grab - 0.6, M.grab - 0.2) * (1 - seg(t, M.grab, M.grab + 0.4)));
  }
  if (t >= M.answer + 0.4 && t < M.now + 0.6) R = NT.earR;
  // reaction: hand to cheek
  if (t > M.reaction && t < M.vaime + 1.0) L = lerpV(NT.lapL, NT.cheekL, seg(t, M.reaction, M.reaction + 0.25));
  // dance: free arm pumps the air
  if (t >= M.vaime + 1.0 && t < M.pay + 0.3) {
    const pump = 0.5 + 0.5 * Math.sin((t - M.vaime) * Math.PI * 4.2);
    L = lerpV(lerpV(NT.cheekL, NT.upL, seg(t, M.vaime + 1.0, M.vaime + 1.3)), v3(0.5, 0.25, 0.15), pump * 0.6);
  }
  if (t >= M.pay + 0.3 && t < M.now) L = lerpV(L, NT.hipL, seg(t, M.pay + 0.3, M.pay + 0.8));
  // card from the pocket, show it off, then hold phone + card for the payment
  if (t >= M.now && t < M.later) {
    const c0 = M.card - 0.9;
    L = track(t, [[M.now, NT.hipL], [c0, NT.hipL], [c0 + 0.4, NT.pocketL], [M.card, NT.pocketL], [M.card + 0.35, NT.cardShowL], [M.bank - 0.4, NT.cardShowL], [M.bank, NT.holdL]]);
    if (t > M.now + 0.4) R = track(t, [[M.now + 0.4, NT.earR], [M.bank - 0.3, NT.earR], [M.bank, NT.holdR]]);
    if (t >= M.bank && t < M.paid + 0.4) {
      // the phone hand's thumb taps: tiny bob
      const tapK = Math.max(0, Math.sin((t - M.bank - 0.9) * Math.PI / 0.32)) * (t > M.bank + 0.9 && t < M.bank + 2.2 ? 1 : 0)
        + Math.sin(clamp((t - M.tap + 0.15) / 0.3) * Math.PI) * 1.5;
      R = NT.holdR.clone().add(v3(0, 0, -0.012 * tapK));
    }
    if (t >= M.paid + 0.4) {
      R = lerpV(NT.holdR, v3(-0.1, 0.0, 0.38), seg(t, M.paid + 0.4, M.paid + 1.0));
      L = lerpV(NT.holdL, NT.hipL, seg(t, M.paid + 0.4, M.paid + 1.0));
    }
  }
  if (t >= M.luck && t < M.later) {
    R = lerpV(v3(-0.1, 0.0, 0.38), v3(-0.14, 0.12, 0.36), seg(t, M.luck, M.luck + 0.5));
    L = track(t, [[M.luck, NT.hipL], [M.luck + 1.8, NT.hipL], [M.luck + 2.2, v3(0.38, 0.35, 0.25)], [M.luck + 3.8, v3(0.38, 0.35, 0.25)], [M.luck + 4.3, NT.hipL]]);
  }
  if (final) {
    L = NT.hipL;
    R = v3(-0.1, -0.04, 0.3);
  }
  solveArm(P.arms[0], L, poleL);
  solveArm(P.arms[1], R, poleR);

  // --- face
  const o = talk('nana', t);
  const f = { t, open: o * 0.9, smile: 0.35, lid: 0.18 + blink(t, 0.3) * 0.82 };
  if (t < M.ring) Object.assign(f, { lid: 0.42 + blink(t, 0.3) * 0.58, smile: 0.1, lookX: 0.0 }); // bored
  if (t > M.startle && t < M.ring + 1.4) Object.assign(f, { eye: 1.35, pupil: 0.7, lid: 0, brow: 1, open: 0.8 * (1 - seg(t, M.startle + 0.5, M.ring + 1.4)), smile: 0 });
  if (t > M.answer && t < M.congrats + 2) Object.assign(f, { brow: 0.4, smile: 0.35 });
  if (t > M.congrats + 2 && t < M.reaction) Object.assign(f, { eye: 1 + seg(t, M.congrats + 2, M.reaction) * 0.25, brow: 0.6, smile: 0.2, open: 0.1 + seg(t, M.reaction - 1, M.reaction) * 0.3 });
  if (t >= M.reaction && t < M.vaime + 0.2) {
    const pop = backOut((t - M.reaction) / 0.35);
    Object.assign(f, { eye: 1 + 0.6 * pop, pupil: 0.55, lid: 0, lidLow: 0, brow: 1.4, open: 1.2 * pop, smile: 0.2, stars: t > M.reaction + 0.45 ? 1 : 0 });
  }
  if (t >= M.vaime + 0.2 && t < M.pay) Object.assign(f, { eye: 1.3, lid: 0, brow: 1.1, smile: 1, open: Math.max(o, t > M.dance ? 0.55 + 0.2 * Math.sin(t * 8) : 0) * 1.1, stars: t < M.dance + 1.6 ? 1 : 0 });
  if (t >= M.pay && t < M.now) Object.assign(f, { eye: 1.15, brow: 0.7, smile: 0.9, lid: 0.05 + blink(t) * 0.9 });
  if (t >= M.now && t < M.bank) Object.assign(f, { eye: 1.2, brow: 0.9, smile: 1, lid: 0.05 + blink(t) * 0.9, open: o * 1.1 });
  if (t >= M.bank && t < M.paid) Object.assign(f, { eye: 1.05, brow: -0.2, browTilt: 0.3, smile: 0.5, lookY: -0.6, lid: 0.25, open: 0.05 + 0.1 * (t > M.tap - 0.3 ? 1 : 0) });
  if (t >= M.paid && t < M.later) Object.assign(f, { eye: 1.0, brow: 0.6, smile: 1.15, lid: 0.35 + blink(t, 1) * 0.6, lidLow: 0.35, lookY: t < M.luck ? -0.5 : 0, open: Math.max(o * 1.05, 0.05), wide: 1.2 });
  if (final) Object.assign(f, { eye: 1, brow: 0.5, smile: 1.1, lid: 0.3 + blink(t, 2) * 0.7, lidLow: 0.35, lookX: track(t, [[M.final + 2.2, 0], [M.final + 2.6, -0.8], [M.final + 4.6, -0.8], [M.final + 5.0, 0]]), wide: 1.2 });
  poseFace(P, f);
  P.root.updateMatrixWorld(true);
}

function toChest(P, world) {
  P.root.updateMatrixWorld(true);
  return P.chest.worldToLocal(world.clone());
}

function poseProps(t) {
  // tea glass: in her left hand at first; flies up when the phone rings, lands on the table
  const handL = new THREE.Vector3(); nana.arms[0].hand.getWorldPosition(handL);
  const teaTable = v3(-0.05, 0.455, -0.9);
  if (t < M.startle) { tea.position.copy(handL).add(v3(0, -0.02, 0.03)); tea.rotation.set(0, 0, 0); }
  else if (t < M.startle + 1.1) {
    const k = (t - M.startle) / 1.1;
    const start = v3(0.27, 0.68, -1.68);
    tea.position.copy(lerpV(start, teaTable, smooth(k))); tea.position.y += Math.sin(k * Math.PI) * 0.8;
    tea.rotation.set(k * Math.PI * 2, 0, k * Math.PI * 2);
  } else { tea.position.copy(teaTable); tea.rotation.set(0, 0, 0); }
  if (t >= M.final) { tea.position.copy(handL).add(v3(0, -0.02, 0)); tea.rotation.set(0, 0, 0); }

  // phone
  const tableSpot = v3(0.42, 0.465, -0.95);
  const rq = new THREE.Quaternion();
  if (t < M.grab) {
    phone.position.copy(tableSpot);
    phone.quaternion.setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0.4));
    // buzzing on the table
    if (t > M.ring) {
      const b = Math.sin(t * 90) * 0.012;
      phone.position.x += b; phone.position.y += Math.abs(Math.sin(t * 45)) * 0.02;
      phone.rotateZ(Math.sin(t * 70) * 0.08);
    }
  } else {
    placeOnHand(phone, nana, 1, v3(0, 0, 0));
    nana.head.updateWorldMatrix(true, false);
    const head = new THREE.Vector3(); nana.head.getWorldPosition(head);
    const atEar = (t >= M.answer && t < M.bank - 0.15) ? seg(t, M.grab + 0.3, M.answer) * (1 - seg(t, M.bank - 0.55, M.bank - 0.15)) : 0;
    // held flat in front of her face vs pressed to the ear
    const front = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(phone.position, head.clone().add(v3(0, 0.05, 0)), v3(0, 1, 0)));
    front.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI, 0)));
    const ear = nana.head.getWorldQuaternion(new THREE.Quaternion()).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0.1, -Math.PI / 2, 0.2)));
    phone.quaternion.copy(front).slerp(ear, atEar);
    if (atEar > 0.5) {
      const earPos = new THREE.Vector3(-0.33, 0.0, 0.03); nana.head.localToWorld(earPos);
      phone.position.lerp(earPos, (atEar - 0.5) * 2);
    }
  }
  if (t >= M.final) { // phone tucked into the cardigan pocket
    phone.position.set(9, 9, 9);
  }

  // card
  card.visible = t > M.card - 0.2 && t < M.paid + 1.2;
  if (card.visible) {
    placeOnHand(card, nana, 0, v3(0.0, 0.05, 0.03));
    const shine = t < M.bank ? Math.sin(clamp((t - M.card) / 0.5) * Math.PI) * 0.5 : 0;
    card.quaternion.setFromEuler(new THREE.Euler(-0.1, -0.35 + shine, 0.15));
    if (t > M.bank - 0.4) {
      const head = new THREE.Vector3(); nana.head.getWorldPosition(head);
      card.lookAt(head); card.rotateX(-0.3);
    }
  }
}

function poseDream(t) {
  const a = M.vaime + 0.7, b = M.pay + 0.6;
  const k = t < a ? 0 : t < b ? backOut((t - a) / 0.5) * (1 - seg(t, b - 0.4, b)) : 0;
  dream.visible = k > 0.01;
  if (!dream.visible) return;
  const head = new THREE.Vector3(); nana.head.getWorldPosition(head);
  dream.position.set(head.x + 1.15, head.y + 0.55 + Math.sin(t * 2) * 0.04, head.z + 0.2);
  dream.scale.setScalar(k * 0.85);
  dream.lookAt(camera.position.x, dream.position.y, camera.position.z);
  dreamPuffs.forEach((p, i) => { p.scale.setScalar(clamp(k * 1.5 - i * 0.2)); });
  bigTV.rotation.z = Math.sin(t * 3) * 0.05;
  bigTV.scale.setScalar(1 + Math.sin(t * 6) * 0.03);
  dream.children.forEach(c => { if (c.userData.k !== undefined) { c.rotation.z = t * 3 + c.userData.k; c.scale.setScalar(0.7 + 0.4 * Math.abs(Math.sin(t * 4 + c.userData.k))); } });
  // rainbow "football + fireworks" on the dream TV
  const g = rainbowCanvas.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 256, 144);
  const h = (t * 80) % 360;
  gr.addColorStop(0, `hsl(${h},80%,60%)`); gr.addColorStop(0.5, `hsl(${(h + 120) % 360},80%,60%)`); gr.addColorStop(1, `hsl(${(h + 240) % 360},80%,60%)`);
  g.fillStyle = gr; g.fillRect(0, 0, 256, 144);
  g.fillStyle = '#2e9e4f'; g.fillRect(0, 100, 256, 44);
  g.fillStyle = '#fff'; g.beginPath(); g.arc(128 + Math.sin(t * 4) * 70, 90 - Math.abs(Math.sin(t * 6)) * 40, 12, 0, 7); g.fill();
  g.font = '900 28px "DejaVu Sans", sans-serif'; g.textAlign = 'center'; g.fillStyle = '#fff'; g.fillText('8K ✦ 100"', 128, 34);
  rainbowTex.needsUpdate = true;
}

function poseConfetti(t) {
  const a = M.vaime + 0.5;
  confetti.visible = t > a && t < M.pay + 1.5;
  if (!confetti.visible) return;
  for (const c of confetti.children) {
    const u = c.userData, lt = t - a - u.d;
    if (lt < 0) { c.visible = false; continue; }
    c.visible = true;
    const y = 2.9 - lt * u.v;
    c.position.set(u.x + Math.sin(lt * 2 + u.s) * 0.15, Math.max(0.02, y), -1.5 + u.z);
    c.rotation.set(lt * u.w + u.s, lt * u.w * 0.7, u.s);
  }
}

function poseHome(t) {
  // static on the old TV
  const g = staticCanvas.getContext('2d'), img = g.createImageData(96, 72), r = rng(1 + Math.floor(t * FPS));
  for (let i = 0; i < img.data.length; i += 4) { const v = r() * 255; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255; }
  // a faint wobbling bar
  const bar = Math.floor((t * 40) % 72);
  for (let x = 0; x < 96; x++) for (let y = bar; y < Math.min(72, bar + 6); y++) { const i = (y * 96 + x) * 4; img.data[i] *= 0.5; img.data[i + 1] *= 0.5; img.data[i + 2] *= 0.5; }
  g.putImageData(img, 0, 0); staticTex.needsUpdate = true;
  oldTV.children[1].rotation.z = 0;
  // clock: real time, then a week spins past at the end
  const spin = t < M.later ? t / 60 : (t - M.later) * 4 + M.later / 60;
  minHand.rotation.z = -spin * Math.PI * 2;
  hourHand.rotation.z = -spin * Math.PI * 2 / 12 - 1.2;
  tvSpot.visible = t >= M.final;
  lampLight.intensity = 3;
}

function drawPhone(t) {
  const g = phoneCanvas.getContext('2d'), w = 360, h = 720;
  g.save();
  g.fillStyle = '#10121a'; g.fillRect(0, 0, w, h);
  const center = (txt, y, font, color = '#fff') => { g.font = font; g.fillStyle = color; g.textAlign = 'center'; g.fillText(txt, w / 2, y); };
  const status = () => { g.font = '600 18px "DejaVu Sans", sans-serif'; g.fillStyle = '#fff'; g.textAlign = 'left'; g.fillText('10:42', 22, 34); g.textAlign = 'right'; g.fillText('▮▮▮ 87%', w - 22, 34); };
  if (t < M.answer) {
    const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#3d2c6b'); gr.addColorStop(1, '#0f3460');
    g.fillStyle = gr; g.fillRect(0, 0, w, h); status();
    if (t > M.ring) {
      center('შემომავალი ზარი', 130, `700 24px ${KA}`, '#c8d0ff');
      center('უცნობი ნომერი', 200, `900 34px ${KA}`);
      center('+995 5** *** ***', 245, '600 22px "DejaVu Sans", sans-serif', '#c8d0ff');
      const p = 1 + Math.sin(t * 10) * 0.08;
      g.fillStyle = '#e63946'; g.beginPath(); g.arc(90, 590, 44, 0, 7); g.fill();
      g.fillStyle = '#2ecc71'; g.beginPath(); g.arc(270, 590, 44 * p, 0, 7); g.fill();
      center('✆', 610, '900 46px "DejaVu Sans", sans-serif');
      g.textAlign = 'center'; g.font = '900 46px "DejaVu Sans", sans-serif'; g.fillStyle = '#fff'; g.fillText('✆', 90, 607);
    } else { center('10:42', 230, '200 84px "DejaVu Sans", sans-serif'); center('ოთხშაბათი', 280, `700 24px ${KA}`, '#c8d0ff'); }
  } else if (t < M.bank) {
    g.fillStyle = '#1b2433'; g.fillRect(0, 0, w, h); status();
    center('უცნობი ნომერი', 180, `900 30px ${KA}`);
    const s = Math.floor(Math.max(0, t - M.answer)); center(`00:${String(s).padStart(2, '0')}`, 225, '600 24px "DejaVu Sans", sans-serif', '#9fb3c8');
    g.fillStyle = '#e63946'; g.beginPath(); g.arc(w / 2, 600, 44, 0, 7); g.fill();
  } else if (t < M.paid) {
    // generic bank app: transfer screen
    g.fillStyle = '#f4f1fb'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#5b3cc4'; g.fillRect(0, 0, w, 130);
    status();
    center('გადარიცხვა', 100, `900 30px ${KA}`);
    g.fillStyle = '#fff'; g.beginPath(); g.roundRect(24, 270, w - 48, 130, 18); g.fill();
    g.fillStyle = '#6b6b80'; g.font = `700 18px ${KA}`; g.fillText('თანხა', 44, 302);
    const digits = '500', n = clamp(Math.floor((t - M.bank - 0.9) / 0.32) + 1, 0, 3);
    const amount = digits.slice(0, n) || '0';
    g.fillStyle = '#1b1b2f'; g.font = '900 56px "DejaVu Sans", sans-serif'; g.fillText(amount + ' ₾', 44, 372);
    if (Math.floor(t * 2.5) % 2 === 0 && n < 3) { const mw = g.measureText(amount).width; g.fillRect(44 + mw + 4, 330, 4, 50); }
    g.fillStyle = '#111'; g.beginPath(); g.roundRect(24, 420, w - 48, 70, 18); g.fill();
    g.fillStyle = '#f0662b'; g.beginPath(); g.arc(62, 455, 16, 0, 7); g.fill();
    g.fillStyle = '#b9a7d6'; g.font = '900 24px "DejaVu Sans", sans-serif'; g.fillText('MONO', 90, 464);
    g.font = `700 20px ${KA}`; g.fillText('მონო 30', 190, 463);
    const pressed = t > M.tap - 0.05;
    g.fillStyle = pressed ? '#3d2690' : '#5b3cc4'; g.beginPath(); g.roundRect(24, 560, w - 48, 84, 42); g.fill();
    center('გადარიცხვა', 612, `900 28px ${KA}`);
    if (t > M.tap - 0.3 && t < M.tap + 0.3) { g.fillStyle = 'rgba(255,255,255,0.35)'; g.beginPath(); g.arc(w / 2, 602, 30 + (t - M.tap + 0.3) * 120, 0, 7); g.fill(); }
  } else {
    g.fillStyle = '#e9fbef'; g.fillRect(0, 0, w, h); status();
    const k = backOut((t - M.paid) / 0.4);
    g.fillStyle = '#21b35b'; g.beginPath(); g.arc(w / 2, 260, 90 * k, 0, 7); g.fill();
    g.strokeStyle = '#fff'; g.lineWidth = 18; g.lineCap = 'round'; g.lineJoin = 'round';
    g.beginPath(); g.moveTo(w / 2 - 42 * k, 262); g.lineTo(w / 2 - 10 * k, 296 * (0.85 + 0.15 * k)); g.lineTo(w / 2 + 46 * k, 228); g.stroke();
    center('გადარიცხულია!', 420, `900 34px ${KA}`, '#1b6b3a');
    center('500 ₾', 480, '900 40px "DejaVu Sans", sans-serif', '#1b1b2f');
  }
  g.restore();
  phoneTex.needsUpdate = true;
}

function poseGogi(t) {
  const P = gogi;
  poseLegs(P, 1);
  P.root.position.set(0, 0.0, -0.3);
  P.hips.position.y = 0.52;
  const o = talk('gogi', t);
  const laugh = t > M.thanks && t < M.thanks + 1.6;
  const shake = laugh ? Math.sin(t * 30) * 0.04 : 0;
  P.spine.rotation.set(0.12 + (laugh ? -0.15 + shake : 0), Math.sin(t * 0.9) * 0.08, Math.sin(t * 0.7) * 0.04);
  P.neck.rotation.set(-0.05 + shake, Math.sin(t * 1.3) * 0.1, 0.1 * Math.sin(t * 0.5));
  const chestEar = v3(-0.25, 0.32, 0.1);
  let L = v3(0.15, -0.2, 0.42), R = chestEar;
  // sneaky hand rubbing / counting cash
  const rub = Math.sin(t * 12) * 0.04;
  L = v3(0.06 + rub, -0.18, 0.42);
  if (t > M.thanks + 1.6 && t < M.luck) { L = v3(0.25, 0.25 + Math.abs(Math.sin(t * 6)) * 0.05, 0.4); } // little victory wave
  solveArm(P.arms[0], L, poleL);
  solveArm(P.arms[1], R, poleR);
  const smirk = 0.6 + 0.4 * Math.sin(t * 0.8);
  poseFace(P, { t, open: laugh ? 0.7 + 0.3 * Math.abs(Math.sin(t * 15)) : o * 0.85, smile: laugh ? 1.2 : smirk, wide: 1.3, brow: laugh ? 0.8 : 0.3 + 0.3 * Math.sin(t * 3), browTilt: -0.5 });
  if (P.stache) P.stache.position.y = -0.085 - 0.02 * (laugh ? 1 : o);
  P.root.updateMatrixWorld(true);
  // handset to the ear
  placeOnHand(handset, P, 1);
  handset.quaternion.copy(P.head.getWorldQuaternion(new THREE.Quaternion())).multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0.1, -Math.PI / 2, 0.2)));
  const earPos = new THREE.Vector3(-0.32, -0.02, 0.05); P.head.localToWorld(earPos);
  handset.position.lerp(earPos, 0.6);
  // money rain after the payment
  moneyRain.visible = t > M.thanks;
  for (const b of moneyRain.children) {
    const u = b.userData, lt = t - M.thanks - u.d * 0.6;
    b.visible = lt > 0;
    b.position.set(u.x + Math.sin(lt * 2 + u.s) * 0.2, Math.max(0.03, 2.6 - lt * 0.9), u.z);
    b.rotation.set(lt * 3 + u.s, lt * 2, u.s);
  }
}

// ---------------------------------------------------------------- shots
// Each shot: [start, which set, camera function(t, local k)].
const DEN = 40;
const nanaHead = () => { const p = new THREE.Vector3(); nana.head.getWorldPosition(p); return p; };
const gogiHead = () => { const p = new THREE.Vector3(); gogi.head.getWorldPosition(p); return p; };
const SHOTS = [
  [0, 'home', (t) => { const k = seg(t, 0, M.ring); return [lerpV(v3(3.6, 2.9, 4.6), v3(1.7, 1.7, 2.1), k), lerpV(v3(0.3, 1.0, -1.6), v3(0.1, 1.05, -1.8), k), 42]; }],
  [M.ring + 0.6, 'home', (t) => { const k = seg(t, M.ring + 0.6, M.grab); return [lerpV(v3(1.2, 1.0, 0.4), v3(1.0, 0.9, -0.1), k), v3(0.4, 0.5, -0.95), 38]; }],
  [M.grab, 'home', (t) => { const k = seg(t, M.grab, M.congrats); return [lerpV(v3(1.6, 1.4, 0.9), v3(1.0, 1.3, 0.2), k), lerpV(v3(0.1, 0.9, -1.7), v3(-0.05, 1.15, -1.9), k), 38]; }],
  [M.congrats - 0.15, 'den', (t) => { const k = seg(t, M.congrats, M.congrats + 3.6); return [lerpV(v3(1.5, 1.55, DEN + 3.6), v3(0.55, 1.45, DEN + 2.3), k), v3(0, 1.3, DEN - 0.3), 40]; }],
  [M.congrats + 3.7, 'home', (t) => { const k = seg(t, M.congrats + 3.7, M.reaction); const h = nanaHead(); return [lerpV(v3(0.8, 1.4, 0.5), v3(0.55, 1.35, 0.1), k), h, 36]; }],
  [M.reaction, 'home', (t) => { const k = backOut((t - M.reaction) / 0.25); const h = nanaHead(); return [lerpV(v3(0.6, 1.4, 0.3), v3(0.42, 1.35, -0.3), k), h, 36]; }],
  [M.vaime + 0.1, 'home', (t) => { const k = seg(t, M.vaime + 0.1, M.pay); return [lerpV(v3(0.6, 1.6, 1.8), v3(1.9, 1.9, 2.3), k), v3(0.35, 1.55, -1.7), 46]; }],
  [M.pay - 0.1, 'den', (t) => { const k = seg(t, M.pay, M.pay + 3.0); return [lerpV(v3(-0.85, 1.4, DEN + 1.0), v3(-0.45, 1.45, DEN + 0.85), k), v3(0, 1.4, DEN - 0.3), 40]; }],
  [M.pay + 3.2, 'home', (t) => { const k = seg(t, M.pay + 3.2, M.now); const h = nanaHead(); return [lerpV(v3(-0.4, 1.45, -0.3), v3(-0.25, 1.5, -0.7), k), h.clone().add(v3(0, -0.1, 0)), 38]; }],
  [M.now, 'home', (t) => { const k = seg(t, M.now, M.bank); const h = nanaHead(); return [lerpV(v3(0.9, 1.35, 0.0), v3(0.6, 1.3, -0.5), k), h.clone().add(v3(0.1, -0.35, 0)), 40]; }],
  [M.bank, 'insert', (t) => { const k = seg(t, M.bank, M.thanks); return [lerpV(v3(-0.06, 0.02, -40 + 0.42), v3(-0.03, 0.0, -40 + 0.33), k), v3(-0.035, -0.005, -40), 40]; }],
  [M.thanks - 0.1, 'den', (t) => { const k = seg(t, M.thanks, M.luck); return [lerpV(v3(0.1, 1.35, DEN + 0.95), v3(0.0, 1.5, DEN + 3.6), k), lerpV(v3(0, 1.35, DEN - 0.3), v3(0, 1.2, DEN - 0.3), k), 44]; }],
  [M.luck - 0.15, 'home', (t) => { const k = seg(t, M.luck, M.later); const h = nanaHead(); return [lerpV(v3(0.6, 1.4, 0.2), v3(0.35, 1.45, -0.55), k), h.clone().add(v3(0, -0.15, 0)), 40]; }],
  [M.later, 'black', () => [v3(0, 0, 0), v3(0, 0, -1), 40]],
  [M.final, 'home', (t) => { const k = seg(t, M.final, M.end); return [lerpV(v3(-0.2, 1.7, 2.2), v3(-1.0, 1.6, 1.4), k), lerpV(v3(-3.6, 1.25, -0.55), v3(-3.5, 1.2, -0.5), k), 46]; }],
];

// ---------------------------------------------------------------- overlay (titles + subtitles)
const overlay = document.createElement('canvas'); overlay.width = W; overlay.height = H;
const og = overlay.getContext('2d');
function wrap(g, text, maxW) {
  const words = text.split(' '), out = []; let line = '';
  for (const w of words) { const test = line ? line + ' ' + w : w; if (g.measureText(test).width > maxW && line) { out.push(line); line = w; } else line = test; }
  if (line) out.push(line); return out;
}
function drawOverlay(t) {
  og.clearRect(0, 0, W, H);
  // letterbox-free 16:9; soft vignette
  const vg = og.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 0.95);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(40,20,10,0.35)');
  og.fillStyle = vg; og.fillRect(0, 0, W, H);

  // "one week later" card
  if (t >= M.later && t < M.final + 0.3) {
    const a = clamp((t - M.later) / 0.3) * (1 - seg(t, M.final, M.final + 0.3));
    og.save(); og.globalAlpha = 1; og.fillStyle = `rgba(20,12,8,${t < M.final ? 1 : 1 - seg(t, M.final, M.final + 0.3)})`; og.fillRect(0, 0, W, H);
    og.globalAlpha = a; og.textAlign = 'center'; og.fillStyle = '#ffe066'; og.font = `900 96px ${KA}`; og.fillText('ერთი კვირის შემდეგ...', W / 2, H / 2);
    og.restore();
  }
  // closing title
  if (t > M.final + 4.2) {
    const a = seg(t, M.final + 4.2, M.final + 4.8);
    og.save(); og.globalAlpha = a; og.textAlign = 'center';
    og.font = `900 76px ${KA}`; og.lineJoin = 'round'; og.lineWidth = 14; og.strokeStyle = '#3b1a10';
    og.strokeText('ტელევიზორი ჯერ კიდევ გზაშია...', W / 2, 150); og.fillStyle = '#ffe066'; og.fillText('ტელევიზორი ჯერ კიდევ გზაშია...', W / 2, 150);
    og.font = `700 26px ${KA}`; og.lineWidth = 6; og.strokeText('გამოგონილი კომედიური ისტორია', W / 2, H - 40); og.fillStyle = '#f1e3c4'; og.fillText('გამოგონილი კომედიური ისტორია', W / 2, H - 40);
    og.restore();
  }
  // subtitles
  for (const l of LINES) {
    if (t < l.start - 0.05 || t > l.start + l.dur + 0.35) continue;
    const a = clamp((t - l.start + 0.05) / 0.12) * clamp((l.start + l.dur + 0.35 - t) / 0.15);
    og.save(); og.globalAlpha = a; og.textAlign = 'center'; og.lineJoin = 'round';
    og.font = `700 50px ${KA}`;
    const ka = wrap(og, l.ka, W - 300);
    let y = H - 60 - (ka.length - 1) * 62;
    const name = l.who === 'nana' ? 'ნანა' : 'ზარი';
    og.font = `900 28px ${KA}`; og.fillStyle = l.who === 'nana' ? '#ffb4a2' : '#9ad1ff';
    og.lineWidth = 6; og.strokeStyle = 'rgba(0,0,0,0.85)';
    og.strokeText(name, W / 2, y - 58); og.fillText(name, W / 2, y - 58);
    og.font = `700 50px ${KA}`; og.lineWidth = 10;
    for (const line of ka) { og.strokeText(line, W / 2, y); og.fillStyle = '#ffffff'; og.fillText(line, W / 2, y); y += 62; }
    og.restore();
  }
  // fade from / to black
  const fade = Math.max(1 - clamp(t / 0.6), seg(t, M.end - 1.0, M.end));
  if (fade > 0) { og.fillStyle = `rgba(0,0,0,${fade})`; og.fillRect(0, 0, W, H); }
}

// ---------------------------------------------------------------- frame
export function renderAt(t) {
  t = clamp(t, 0, M.end);
  let shot = SHOTS[0];
  for (const s of SHOTS) if (t >= s[0]) shot = s;
  const set = shot[1];
  home.visible = set === 'home';
  den.visible = set === 'den';
  insert.visible = set === 'insert';
  denLight.visible = set === 'den';
  sun.visible = set === 'home';
  scene.background = new THREE.Color(set === 'den' ? 0x1a1816 : set === 'black' ? 0x140c08 : 0xf4dcb0);
  phone.visible = home.visible; card.visible = card.visible && home.visible; tea.visible = home.visible;
  handset.visible = den.visible;

  poseNana(t);
  poseProps(t);
  if (!home.visible) { phone.visible = card.visible = tea.visible = false; }
  poseHome(t);
  poseConfetti(t);
  if (home.visible) drawPhone(t);
  if (den.visible) poseGogi(t);
  if (insert.visible) { drawPhone(t); poseInsert(t); }

  camera.up.set(0, 1, 0);
  const [pos, target, fov] = shot[2](t);
  // a little handheld life
  pos.x += Math.sin(t * 0.9) * 0.012; pos.y += Math.sin(t * 1.3) * 0.008;
  // shake on the reaction pop
  if (t > M.reaction && t < M.reaction + 0.35) { const s = (1 - (t - M.reaction) / 0.35) * 0.02; pos.x += Math.sin(t * 90) * s; pos.y += Math.cos(t * 80) * s; }
  camera.position.copy(pos); camera.fov = fov; camera.updateProjectionMatrix(); camera.lookAt(target);
  poseDream(t);
  if (!home.visible) dream.visible = confetti.visible = false;
  renderer.render(scene, camera);
  drawOverlay(t);
}

export const overlayCanvas = overlay;
export { M };

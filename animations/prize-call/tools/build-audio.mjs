// Builds the English voice lines (espeak-ng), sound effects and music,
// mixes them into soundtrack.m4a and writes timeline.js (cue times plus
// per-frame mouth-opening envelopes for lip sync).
//
//   node animations/prize-call/tools/build-audio.mjs
//
// Needs espeak-ng and ffmpeg on PATH. The film is spoken in English with
// Georgian subtitles (the `ka` text below).
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = join(dirname(fileURLToPath(import.meta.url)), '..');
const TMP = mkdtempSync(join(tmpdir(), 'prize-call-'));
const SR = 44100;
const FPS = 30;

const VOICES = {
  nana: ['-v', 'en-us+f4', '-p', '75', '-s', '150', '-a', '170'],
  gogi: ['-v', 'en-us+m3', '-p', '30', '-s', '158', '-a', '170'],
};

const LINES = {
  alo:      { who: 'nana', ka: 'ალო? გისმენთ!', en: 'Hello? I\'m listening!' },
  congrats: { who: 'gogi', ka: 'გილოცავთ, ქალბატონო! თქვენ მოიგეთ ახალთახალი, უზარმაზარი ტელევიზორი!', en: 'Congratulations, madam! You\'ve won a brand-new, enormous television!' },
  vaime:    { who: 'nana', ka: 'ვაიმე! მართლა?! ტელევიზორი?! მე?!', en: 'Oh my! Really?! A television?! Me?!' },
  pay:      { who: 'gogi', ka: 'დიახ, დიახ! პრიზის მისაღებად, უბრალოდ, პატარა თანხა უნდა გადმოგვირიცხოთ.', en: 'Yes, yes! To claim your prize, you just need to send us a small amount.' },
  now:      { who: 'nana', ka: 'ახლავე, შვილო, ახლავე! აი, ბარათიც აქ მაქვს!', en: 'Right away, dear, right away! Here\'s my card!' },
  thanks:   { who: 'gogi', ka: 'ჰა, ჰა, ჰა! დიდი მადლობა, ქალბატონო! ტელევიზორი... აუცილებლად მოვა!', en: 'Ha, ha, ha! Thank you so much, madam! The television... will definitely arrive!' },
  luck:     { who: 'nana', ka: 'აი, ეს არის იღბალი! ახლა მთელი უბანი ჩემთან უყურებს ფეხბურთს!', en: 'Now that\'s luck! The whole neighbourhood will watch football at my place!' },
};

// ---------- wav io ----------
function readWav(file) {
  const b = readFileSync(file);
  let p = 12, rate = 22050, data = null;
  while (p + 8 <= b.length) {
    const id = b.toString('ascii', p, p + 4);
    let size = b.readUInt32LE(p + 4);
    if (id === 'fmt ') rate = b.readUInt32LE(p + 12);
    if (id === 'data') {
      if (p + 8 + size > b.length) size = b.length - p - 8;
      data = b.subarray(p + 8, p + 8 + size);
      break;
    }
    p += 8 + size + (size & 1);
  }
  const n = data.length >> 1;
  const src = new Float32Array(n);
  for (let i = 0; i < n; i++) src[i] = data.readInt16LE(i * 2) / 32768;
  // resample to SR (linear)
  const outN = Math.round(n * SR / rate);
  const out = new Float32Array(outN);
  for (let i = 0; i < outN; i++) {
    const x = i * rate / SR, i0 = Math.floor(x), f = x - i0;
    out[i] = (src[i0] || 0) * (1 - f) + (src[i0 + 1] || 0) * f;
  }
  return out;
}

function writeWav(file, ch) {
  const n = ch[0].length, nc = ch.length;
  const b = Buffer.alloc(44 + n * nc * 2);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * nc * 2, 4); b.write('WAVE', 8);
  b.write('fmt ', 12); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(nc, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * nc * 2, 28); b.writeUInt16LE(nc * 2, 32); b.writeUInt16LE(16, 34);
  b.write('data', 36); b.writeUInt32LE(n * nc * 2, 40);
  for (let i = 0; i < n; i++) for (let c = 0; c < nc; c++) {
    const v = Math.max(-1, Math.min(1, ch[c][i]));
    b.writeInt16LE(Math.round(v * 32767), 44 + (i * nc + c) * 2);
  }
  writeFileSync(file, b);
}

function trimSilence(s) {
  let a = 0, z = s.length - 1;
  while (a < z && Math.abs(s[a]) < 0.01) a++;
  while (z > a && Math.abs(s[z]) < 0.01) z--;
  return s.subarray(Math.max(0, a - 400), Math.min(s.length, z + 1200));
}

// ---------- voices ----------
const voice = {};
for (const [id, line] of Object.entries(LINES)) {
  const f = join(TMP, id + '.wav');
  execFileSync('espeak-ng', [...VOICES[line.who], '-w', f, line.en]);
  let s = trimSilence(readWav(f));
  // gentle warmth: one-pole low-pass to soften the synth edge
  const out = new Float32Array(s.length);
  let y = 0;
  for (let i = 0; i < s.length; i++) { y += 0.55 * (s[i] - y); out[i] = y; }
  voice[id] = out;
}
const dur = id => voice[id].length / SR;

// ---------- cue sheet ----------
const M = {};
M.ring = 3.0;
M.startle = 3.08;
M.grab = 4.4;
M.answer = 5.3;
M.alo = 5.6;
M.congrats = M.alo + dur('alo') + 0.5;
M.reaction = M.congrats + dur('congrats') + 0.15;
M.vaime = M.reaction + 1.0;
M.dance = M.vaime + dur('vaime') + 0.1;
M.pay = M.dance + 2.8;
M.now = M.pay + dur('pay') + 0.35;
M.card = M.now + 1.2;
M.bank = M.now + dur('now') + 0.3;
M.tap = M.bank + 2.7;
M.paid = M.tap + 0.35;
M.thanks = M.paid + 1.5;
M.luck = M.thanks + dur('thanks') + 0.5;
M.later = M.luck + dur('luck') + 1.4;
M.final = M.later + 2.4;
M.end = M.final + 7.0;

const lines = Object.entries(LINES).map(([id, l]) => {
  const s = voice[id];
  const win = Math.round(SR / FPS);
  const env = [];
  for (let i = 0; i < s.length; i += win) {
    let e = 0;
    for (let j = i; j < Math.min(s.length, i + win); j++) e += s[j] * s[j];
    env.push(Math.sqrt(e / win));
  }
  const sorted = [...env].sort((a, b) => a - b);
  const ref = sorted[Math.floor(sorted.length * 0.92)] || 1;
  const norm = env.map(v => Math.round(Math.min(1, Math.pow(v / ref, 0.8)) * 100) / 100);
  return { id, who: l.who, ka: l.ka, en: l.en, start: +M[id].toFixed(3), dur: +dur(id).toFixed(3), env: norm };
});

// ---------- synth helpers ----------
const total = Math.ceil(M.end * SR) + SR;
const L = new Float32Array(total), R = new Float32Array(total);
function add(buf, t0, gain = 1, pan = 0) {
  const o = Math.round(t0 * SR);
  const gl = gain * Math.min(1, 1 - pan), gr = gain * Math.min(1, 1 + pan);
  for (let i = 0; i < buf.length && o + i < total; i++) { L[o + i] += buf[i] * gl; R[o + i] += buf[i] * gr; }
}
function tone(len, fn) {
  const n = Math.round(len * SR), b = new Float32Array(n);
  for (let i = 0; i < n; i++) b[i] = fn(i / SR, i / n);
  return b;
}
const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
const pluck = (m, len = 0.5, bright = 1) => tone(len, (t) => {
  const f = mtof(m), e = Math.exp(-t * 7) * Math.min(1, t * 400);
  return e * (Math.sin(2 * Math.PI * f * t) + 0.35 * bright * Math.sin(4 * Math.PI * f * t) + 0.12 * bright * Math.sin(6 * Math.PI * f * t)) * 0.3;
});
const marimba = (m, len = 0.35) => tone(len, (t) => {
  const f = mtof(m), e = Math.exp(-t * 11) * Math.min(1, t * 600);
  return e * (Math.sin(2 * Math.PI * f * t) + 0.25 * Math.sin(2 * Math.PI * f * 3.9 * t) * Math.exp(-t * 30)) * 0.45;
});
const bell = (m, len = 1.2) => tone(len, (t) => {
  const f = mtof(m), e = Math.exp(-t * 3.2) * Math.min(1, t * 800);
  return e * (Math.sin(2 * Math.PI * f * t) + 0.5 * Math.sin(2 * Math.PI * f * 2.76 * t) * Math.exp(-t * 4) + 0.25 * Math.sin(2 * Math.PI * f * 5.4 * t) * Math.exp(-t * 8)) * 0.3;
});
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

// ---------- music bed ----------
// Cheerful home theme (G major, 112 bpm) and a sneaky minor theme for the caller's den.
const beat = 60 / 112;
const homeChords = [[55, 59, 62], [60, 64, 67], [62, 66, 69], [55, 59, 62]];
const denBass = [45, 48, 52, 51, 50, 48, 47, 44];
function homeMusic(a, b, gain) {
  for (let t = a, k = 0; t < b; t += beat / 2, k++) {
    const ch = homeChords[Math.floor(k / 8) % 4];
    add(pluck(ch[k % 3] + 12, 0.4), t, gain * 0.55, k % 2 ? 0.3 : -0.3);
    if (k % 4 === 0) add(pluck(ch[0] - 12, 0.7, 0.5), t, gain * 0.9);
    if (k % 8 === 6) add(marimba(ch[2] + 24, 0.3), t, gain * 0.35, 0.5);
  }
}
function denMusic(a, b, gain) {
  for (let t = a, k = 0; t < b; t += beat / 2, k++) {
    add(pluck(denBass[k % 8] - 12, 0.35, 0.3), t, gain * 1.1);
    if (k % 4 === 2) add(tone(0.06, (x) => (rnd() * 2 - 1) * Math.exp(-x * 60) * 0.25), t, gain * 0.6, 0.4);
  }
}
const gogiSpans = [];
for (const id of ['congrats', 'pay', 'thanks']) {
  const l = lines.find(x => x.id === id);
  gogiSpans.push([l.start - 0.2, l.start + l.dur + 0.4]);
}
homeMusic(0, M.ring, 0.55);
homeMusic(M.vaime, M.pay - 0.2, 0.6);
homeMusic(M.paid + 0.2, M.thanks - 0.2, 0.4);
homeMusic(M.luck, M.later, 0.4);
for (const [a, b] of gogiSpans) denMusic(a, b, 0.55);

// ---------- sound effects ----------
// ringtone: bright marimba riff, three times
const riff = [76, 79, 84, 79, 81, 83, 84];
for (let r = 0; r < 3; r++) riff.forEach((m, i) => {
  const t = M.ring + r * 0.8 + i * 0.09;
  if (t < M.answer) add(marimba(m, 0.25), t, 0.8, -0.2);
});
// startle "boing"
add(tone(0.5, (t) => Math.sin(2 * Math.PI * (180 * t + 260 * t * t * (1 - t))) * Math.exp(-t * 6) * 0.5), M.startle, 0.7);
// answer click
add(tone(0.04, (t) => (rnd() * 2 - 1) * Math.exp(-t * 120)), M.answer, 0.5);
// reaction: slide whistle up + record freeze sting
add(tone(0.9, (t, p) => Math.sin(2 * Math.PI * (400 * t + 900 * t * t)) * Math.sin(Math.PI * p) * 0.3), M.reaction, 0.7);
// celebration sparkle glissando + confetti pops
for (let i = 0; i < 14; i++) add(bell(72 + [0, 4, 7, 12][i % 4] + 12 * Math.floor(i / 4) % 24, 0.6), M.vaime + 0.2 + i * 0.06, 0.25, (i % 2) - 0.5);
for (let i = 0; i < 6; i++) add(tone(0.08, (t) => (rnd() * 2 - 1) * Math.exp(-t * 50) * 0.6), M.dance + i * 0.42, 0.45, (i % 3) * 0.4 - 0.4);
// card "shing"
add(tone(0.6, (t) => Math.sin(2 * Math.PI * 2600 * t) * Math.sin(2 * Math.PI * 3900 * t) * Math.exp(-t * 7) * 0.3), M.card, 0.6);
// keypad taps while typing the amount, then the confirm tap
for (let i = 0; i < 4; i++) add(tone(0.05, (t) => Math.sin(2 * Math.PI * 1200 * t) * Math.exp(-t * 80) * 0.4), M.bank + 0.9 + i * 0.32, 0.6);
add(tone(0.05, (t) => Math.sin(2 * Math.PI * 900 * t) * Math.exp(-t * 80) * 0.5), M.tap, 0.7);
// success chime + cash register
[72, 76, 79, 84].forEach((m, i) => add(bell(m, 1.0), M.paid + i * 0.08, 0.5));
add(tone(0.5, (t) => (Math.sin(2 * Math.PI * 3300 * t) + Math.sin(2 * Math.PI * 4400 * t)) * Math.exp(-t * 9) * 0.2), M.thanks + 0.1, 0.6);
// "one week later" whoosh
add(tone(1.0, (t, p) => (rnd() * 2 - 1) * Math.sin(Math.PI * p) * 0.25), M.later - 0.3, 0.6);
// crickets at the end
for (let t = M.final + 0.4; t < M.end - 0.3; t += 0.62) for (let k = 0; k < 3; k++)
  add(tone(0.035, (x) => Math.sin(2 * Math.PI * 4600 * x) * Math.sin(Math.PI * x / 0.035) * 0.18), t + k * 0.05, 0.6, 0.6);
// slow ticking clock at the end
for (let t = M.final; t < M.end; t += 1) add(tone(0.03, (x) => (rnd() * 2 - 1) * Math.exp(-x * 150) * 0.35), t, 0.4, -0.5);

// ---------- voices on top (music ducks under them) ----------
const duck = new Float32Array(total).fill(1);
for (const l of lines) {
  const a = Math.round((l.start - 0.15) * SR), b = Math.round((l.start + l.dur + 0.15) * SR);
  for (let i = Math.max(0, a); i < Math.min(total, b); i++) duck[i] = 0.45;
}
let d = 1;
for (let i = 0; i < total; i++) { d += (duck[i] - d) * 0.0008; L[i] *= d; R[i] *= d; }
for (const l of lines) add(voice[l.id], l.start, 1.0, l.who === 'gogi' ? 0.08 : -0.05);

// fade out + normalise
let peak = 0;
for (let i = 0; i < total; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
const g = 0.92 / peak;
const fadeA = Math.round((M.end - 1.2) * SR);
for (let i = 0; i < total; i++) {
  const f = i < fadeA ? 1 : Math.max(0, 1 - (i - fadeA) / (1.2 * SR));
  L[i] *= g * f; R[i] *= g * f;
}

const wav = join(TMP, 'mix.wav');
writeWav(wav, [L.subarray(0, Math.round(M.end * SR)), R.subarray(0, Math.round(M.end * SR))]);
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '160k', join(OUT, 'soundtrack.m4a')]);

for (const k of Object.keys(M)) M[k] = +M[k].toFixed(3);
writeFileSync(join(OUT, 'timeline.js'),
  '// Generated by tools/build-audio.mjs. Do not edit by hand.\n' +
  `export const FPS = ${FPS};\n` +
  `export const M = ${JSON.stringify(M, null, 1)};\n` +
  `export const LINES = ${JSON.stringify(lines)};\n`);
rmSync(TMP, { recursive: true, force: true });
console.log('duration', M.end.toFixed(2), 's');
for (const l of lines) console.log(l.id.padEnd(9), l.start.toFixed(2), l.dur.toFixed(2));

// fwrun: run an app on the REAL AREA512 firmware (official Area512Adv.bin) inside the
// emucard-adv ESP32-S3 emulator, headless. Ground truth for "does main.mpy run".
//
//   node emu/fwrun.mjs <app-dir>... [--keys "<script>"] [--out DIR] [--fw Area512Adv.bin] [--dump DIR]
//
// Each app dir is copied to /Area512_data/home/ai/<name>/ on a fresh card, then driven by a
// script of steps: plain characters type, and these tokens are special:
//   ENTER ESC BS SPACE UP DOWN LEFT RIGHT   keys      R / Q ...  uppercase = shift+letter
//   WAIT  ~0.25 s idle      SHOT:<name>  screenshot to <out>/<name>.png
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { createJitHost } from '../vendor/emucard-adv/src/jit.mjs';
import { FatVolume, formatImage } from '../vendor/emucard-adv/src/fat.js';
import { CODE, KEYS } from '../vendor/emucard-adv/src/keymap.js';

const EMU = new URL('../vendor/emucard-adv/', import.meta.url);
const FW_URL = 'https://raw.githubusercontent.com/engneer-hamachan/area512/main/firmware/Area512Adv.bin';
const FW_CACHE = new URL('../vendor/Area512Adv.bin', import.meta.url);

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); if (i < 0) return d; const v = args[i + 1]; args.splice(i, 2); return v; };
const outDir = opt('--out', 'emu/shots');
const fwPath = opt('--fw', null);
const keysArg = opt('--keys', null);
const dumpDir = opt('--dump', null);   // copy /Area512_data/data from the card here afterwards
const apps = args;
fs.mkdirSync(outDir, { recursive: true });

async function firmware() {
  if (fwPath) return new Uint8Array(fs.readFileSync(fwPath));
  if (!fs.existsSync(FW_CACHE)) {
    const res = await fetch(FW_URL);
    if (!res.ok) throw new Error('firmware download: HTTP ' + res.status);
    fs.writeFileSync(FW_CACHE, new Uint8Array(await res.arrayBuffer()));
  }
  return new Uint8Array(fs.readFileSync(FW_CACHE));
}

// --- tiny PNG writer (RGB565 frame -> RGB PNG)
const crcTable = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c; });
const crc = (b) => { let c = -1; for (const x of b) c = crcTable[(c ^ x) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };
function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type), data]);
  const c = Buffer.alloc(4); c.writeUInt32BE(crc(td));
  return Buffer.concat([len, td, c]);
}
function png(frame, scale = 2) {
  const w = frame[1] | (frame[2] << 8), h = frame[3] | (frame[4] << 8);
  const W = w * scale, H = h * scale;
  const raw = Buffer.alloc((W * 3 + 1) * H);
  for (let y = 0; y < H; y++) {
    raw[y * (W * 3 + 1)] = 0;
    for (let x = 0; x < W; x++) {
      const o = 5 + ((Math.floor(y / scale) * w + Math.floor(x / scale)) * 2);
      const v = frame[o] | (frame[o + 1] << 8);
      const r = v >> 11, g = (v >> 5) & 63, b = v & 31;
      const p = y * (W * 3 + 1) + 1 + x * 3;
      raw[p] = (r << 3) | (r >> 2); raw[p + 1] = (g << 2) | (g >> 4); raw[p + 2] = (b << 3) | (b >> 2);
    }
  }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

// --- keys
const charKey = new Map();
for (const k of KEYS) { if (k.name) continue; charKey.set(k.label, [k.code, false]); if (k.shifted) charKey.set(k.shifted, [k.code, true]); }
const FN_ARROWS = { UP: ';', DOWN: '.', LEFT: ',', RIGHT: '/' };

async function runApp(fw, appDirs, script, tag) {
  let wasm;
  const jit = createJitHost(() => wasm);
  const dec = new TextDecoder();
  const { instance } = await WebAssembly.instantiate(fs.readFileSync(new URL('vendor/esp32sim.wasm', EMU)), {
    env: { ...jit.imports, host_log: () => {}, host_profile_now: () => 0 },
  });
  wasm = instance.exports;
  const mem = () => new Uint8Array(wasm.memory.buffer);
  const withBytes = (b, f) => { const p = wasm.esp32sim_alloc(b.length); mem().set(b, p); try { return f(p, b.length); } finally { wasm.esp32sim_free(p, b.length); } };
  const emu = withBytes(new TextEncoder().encode('cardputer-adv'), (p, n) => wasm.esp32sim_new(p, n, 8, 0));
  wasm.esp32sim_set_jit(emu, 1);
  wasm.esp32sim_set_spin_skip(emu, 1);
  const ok = (what, rc) => { if (rc !== 0) throw new Error(what + ' failed: ' + rc); };

  // Card: the firmware seeds /Area512_data on first boot; our apps are pre-placed under it.
  const img = formatImage(64 * 1024 * 1024);
  const vol = new FatVolume(img);
  for (const p of ['/Area512_data', '/Area512_data/home', '/Area512_data/home/ai']) if (!vol.exists(p)) vol.mkdir(p);
  for (const dir of appDirs) {
    const name = path.basename(path.resolve(dir));
    const dst = '/Area512_data/home/ai/' + name;
    vol.mkdir(dst);
    // every plain file in the app folder (main.mpy, or main.manifest + its .mpy entries, README...)
    for (const f of fs.readdirSync(dir)) {
      const src = path.join(dir, f);
      if (fs.statSync(src).isFile()) vol.writeFile(dst + '/' + f, new Uint8Array(fs.readFileSync(src)));
    }
  }
  ok('rom', withBytes(fs.readFileSync(new URL('vendor/esp32s3_rev0_rom.elf', EMU)), (p, n) => wasm.esp32sim_load(emu, 0, p, n)));
  ok('firmware', withBytes(fw, (p, n) => wasm.esp32sim_load(emu, 5, p, n)));
  ok('sd', withBytes(vol.image ?? img, (p, n) => wasm.esp32sim_load(emu, 8, p, n)));
  ok('boot', wasm.esp32sim_boot(emu, 0));

  const hz = wasm.esp32sim_cpu_hz(emu);
  let serial = '', frame = null, t = 0;
  const run = (secs) => {
    t += secs;
    while (wasm.esp32sim_cycles(emu) < t * hz) {
      if (wasm.esp32sim_run(emu, 4_000_000, Date.now()) !== 0) throw new Error('chip stopped');
      const n = wasm.esp32sim_out_take(emu);
      for (let i = 0; i < n; i++) {
        const p = wasm.esp32sim_out_ptr(emu, i), len = wasm.esp32sim_out_len(emu, i);
        if (wasm.esp32sim_out_kind(emu, i) === 1) {
          const m = JSON.parse(dec.decode(mem().subarray(p, p + len)));
          if (m.t === 'serial') serial += m.data;
        } else if (mem()[p] === 1) frame = mem().slice(p, p + len);
      }
    }
  };
  const tap = (code, mods = []) => {
    for (const m of mods) wasm.esp32sim_key(emu, m, 1);
    wasm.esp32sim_key(emu, code, 1); run(0.05); wasm.esp32sim_key(emu, code, 0);
    for (const m of mods) wasm.esp32sim_key(emu, m, 0);
    run(0.12);
  };
  run(14);  // boot
  const shots = [];
  for (const tok of script.split(/\s+/).filter(Boolean)) {
    if (tok.startsWith('SHOT:')) {
      const f = path.join(outDir, `${tag}-${tok.slice(5)}.png`);
      if (frame) { fs.writeFileSync(f, png(frame)); shots.push(f); }
    } else if (tok === 'WAIT') run(0.25);
    else if (tok === 'ENTER') tap(CODE.Enter);
    else if (tok === 'BS') tap(CODE.Backspace);
    else if (tok === 'SPACE') tap(CODE.Space);
    else if (tok === 'ESC') tap(charKey.get('`')[0]);
    else if (FN_ARROWS[tok]) tap(charKey.get(FN_ARROWS[tok])[0], [CODE.Fn]);
    else for (const ch of tok) {
      const k = charKey.get(ch);
      if (!k) throw new Error('no key for ' + ch);
      tap(k[0], k[1] ? [CODE.Shift] : []);
    }
  }
  if (dumpDir) {
    // The firmware's writes live in the emulator's card image; read it back with the same FAT code.
    const len = wasm.esp32sim_sd_len(emu);
    const card = new FatVolume(mem().slice(wasm.esp32sim_sd_ptr(emu), wasm.esp32sim_sd_ptr(emu) + len));
    if (card.exists('/Area512_data/data')) {
      for (const e of card.walk('/Area512_data/data')) {
        const dst = path.join(dumpDir, e.path.replace('/Area512_data/', ''));
        if (e.isDir) fs.mkdirSync(dst, { recursive: true });
        else { fs.mkdirSync(path.dirname(dst), { recursive: true }); fs.writeFileSync(dst, card.readFile(e.path)); }
      }
    }
  }
  return { serial, shots };
}

const fw = await firmware();
const script = keysArg ?? 'SHOT:boot';
const res = await runApp(fw, apps, script, apps.length === 1 ? path.basename(path.resolve(apps[0])) : 'run');
fs.writeFileSync(path.join(outDir, 'serial.log'), res.serial);
console.log(res.shots.join('\n'));
console.log('--- serial tail ---\n' + res.serial.split('\n').slice(-25).join('\n'));

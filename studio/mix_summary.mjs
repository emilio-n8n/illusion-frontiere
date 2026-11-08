// Build the 60-second summary audio: music bed + archive SFX, no voice.
//
//   node studio/mix_summary.mjs
//   node studio/mix_summary.mjs --video out/summary/summary-60s-silent.mp4 \
//     --out out/summary/illusion-frontiere-60s.mp4
//
// Levels are relative; the final pass normalises to -14 LUFS / -1 dBTP.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const get = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const audioDir = path.join(root, 'out/summary');
fs.mkdirSync(audioDir, { recursive: true });

const musicDir = path.join(root, 'films/01-illusion-frontiere/audio/music');
const sfxDir = path.join(root, 'films/01-illusion-frontiere/audio/sfx');
const foleyDir = path.join(root, 'films/01-illusion-frontiere/audio/foley');

const run = (label, argv) => {
  const r = spawnSync('ffmpeg', argv, { stdio: ['ignore', 'ignore', 'pipe'] });
  if (r.status !== 0) {
    console.error(`✗ ${label}\n${r.stderr.toString().slice(-3000)}`);
    process.exit(r.status || 1);
  }
  console.log(`✓ ${label}`);
};

// --- 1. music bed: tension (M03) into the finale swell (M05) --------------
const musicOut = path.join(audioDir, 'music-bed.wav');
const musicGraph = [
  `[0:a]atrim=0:45.5,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.5,afade=t=out:st=42:d=3.5,volume=0.55,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[m3]`,
  `[1:a]atrim=55:75,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=2.5,afade=t=out:st=17.5:d=2.5,volume=0.5,adelay=43000|43000,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[m5]`,
  `[m3][m5]amix=inputs=2:duration=longest:normalize=0,atrim=0:60,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[out]`,
].join(';');
run('music bed', ['-y', '-loglevel', 'error',
  '-i', path.join(musicDir, 'M03.wav'),
  '-i', path.join(musicDir, 'M05.wav'),
  '-filter_complex', musicGraph, '-map', '[out]',
  '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2', musicOut]);

// --- 2. SFX bed: projector, transitions, drawer, stamp --------------------
const sfxOut = path.join(audioDir, 'sfx-bed.wav');
const sfxGraph = [
  // projector clatter, looped to 60 s and filtered to a distant hum
  `[0:a]atrim=0:60,volume=0.16,highpass=f=140,lowpass=f=4200,afade=t=in:st=0:d=2,afade=t=out:st=56:d=4,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[proj]`,

  // shimmer tail: four cues
  `[1:a]asplit=4[s1][s2][s3][s4]`,
  `[s1]atrim=0:3,asetpts=PTS-STARTPTS,afade=t=out:st=1.2:d=1.8,volume=0.16,adelay=4000|4000,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[sh1]`,
  `[s2]atrim=2:5,asetpts=PTS-STARTPTS,afade=t=out:st=1.2:d=1.8,volume=0.13,adelay=48000|48000,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[sh2]`,
  `[s3]atrim=4:7,asetpts=PTS-STARTPTS,afade=t=out:st=1.2:d=1.8,volume=0.11,adelay=52200|52200,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[sh3]`,
  `[s4]atrim=6:8.5,asetpts=PTS-STARTPTS,afade=t=out:st=1.2:d=1.3,volume=0.09,adelay=58800|58800,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[sh4]`,

  // sub drops at the two lab reveals
  `[2:a]asplit=2[d1][d2]`,
  `[d1]atrim=0:3,asetpts=PTS-STARTPTS,afade=t=out:st=0.8:d=2.2,volume=0.12,lowpass=f=170,adelay=19000|19000,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[sub1]`,
  `[d2]atrim=3:6,asetpts=PTS-STARTPTS,afade=t=out:st=0.8:d=2.2,volume=0.09,lowpass=f=170,adelay=26000|26000,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[sub2]`,

  // file-cabinet drawer under the dossier page
  `[3:a]atrim=6.2:7.4,asetpts=PTS-STARTPTS,volume=0.38,afade=t=out:st=0.7:d=0.5,adelay=41000|41000,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[drawer]`,

  // the stamp lands exactly at 45.22 (local 4.22 in scene 7)
  `[4:a]atrim=0:1.2,asetpts=PTS-STARTPTS,volume=0.5,afade=t=out:st=0.25:d=0.9,adelay=45220|45220,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[stamp]`,

  `[proj][sh1][sh2][sh3][sh4][sub1][sub2][drawer][stamp]amix=inputs=9:duration=longest:normalize=0,atrim=0:60,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[out]`,
].join(';');
run('sfx bed', ['-y', '-loglevel', 'error',
  '-stream_loop', '1', '-i', path.join(sfxDir, 'S14.wav'),
  '-i', path.join(sfxDir, 'S17.wav'),
  '-i', path.join(sfxDir, 'S12.wav'),
  '-i', path.join(foleyDir, 'drawer-454013-file_cabinet_metal_open_close_drawer_close_various.mp3'),
  '-i', path.join(foleyDir, 'stamp-470710-traditional_stamp_wav.mp3'),
  '-filter_complex', sfxGraph, '-map', '[out]',
  '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2', sfxOut]);

// --- 3. mix + loudness ---------------------------------------------------
const mixOut = path.join(audioDir, 'mix.wav');
const mixGraph = [
  `[0:a][1:a]amix=inputs=2:duration=longest:weights=1 1:normalize=0[m]`,
  `[m]loudnorm=I=-14:TP=-1.5:LRA=11,volume=-1.3dB,atrim=0:60,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a]`,
].join(';');
run('mix', ['-y', '-loglevel', 'error',
  '-i', musicOut, '-i', sfxOut,
  '-filter_complex', mixGraph, '-map', '[a]',
  '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2', mixOut]);

// --- 4. attach to the silent picture -------------------------------------
const video = get('--video', '');
const out = get('--out', 'out/summary/illusion-frontiere-60s.mp4');
if (video) {
  const videoPath = path.join(root, video);
  if (!fs.existsSync(videoPath)) {
    console.error(`✗ missing video ${video}`);
    process.exit(1);
  }
  run('mux', ['-y', '-loglevel', 'error',
    '-i', videoPath, '-i', mixOut,
    '-map', '0:v:0', '-map', '1:a:0',
    '-vf', 'scale=in_range=full:out_range=tv,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19',
    '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
    '-c:a', 'aac', '-b:a', '192k', '-shortest',
    '-movflags', '+faststart', path.join(root, out)]);
  console.log(`✓ ${out}`);
}

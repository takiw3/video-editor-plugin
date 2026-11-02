/* digital-zoom (layer: top). A camera viewfinder comes up and the shot steps in digitally, twice, then back out.
   Beat by beat:
     A          the viewfinder snaps on: corner brackets, REC blinking, 1.0×, the video's running timecode
     STEPS[k]   a hard digital step in (no ease), two frames of soft focus, the readout jumps to the new zoom
     BACK       one hard step back to 1.0×
     B          viewfinder off, camera back to 1
   Reach for it on "zoom in", "closer", "look at this", anything that inspects.
   Supply: nothing. ORIGIN is the point it zooms into (between the eyes is good; measure it on a still).
   Sound: a click on every step, a shutter on A.
   Change only these constants: */
var STEPS = [['digital', 0.05, 1.6], ['zoom', 0.42, 2.6]];  // [cue word, fallback (fraction of the window), scale]
var BACK = ['', 0.88];
var ORIGIN = [510, 1040];
var SOFT = 2;                                              // frames of soft focus on a step

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function cue(word, frac, after) {
  var w = word ? wordAt(word, after === undefined ? A : after) : null;
  return (w === null || w >= B) ? A + frac * (B - A) : w;
}
function pad(n) { return (n < 10 ? '0' : '') + n; }
function tc(f) { return pad(Math.floor(f / 108000)) + ':' + pad(Math.floor(f / 1800) % 60) + ':' + pad(Math.floor(f / 30) % 60) + ':' + pad(f % 30); }
function step(t, s) {
  var f = Math.round(t * FPS);
  tl.set('#fxcam', { scale: s, filter: 'blur(5px)' }, fq(f));
  tl.set('#fxcam', { filter: 'none' }, fq(f + SOFT));
  tl.set('#{{ID}}-x', { textContent: s.toFixed(1) + '×' }, fq(f));
  tl.fromTo('#{{ID}}-x', { scale: 1.12 }, { scale: 1, duration: 0.18, ease: 'power3.out', immediateRender: false }, fq(f));
}

tl.set('#fxcam', { transformOrigin: ORIGIN[0] + 'px ' + ORIGIN[1] + 'px', scale: 1, x: 0, y: 0, filter: 'none' }, q(A));
tl.fromTo('#{{ID}}-hud', { scale: 1.04 }, { scale: 1, duration: 0.2, ease: 'power3.out', immediateRender: false }, q(A));
var last = A - 0.01;
STEPS.forEach(function (s) {
  var t = Math.max(cue(s[0], s[1], last + 0.01), last + 0.25);
  step(t, s[2]); last = t;
});
step(Math.min(Math.max(cue(BACK[0], BACK[1], last + 0.01), last + 0.3), B - 0.1), 1);
tl.set('#fxcam', { scale: 1, filter: 'none' }, q(B));

var fA = Math.round(A * FPS), fB = Math.round(B * FPS);
for (var f = fA; f < fB; f++) {
  tl.set('#{{ID}}-tc', { textContent: tc(f) }, fq(f));
  if ((f - fA) % 15 === 0) tl.set('#{{ID}}-dot', { opacity: ((f - fA) / 15) % 2 ? 0.15 : 1 }, fq(f));
}

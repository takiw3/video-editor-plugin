/* snap-zoom (layer: top). A hard, fast punch-in that lands on the word.
   Beat by beat:
     STEPS[0]   the camera snaps in (0.12 s, expo out), a decaying shake and a light flash land with it
     STEPS[1]   it snaps closer the same way (add or remove steps freely)
     BACK       it snaps back out to the full frame
     B          the camera is back to 1 whatever happened
   Reach for it on a word that should hit: "boom", "this", a number, a name.
   Supply: nothing. ORIGIN is the point it zooms into (the face; measure it on a still).
   Sound: a whoosh-soft or a drum-hit on every step.
   Change only these constants: */
var STEPS = [['snap', 0.03, 1.30], ['zoom', 0.45, 1.58]];   // [cue word, fallback (fraction of the window), scale]
var BACK = ['', 0.86];                                      // [cue word, fallback]: back to the full frame
var ORIGIN = [540, 1060];                                   // the zoom point on the 1080x1920 frame
var SHAKE = 14;                                             // shake on a snap, px (decays over 6 frames)
var FLASH = 0.22;                                           // flash strength on a snap

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function cue(word, frac, after) {
  var w = word ? wordAt(word, after === undefined ? A : after) : null;
  return (w === null || w >= B) ? A + frac * (B - A) : w;
}
function kick(t0, px) {
  var f0 = Math.round(t0 * FPS);
  for (var k = 0; k < 6; k++) {
    var d = px * Math.pow(1 - k / 6, 1.5);
    tl.set('#fxcam', { x: d * Math.sin(k * 2.7 + f0), y: d * Math.cos(k * 3.1 + f0 * 0.7) }, fq(f0 + k));
  }
  tl.set('#fxcam', { x: 0, y: 0 }, fq(f0 + 6));
}

tl.set('#fxcam', { transformOrigin: ORIGIN[0] + 'px ' + ORIGIN[1] + 'px', scale: 1, x: 0, y: 0 }, q(A));
var prev = 1, last = A - 0.01;
STEPS.forEach(function (s, i) {
  var t = Math.max(cue(s[0], s[1], last + 0.01), last + 0.2);
  tl.fromTo('#fxcam', { scale: prev }, { scale: s[2], duration: 0.12, ease: 'expo.out', immediateRender: false }, q(t));
  kick(t, SHAKE * (1 + 0.15 * i));
  tl.fromTo('#{{ID}}-flash', { opacity: FLASH }, { opacity: 0, duration: 0.1, ease: 'none', immediateRender: false }, q(t));
  prev = s[2]; last = t;
});
var tBack = Math.min(Math.max(cue(BACK[0], BACK[1], last + 0.01), last + 0.25), B - 0.15);
tl.fromTo('#fxcam', { scale: prev }, { scale: 1, duration: 0.14, ease: 'power3.out', immediateRender: false }, q(tBack));
tl.set('#fxcam', { scale: 1, x: 0, y: 0 }, q(B));

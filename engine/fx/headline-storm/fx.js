/* headline-storm (layer: behind; needs a CUT_WINDOWS entry over the window). Headlines everywhere.
   Beat by beat:
     A + k*gap  strip k slams in from its side (0.2 s, expo out), tilted, the camera jolts
     hold       the strips sit behind the head, the head breaking them
     B - 0.2    they fly out the way they came
   Reach for it on "everyone's talking about", "it's all over the news", hype, a launch.
   Supply: nothing. HEADLINES [] takes the speaker's own lines around the window (4-5 words each, from words.json);
   or write them (their words or true facts only). The kickers are plain labels.
   Sound: a whoosh-soft or stamp on every strip.
   Change only these constants: */
var HEADLINES = [];                              // [] = the speaker's own lines
var KICKERS = ['BREAKING', 'JUST IN', 'LIVE', 'NEW', 'UPDATE'];
var ROWS = [[470, -4], [650, 3], [1150, -2.5], [830, 4], [1300, -3]];   // [top, tilt] per strip, in slam order
var SPREAD = 0.62;                               // strips slam in over this fraction of the window
var JOLT = 8;                                    // camera jolt per strip, px

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function lines() {
  if (HEADLINES.length) return HEADLINES;
  var out = [], cur = [];
  WORDS.forEach(function (w) {
    if (w[0] < A - 8 || w[0] > B + 8) return;
    cur.push(w[2].replace(/[.,!?;:]+$/, ''));
    if (cur.length >= 5 || /[.!?]$/.test(w[2])) { if (cur.length >= 2) out.push(cur.join(' ')); cur = []; }
  });
  if (cur.length >= 2) out.push(cur.join(' '));
  return out.length ? out : ['Your headline here'];
}
var H = lines().slice(0, ROWS.length);
var box = document.getElementById('{{ID}}-s');
H.forEach(function (h, i) {
  var b = document.createElement('div');
  b.className = '{{ID}}-b'; b.id = '{{ID}}-b' + i;
  b.setAttribute('data-layout-allow-overlap', ''); b.setAttribute('data-layout-allow-occlusion', '');
  b.style.top = ROWS[i][0] + 'px';
  b.innerHTML = '<span class="{{ID}}-k">' + KICKERS[i % KICKERS.length] + '</span><span class="{{ID}}-h">' + esc(h) + '</span>';
  box.appendChild(b);
});

H.forEach(function (h, i) {
  var id = '#{{ID}}-b' + i, side = i % 2 ? 1 : -1;
  var t = A + 0.04 + SPREAD * (B - A) * i / Math.max(1, H.length);
  gsap.set(id, { rotation: ROWS[i][1], x: side * 1700 });
  tl.fromTo(id, { x: side * 1700 }, { x: 0, duration: 0.2, ease: 'expo.out', immediateRender: false }, q(t));
  var f0 = Math.round((t + 0.1) * FPS);
  for (var k = 0; k < 5; k++) {
    var d = JOLT * Math.pow(1 - k / 5, 1.5);
    tl.set('#fxcam', { x: d * Math.sin(k * 2.9 + i), y: d * Math.cos(k * 3.3 + i) }, fq(f0 + k));
  }
  tl.set('#fxcam', { x: 0, y: 0 }, fq(f0 + 5));
  tl.to(id, { x: -side * 1700, duration: 0.2, ease: 'power3.in' }, q(B - 0.22 + 0.02 * i));
});
tl.set('#fxcam', { x: 0, y: 0 }, q(B));

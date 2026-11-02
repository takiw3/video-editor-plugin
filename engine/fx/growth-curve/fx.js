/* growth-curve (layer: behind; needs a CUT_WINDOWS entry over the window). Up and to the right, behind them.
   Beat by beat:
     A          the room dims to the dark ground (0.2 s), the grid fades up
     DRAW_ON    the curve draws over DRAW seconds (slow then steep), the dot riding its tip, the chip counting up
     B - 0.2    the ground lifts away
   Reach for it on "growth", "it took off", "10x", any number that went up.
   Supply: VALUE (the real number; SAMPLE stays true unless it is real and you can say where it's from), LABEL.
   Sound: a riser under the draw, a ding when the chip lands on VALUE.
   Change only these constants: */
var VALUE = 6, SUFFIX = '×', LABEL = 'GROWTH';   // the chip counts 1 -> VALUE
var SAMPLE = true;                               // shows "SAMPLE DATA": set false only for a real, sourced number
var DRAW_ON = 'curve', DRAW_AT = 0.12;           // cue word, fallback (fraction of the window)
var DRAW = 1.1;                                  // seconds the curve takes
var FROM = [70, 640], TO = [960, 380];           // where the curve starts and ends: above the head, so none of it hides
var BEND = 3.2;                                  // how steep the end is (exponential)
var GRID = 120;

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
var NS = 'http://www.w3.org/2000/svg', grid = document.getElementById('{{ID}}-grid');
for (var gx = GRID; gx < 1080; gx += GRID) { var l = document.createElementNS(NS, 'line'); l.setAttribute('x1', gx); l.setAttribute('x2', gx); l.setAttribute('y1', 220); l.setAttribute('y2', 1920); grid.appendChild(l); }
for (var gy = 240; gy < 1920; gy += GRID) { var m = document.createElementNS(NS, 'line'); m.setAttribute('x1', 0); m.setAttribute('x2', 1080); m.setAttribute('y1', gy); m.setAttribute('y2', gy); grid.appendChild(m); }
var P = [];
for (var i = 0; i <= 80; i++) {
  var u = i / 80, v = (Math.exp(BEND * u) - 1) / (Math.exp(BEND) - 1);
  P.push([FROM[0] + (TO[0] - FROM[0]) * u, FROM[1] + (TO[1] - FROM[1]) * v]);
}
var cv = document.getElementById('{{ID}}-cv');
cv.setAttribute('d', 'M' + P.map(function (p) { return p[0].toFixed(1) + ' ' + p[1].toFixed(1); }).join(' L'));
var LEN = cv.getTotalLength();
gsap.set(cv, { strokeDasharray: LEN, strokeDashoffset: LEN });
gsap.set('#{{ID}}-dot', { opacity: 0 });
if (!SAMPLE) gsap.set('#{{ID}}-sm', { display: 'none' });
document.getElementById('{{ID}}-l').textContent = LABEL;

tl.fromTo('#{{ID}}-g', { opacity: 0 }, { opacity: 1, duration: 0.2, ease: 'power1.out', immediateRender: false }, q(A));
tl.fromTo('#{{ID}}-grid', { opacity: 0 }, { opacity: 1, duration: 0.3, ease: 'none', immediateRender: false }, q(A + 0.1));
tl.fromTo('#{{ID}}-chip', { opacity: 0, y: -16 }, { opacity: 1, y: 0, duration: 0.25, ease: 'power3.out', immediateRender: false }, q(A + 0.15));
var w = wordAt(DRAW_ON, A), t0 = (w === null || w >= B) ? A + DRAW_AT * (B - A) : Math.max(w, A + 0.2);
var f0 = Math.round(t0 * FPS), n = Math.max(8, Math.round(DRAW * FPS)), fB = Math.round(B * FPS);
tl.set('#{{ID}}-dot', { opacity: 1 }, fq(f0));
for (var k = 0; k <= n && f0 + k < fB; k++) {
  var e = k / n, e2 = e < 0.5 ? 2 * e * e : 1 - Math.pow(-2 * e + 2, 2) / 2;
  var idx = Math.min(80, Math.round(e2 * 80));
  tl.set(cv, { strokeDashoffset: LEN * (1 - e2) }, fq(f0 + k));
  tl.set('#{{ID}}-dot', { attr: { cx: P[idx][0], cy: P[idx][1] } }, fq(f0 + k));
  var val = 1 + (VALUE - 1) * e2;
  tl.set('#{{ID}}-n', { textContent: (k === n ? String(VALUE) : val.toFixed(VALUE < 20 ? 1 : 0)) + SUFFIX }, fq(f0 + k));
}
tl.fromTo('#{{ID}}-chip', { scale: 1.12 }, { scale: 1, duration: 0.25, ease: 'back.out(2)', immediateRender: false }, fq(f0 + n));
tl.to('#{{ID}}-g', { opacity: 0, duration: 0.2, ease: 'power1.in' }, q(B - 0.2));

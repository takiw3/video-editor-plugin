/* paper-cutout (layer: behind; needs a CUT_WINDOWS entry over the window). The frame becomes a paper collage.
   Beat by beat:
     A          the accent ground slaps in on threes (3 frames each: 1.08, 1.03, 1); the speaker's cutout gets a
                sticker edge in the light colour and a flat paper shadow
     A + k*0.07 the shapes drop in one by one (on threes, a little overshoot)
     hold       everything boils: a fresh 2-4 px nudge and a small turn every HOLD frames, like stop motion
     B          the edge comes off, everything is gone (a hard cut back, as stop motion would)
   Reach for it on "paper", "cut out", "collage", "handmade", a playful line.
   Supply: nothing. Move the shapes in fx.html if they land on the face. A GRADES change inside the window resets the
   cutout's edge, so keep looks out of it.
   Sound: a stamp on A, pops (or paper-like clicks) on the shapes.
   Change only these constants: */
var HOLD = 3;                 // frames per stop-motion drawing
var EDGE = 9;                 // the sticker edge, px
var SHADOW = [12, 16];        // the flat paper shadow's offset, px
var N = 7;

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function rnd(i) { var x = Math.sin(i * 12.9898) * 43758.5453; return x - Math.floor(x); }
function tok(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
var fA = Math.round(A * FPS), fB = Math.round(B * FPS);

// the ground slaps in on threes
gsap.set('#{{ID}}-g', { transformOrigin: '580px 1000px' });
[1.08, 1.03, 1].forEach(function (s, k) { tl.set('#{{ID}}-g', { scale: s }, fq(fA + HOLD * k)); });

// the shapes: drop in on threes, then boil
for (var i = 0; i < N; i++) {
  var id = '#{{ID}}-s' + i, f0 = fA + 2 + Math.round(i * 0.07 * FPS);
  gsap.set(id, { opacity: 0 });
  tl.set(id, { opacity: 1, scale: 0.4, y: -60, rotation: -12 }, fq(f0));
  tl.set(id, { scale: 1.12, y: 8, rotation: 4 }, fq(f0 + HOLD));
  for (var f = f0 + 2 * HOLD, k = 0; f < fB; f += HOLD, k++) {
    tl.set(id, { scale: 1, x: (rnd(i * 97 + k) - 0.5) * 6, y: (rnd(i * 53 + k + 7) - 0.5) * 6, rotation: (rnd(i * 31 + k + 3) - 0.5) * 3 }, fq(f));
  }
}

// the speaker's sticker edge: on every cutout copy playing in the window
var L = tok('--c-light'), D = tok('--c-dark');
var base = (typeof COLOR === 'string' && COLOR && COLOR !== 'none') ? COLOR + ' ' : '';
var edge = base + ['drop-shadow(' + EDGE + 'px 0 0 ' + L + ')', 'drop-shadow(-' + EDGE + 'px 0 0 ' + L + ')',
                   'drop-shadow(0 ' + EDGE + 'px 0 ' + L + ')', 'drop-shadow(0 -' + EDGE + 'px 0 ' + L + ')',
                   'drop-shadow(' + SHADOW[0] + 'px ' + SHADOW[1] + 'px 0 color-mix(in srgb, ' + D + ' 35%, transparent))'].join(' ');
Array.prototype.forEach.call(document.querySelectorAll('video[src="subject.webm"]'), function (v) {
  var s = parseFloat(v.getAttribute('data-start')), d = parseFloat(v.getAttribute('data-duration'));
  if (s <= A + 0.05 && s + d >= A + 0.05) {
    tl.set(v, { filter: edge }, q(A));
    tl.set(v, { filter: base || 'none' }, q(B));
  }
});

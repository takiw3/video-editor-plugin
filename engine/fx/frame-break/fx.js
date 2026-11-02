/* frame-break (layer: cam). The picture cracks, then shatters.
   Beat by beat:
     HIT_ON     the crack: light lines draw out from IMPACT in CRACK seconds, the camera jolts
     + CRACK    the burst: the frame is now shards of a still of this moment, over the dark ground; they fly out from
                IMPACT, turning and falling, faster the nearer they were
     + BURST    the dark ground and the shards are gone: the live shot cuts back (end the window here or later)
   Reach for it on "break", "smash", "shatter", "breaking", a hard turn in the story.
   Supply: nothing: gen.py pulls frame.jpg (the moment of the burst) from clean.mp4 by itself when the effect is first
   used; rerun it (`ve py fx/<id>/gen.py <project> <id>`) if the window or HIT_ON moves.
   Sound: a key or click on the crack, impact-low and a scratch on the burst.
   Change only these constants: */
var HIT_ON = 'break', HIT_AT = 0.1;     // the crack lands on this word (fallback: fraction of the window)
var IMPACT = [770, 1190];               // where it breaks from
var CRACK = 0.2, BURST = 0.85;          // seconds
var RINGS = [0, 90, 230, 430, 700, 1050, 1500, 2300];
var SECTORS = 11;
var JOLT = 16;

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function rnd(i) { var x = Math.sin(i * 12.9898) * 43758.5453; return x - Math.floor(x); }
var w = wordAt(HIT_ON, A), tHit = (w === null || w >= B - 0.3) ? A + HIT_AT * (B - A) : w;
var tBurst = tHit + CRACK, tDone = Math.min(B, tBurst + BURST);
var ck = document.getElementById('{{ID}}-ck'), NS = 'http://www.w3.org/2000/svg';

// the crack: jagged lines out from the impact
for (var r = 0; r < 9; r++) {
  var a = 2 * Math.PI * r / 9 + rnd(r) * 0.5, pts = [IMPACT.slice()], x = IMPACT[0], y = IMPACT[1];
  for (var s = 1; s <= 4; s++) {
    var len = 70 + 120 * s * rnd(r * 7 + s), aa = a + (rnd(r * 11 + s) - 0.5) * 0.6;
    x += Math.cos(aa) * len; y += Math.sin(aa) * len; pts.push([x, y]);
  }
  var pl = document.createElementNS(NS, 'polyline');
  pl.setAttribute('points', pts.map(function (p) { return p[0].toFixed(0) + ',' + p[1].toFixed(0); }).join(' '));
  pl.setAttribute('pathLength', '1'); pl.setAttribute('stroke-dasharray', '1 1'); pl.setAttribute('stroke-dashoffset', '1');
  ck.appendChild(pl);
}
tl.fromTo('#{{ID}}-ck polyline', { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: CRACK * 0.8, ease: 'power3.out', stagger: 0.01, immediateRender: false }, q(tHit));
var fH = Math.round(tHit * FPS);
for (var k = 0; k < 6; k++) {
  var d = JOLT * Math.pow(1 - k / 6, 1.5);
  tl.set('#fxcam', { x: d * Math.sin(k * 2.7), y: d * Math.cos(k * 3.1) }, fq(fH + k));
}
tl.set('#fxcam', { x: 0, y: 0 }, fq(fH + 6));

// the shards: a radial grid of quads around the impact, each a piece of the still
var V = function (ri, si) {
  var jr = ri ? 1 + (rnd(ri * 31 + si) - 0.5) * 0.25 : 0, ja = (rnd(ri * 17 + si * 3) - 0.5) * 0.35;
  var a = 2 * Math.PI * si / SECTORS + ja;
  return [IMPACT[0] + Math.cos(a) * RINGS[ri] * jr, IMPACT[1] + Math.sin(a) * RINGS[ri] * jr];
};
var box = document.getElementById('{{ID}}-sh'), base = (typeof COLOR === 'string' && COLOR !== 'none') ? COLOR : 'none', n = 0;
for (var ri = 0; ri < RINGS.length - 1; ri++) {
  for (var si = 0; si < SECTORS; si++) {
    var P = [V(ri, si), V(ri, (si + 1) % SECTORS), V(ri + 1, (si + 1) % SECTORS), V(ri + 1, si)];
    if (si === SECTORS - 1) { P[1] = V(ri, 0); P[2] = V(ri + 1, 0); }
    var el = document.createElement('div');
    el.className = '{{ID}}-p'; el.id = '{{ID}}-p' + n;
    el.style.backgroundImage = 'url(fx/{{ID}}/frame.jpg)';
    el.style.clipPath = 'polygon(' + P.map(function (p) { return p[0].toFixed(1) + 'px ' + p[1].toFixed(1) + 'px'; }).join(', ') + ')';
    el.style.filter = base;
    box.appendChild(el);
    var cx = (P[0][0] + P[1][0] + P[2][0] + P[3][0]) / 4, cy = (P[0][1] + P[1][1] + P[2][1] + P[3][1]) / 4;
    var dx = cx - IMPACT[0], dy = cy - IMPACT[1], dl = Math.max(1, Math.hypot(dx, dy));
    var sp = (900 + 700 * rnd(n * 5 + 1)) / (1 + ri * 0.35);
    gsap.set(el, { transformOrigin: cx.toFixed(0) + 'px ' + cy.toFixed(0) + 'px' });
    tl.fromTo(el, { x: 0, y: 0, rotation: 0, scale: 1 },
              { x: dx / dl * sp, y: dy / dl * sp * 0.7 + 1500, rotation: (rnd(n * 9 + 2) - 0.5) * 220, scale: 0.9 + 0.5 * rnd(n * 3 + 4),
                duration: BURST, ease: 'power2.in', immediateRender: false }, q(tBurst + 0.012 * ri));
    n++;
  }
}
gsap.set(['#{{ID}}-g', '#{{ID}}-sh'], { opacity: 0 });
tl.set(['#{{ID}}-g', '#{{ID}}-sh'], { opacity: 1 }, q(tBurst));
tl.set('#{{ID}}-ck', { opacity: 0.55 }, q(tBurst));
tl.set(['#{{ID}}-g', '#{{ID}}-sh', '#{{ID}}-ck'], { opacity: 0 }, q(tDone));
tl.set('#fxcam', { x: 0, y: 0 }, q(B));

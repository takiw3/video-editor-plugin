/* zoom-portal (layer: cam). A window into the same moment opens beside them, then the camera dives through it.
   Beat by beat:
     OPEN_ON    the portal opens (back out, 0.3 s): a ring in the accent, a small synced copy of the shot inside
     hold       it breathes a little
     DIVE_ON    it swallows the frame in DIVE seconds, the copy growing to full size; it lands on the live shot
     B          nothing left to remove (the copy is the live frame by then)
   Reach for it on "portal", "go inside", "zoom into", "another world", a change of scene.
   Supply: nothing. PORTAL / R place it in empty space beside the head (measure on a still); FOCUS is the point of
   the shot shown in the middle of the portal (the face).
   Sound: a whoosh-soft on the open, whoosh-deep on the dive.
   Change only these constants: */
var OPEN_ON = 'portal', OPEN_AT = 0.06;     // cue word and fallback (fraction of the window)
var DIVE_ON = '', DIVE_AT = 0.68;
var DIVE = 0.55;                            // seconds the dive takes
var PORTAL = [190, 840], R = 165;           // the portal's centre and radius
var K = 0.34;                               // the copy's scale inside the portal
var FOCUS = [520, 1010];                    // the point of the shot at the portal's centre

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function cue(word, frac, after) {
  var w = word ? wordAt(word, after === undefined ? A : after) : null;
  return (w === null || w >= B) ? A + frac * (B - A) : w;
}
function backOut(p) { var s = 1.7; p -= 1; return 1 + (s + 1) * p * p * p + s * p * p; }
function io(p) { return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; }
function draw(f, cx, cy, r, k, ring) {
  tl.set('#{{ID}}-p', { clipPath: 'circle(' + r.toFixed(1) + 'px at ' + cx.toFixed(1) + 'px ' + cy.toFixed(1) + 'px)' }, fq(f));
  tl.set('#{{ID}}-v', { x: cx - FOCUS[0] * k, y: cy - FOCUS[1] * k, scale: k }, fq(f));
  tl.set('#{{ID}}-r', { x: cx - 100, y: cy - 100, scale: r / 100, opacity: ring }, fq(f));
}

gsap.set('#{{ID}}-v', { transformOrigin: '0px 0px' });
gsap.set('#{{ID}}-r', { opacity: 0 });
var tOpen = cue(OPEN_ON, OPEN_AT), tDive = Math.max(cue(DIVE_ON, DIVE_AT, tOpen + 0.4), tOpen + 0.5);
var fO = Math.round(tOpen * FPS), fD = Math.round(tDive * FPS), nD = Math.max(6, Math.round(DIVE * FPS));
var fB = Math.round(B * FPS), BIG = 2300;
draw(Math.round(A * FPS), PORTAL[0], PORTAL[1], 0, K, 0);
for (var f = fO; f < fD; f++) {
  var u = Math.min(1, (f - fO) / 9);
  var r = R * (u < 1 ? backOut(u) : 1 + 0.02 * Math.sin((f - fO) * 0.25));
  draw(f, PORTAL[0], PORTAL[1], Math.max(0, r), K, 1);
}
for (var g = 0; g <= nD && fD + g < fB; g++) {
  var e = io(g / nD);
  draw(fD + g, PORTAL[0] + (FOCUS[0] - PORTAL[0]) * e, PORTAL[1] + (FOCUS[1] - PORTAL[1]) * e,
       R * Math.pow(BIG / R, e), K + (1 - K) * e, Math.max(0, 1 - 2.2 * e));
}

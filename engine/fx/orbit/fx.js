/* orbit (layer: top). Tools circle the head like it's the centre of the edit.
   Beat by beat:
     A          the dashed ring opens out from the head (0.3 s)
     A + 0.08   the six tiles pop onto the ring one after another, already moving
     hold       they orbit: near side bigger and in front, far side smaller, hidden while behind the head
     B - 0.25   tiles pop out, the ring closes
   Reach for it when the line lists tools, says "everything around me", or as an opener over the hook.
   Supply: nothing. CENTER, RX, RY and HEAD come from a still: CENTER is the middle of the head, HEAD its width.
   Sound: a whoosh-soft on A, pops on the tiles.
   Change only these constants: */
var CENTER = [540, 1080];        // the ring's centre (middle of the head)
var RX = 380, RY = 140;          // the ring's radii
var TILT = -8;                   // ring tilt, degrees
var HEAD = 330;                  // head width: tiles on the far side are hidden inside it
var SPEED = 1.15;                // radians per second
var N = 6;
var TILE = 136;                  // tile size, px

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
var tr = TILT * Math.PI / 180, ct = Math.cos(tr), st = Math.sin(tr);
var el = document.getElementById('{{ID}}-el');
el.setAttribute('cx', CENTER[0]); el.setAttribute('cy', CENTER[1]);
el.setAttribute('rx', RX); el.setAttribute('ry', RY);
el.setAttribute('transform', 'rotate(' + TILT + ' ' + CENTER[0] + ' ' + CENTER[1] + ')');

gsap.set('#{{ID}}-ring', { transformOrigin: CENTER[0] + 'px ' + CENTER[1] + 'px' });
tl.fromTo('#{{ID}}-ring', { scale: 0.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: 'power3.out', immediateRender: false }, q(A));
tl.to('#{{ID}}-ring', { scale: 0.7, opacity: 0, duration: 0.22, ease: 'power2.in' }, q(B - 0.25));

var fA = Math.round(A * FPS), fB = Math.round(B * FPS);
for (var i = 0; i < N; i++) {
  var id = '#{{ID}}-t' + i, inner = id + ' .{{ID}}-in';
  gsap.set(inner, { scale: 0 });
  tl.fromTo(inner, { scale: 0 }, { scale: 1, duration: 0.28, ease: 'back.out(1.8)', immediateRender: false }, q(A + 0.08 + 0.06 * i));
  tl.to(inner, { scale: 0, duration: 0.18, ease: 'power2.in' }, q(B - 0.25 + 0.02 * i));
  for (var f = fA; f < fB; f++) {
    var a = 2 * Math.PI * i / N + SPEED * (f - fA) / FPS;
    var ex = RX * Math.cos(a), ey = RY * Math.sin(a);
    var x = CENTER[0] + ex * ct - ey * st, y = CENTER[1] + ex * st + ey * ct;
    var depth = (Math.sin(a) + 1) / 2;                       // 1 = nearest the camera
    var behind = Math.sin(a) < 0 && Math.abs(x - CENTER[0]) < HEAD / 2 + 40;
    tl.set(id, { x: x - TILE / 2, y: y - TILE / 2, scale: 0.7 + 0.42 * depth, opacity: behind ? 0 : 0.55 + 0.45 * depth, zIndex: depth > 0.5 ? 2 : 1 }, fq(f));
  }
}

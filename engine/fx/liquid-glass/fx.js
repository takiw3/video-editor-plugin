/* liquid-glass (layer: top). A drop of liquid glass slides over the shot.
   Beat by beat:
     A          the lens grows from nothing at PATH[0] (0.25 s)
     hold       it drifts along PATH (eased), magnifying MAG and rippling, the ripple moving every frame
     B - 0.2    it shrinks away where it ends
   Reach for it on "glass", "liquid", "smooth", "clean", a premium beat.
   Supply: nothing. PATH runs over the face by default; any path works.
   Sound: whoosh-soft at A, a soft riser across.
   Change only these constants: */
var PATH = [[160, 1250], [470, 1080], [760, 900], [930, 760]];   // the lens's centre over the window
var R = 230;                     // lens radius
var MAG = 1.32;                  // magnification inside the lens
var RIPPLE = 40;                 // displacement strength

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function io(p) { return p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; }
function at(u) {
  var s = Math.min(PATH.length - 1.0001, u * (PATH.length - 1)), i = Math.floor(s), k = s - i;
  return [PATH[i][0] + (PATH[i + 1][0] - PATH[i][0]) * k, PATH[i][1] + (PATH[i + 1][1] - PATH[i][1]) * k];
}
document.querySelector('#{{ID}}-warp feDisplacementMap').setAttribute('scale', RIPPLE);
var fA = Math.round(A * FPS), fB = Math.round(B * FPS), n = Math.max(1, fB - fA);
for (var f = fA; f < fB; f++) {
  var u = (f - fA) / n, p = at(io(u));
  var grow = Math.min(1, (f - fA) / 7.5), shrink = Math.min(1, (fB - f) / 6);
  var r = R * Math.min(grow < 1 ? 1 - Math.pow(1 - grow, 3) : 1, shrink) * (1 + 0.03 * Math.sin(f * 0.4));
  tl.set('#{{ID}}-lens', { clipPath: 'circle(' + r.toFixed(1) + 'px at ' + p[0].toFixed(1) + 'px ' + p[1].toFixed(1) + 'px)' }, fq(f));
  tl.set('#{{ID}}-w', { transformOrigin: p[0].toFixed(1) + 'px ' + p[1].toFixed(1) + 'px', scale: MAG }, fq(f));
  tl.set('#{{ID}}-rim', { x: p[0] - 100, y: p[1] - 100, scale: r / 100 }, fq(f));
  tl.set('#{{ID}}-turb', { attr: { baseFrequency: (0.006 + 0.0015 * Math.sin(f * 0.21)).toFixed(4) + ' ' + (0.009 + 0.002 * Math.cos(f * 0.17)).toFixed(4) } }, fq(f));
}

/* zoom-through (layer: top). A rush into the face that cuts to a closer shot.
   Beat by beat:
     CUT_ON - RUSH  the rush starts: scale 1 to PEAK, accelerating, with motion softness building
     CUT_ON         the peak: a flash, a hard cut to LAND[0], and it settles to LAND[1] (0.5 s)
     hold           a slow push to HOLD_TO until B
     B              back to the full frame (end the window on a sentence end or a picture cut)
   Reach for it on "zoom through", "go deeper", "inside", a change of topic.
   Supply: nothing. POINT is where it rushes in (an eye or a lens reads best; measure it on a still).
   Sound: whoosh-long under the rush, a boom-low on the cut.
   Change only these constants: */
var CUT_ON = 'through';           // the cut lands on this word
var AT = 0.35;                    // fallback for the cut (fraction of the window)
var RUSH = 0.5;                   // seconds of rush before the cut
var PEAK = 3.4;                   // scale at the peak of the rush
var LAND = [2.3, 1.28];           // the cut lands here, and settles to here
var HOLD_TO = 1.32;               // slow push while it holds
var POINT = [405, 1045];          // the point it rushes into
var FLASH = 0.6;

var w = wordAt(CUT_ON, A);
var tCut = (w === null || w >= B) ? A + AT * (B - A) : w;
tCut = Math.max(tCut, A + RUSH);
var t0 = tCut - RUSH;
tl.set('#fxcam', { transformOrigin: POINT[0] + 'px ' + POINT[1] + 'px', scale: 1, x: 0, y: 0, filter: 'none' }, q(A));
tl.fromTo('#fxcam', { scale: 1, filter: 'blur(0px)' }, { scale: PEAK, filter: 'blur(9px)', duration: RUSH, ease: 'power3.in', immediateRender: false }, q(t0));
tl.set('#fxcam', { scale: LAND[0], filter: 'none' }, q(tCut));
tl.fromTo('#fxcam', { scale: LAND[0] }, { scale: LAND[1], duration: 0.5, ease: 'power3.out', immediateRender: false }, q(tCut));
if (B - tCut > 0.55) {
  tl.fromTo('#fxcam', { scale: LAND[1] }, { scale: HOLD_TO, duration: B - tCut - 0.5, ease: 'none', immediateRender: false }, q(tCut + 0.5));
}
tl.fromTo('#{{ID}}-flash', { opacity: FLASH }, { opacity: 0, duration: 0.13, ease: 'power1.out', immediateRender: false }, q(tCut));
tl.set('#fxcam', { scale: 1, filter: 'none' }, q(B));

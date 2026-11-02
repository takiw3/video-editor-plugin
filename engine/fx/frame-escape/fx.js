/* frame-escape (layer: behind; needs a CUT_WINDOWS entry over the window). They step out of their own video.
   Beat by beat:
     A          the shot shrinks to K and tilts ROT (0.34 s, eased) while a dark blind slides down to EDGE: above that
                line the room goes dark, the white frame line lands on it, and the head stays in front, out of the frame
     hold       a slow drift
     B - 0.34   it all grows back and the blind lifts
   Reach for it on "breaking out", "escape", "outside the box", "step out of".
   Supply: EDGE, the frame's top edge on the full frame: just under the chin is the classic (measure on a still).
   Sound: a whoosh-soft in and out, a stamp as the frame lands.
   Change only these constants: */
var EDGE = 1330;               // the photo's top edge on the 1080x1920 frame
var K = 0.72;                  // the photo's scale
var ROT = -3.5;                // its tilt, degrees
var CENTER = [540, 1060];      // it shrinks about this point
var IN = 0.34;                 // seconds in (and out)
var DRIFT = 1.02;

var tOut = Math.max(A + IN + 0.1, B - IN);
gsap.set('#{{ID}}-blind', { y: 0 });
tl.set('#fxcam', { transformOrigin: CENTER[0] + 'px ' + CENTER[1] + 'px', scale: 1, rotation: 0, x: 0, y: 0 }, q(A));
tl.fromTo('#fxcam', { scale: 1, rotation: 0 }, { scale: K, rotation: ROT, duration: IN, ease: 'power3.inOut', immediateRender: false }, q(A));
tl.fromTo('#fxcam', { scale: K }, { scale: K * DRIFT, duration: Math.max(0.1, tOut - A - IN), ease: 'none', immediateRender: false }, q(A + IN));
tl.fromTo('#{{ID}}-blind', { y: 0 }, { y: EDGE, duration: IN, ease: 'power3.inOut', immediateRender: false }, q(A));
tl.fromTo('#{{ID}}-sides', { opacity: 0 }, { opacity: 1, duration: IN * 0.6, ease: 'none', immediateRender: false }, q(A + IN * 0.4));
tl.fromTo('#fxcam', { scale: K * DRIFT, rotation: ROT }, { scale: 1, rotation: 0, duration: IN, ease: 'power3.inOut', immediateRender: false }, q(tOut));
tl.fromTo('#{{ID}}-blind', { y: EDGE }, { y: 0, duration: IN, ease: 'power3.inOut', immediateRender: false }, q(tOut));
tl.to('#{{ID}}-sides', { opacity: 0, duration: IN * 0.5, ease: 'none' }, q(tOut));
tl.set('#fxcam', { scale: 1, rotation: 0 }, q(B));

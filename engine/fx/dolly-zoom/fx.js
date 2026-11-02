/* dolly-zoom (layer: behind; needs a CUT_WINDOWS entry over the window). The room moves, the speaker doesn't.
   Beat by beat:
     A + 0.06   the room starts to pull away from Z[0] to Z[1] (eased in and out) while the speaker holds still
     B - 0.04   it has arrived; at B everything is back (end the window on a sentence end)
   Reach for it on "dolly zoom", "vertigo", "it hit me", "everything changed", a realisation.
   Supply: nothing, but it needs a room with depth behind the speaker; a flat wall shows little. Z below 1 pulls the
   room away (keeps the edges filled by the soft copy), above 1 pushes it in.
   Sound: a riser-long or whoosh-long across the move.
   Change only these constants: */
var Z = [1.0, 0.8];           // the room's scale from, to
var ORIGIN = [540, 1920];     // it scales about this point (bottom centre keeps the speaker's copy hidden behind them)
var SOFT = 'blur(22px) brightness(0.82)';

var base = (typeof COLOR === 'string' && COLOR && COLOR !== 'none') ? COLOR + ' ' : '';
gsap.set('#{{ID}}-u', { filter: base + SOFT, scale: 1.06, transformOrigin: '540px 960px' });
gsap.set('#{{ID}}-v', { transformOrigin: ORIGIN[0] + 'px ' + ORIGIN[1] + 'px', scale: Z[0] });
tl.fromTo('#{{ID}}-v', { scale: Z[0] }, { scale: Z[1], duration: Math.max(0.3, B - A - 0.1), ease: 'power2.inOut', immediateRender: false }, q(A + 0.06));

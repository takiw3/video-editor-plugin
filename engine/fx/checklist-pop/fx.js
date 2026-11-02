/* checklist-pop (layer: top). The things they list pop up as ticked pills next to their head.
   Beat by beat:
     ITEMS[k]   a pill pops in (back out) on its word, the tick draws 0.08 s later, the camera bumps 1.025 and settles
     B - 0.22   the pills slide out right, one after another
   Reach for it on any short list: "edit, captions, effects", "done, done, done", steps that are finished.
   Supply: the items in their words, each with the word it lands on. X / Y place the stack beside the head (on the
   side with more room; measure on a still). Keep it to 2-5 items.
   Sound: a pop on every item, a tick on every check.
   Change only these constants: */
var ITEMS = [['Edit', 'edit'], ['Captions', 'caption']];   // [label, the word it pops on]; fallback: spread over the window
var X = 660, Y = 860, GAP = 112;                           // the first pill's left / top, and the gap down
var BUMP = 1.025;                                          // camera bump per pop (1 = none)
var FACE = [540, 1080];                                    // the bump grows from here

var list = document.getElementById('{{ID}}-list');
ITEMS.forEach(function (it, i) {
  var p = document.createElement('div');
  p.className = '{{ID}}-p'; p.id = '{{ID}}-p' + i;
  p.setAttribute('data-layout-allow-overlap', ''); p.setAttribute('data-layout-allow-occlusion', '');
  p.style.left = X + 'px'; p.style.top = (Y + GAP * i) + 'px';
  p.innerHTML = '<span class="{{ID}}-k"><svg viewBox="0 0 30 30"><path id="{{ID}}-c' + i + '" d="M7 15.5l5.5 5.5L23.5 9" pathLength="1" stroke-dasharray="1 1"/></svg></span>' + it[0];
  list.appendChild(p);
});

var last = A;
tl.set('#fxcam', { transformOrigin: FACE[0] + 'px ' + FACE[1] + 'px' }, q(A));
ITEMS.forEach(function (it, i) {
  var w = it[1] ? wordAt(it[1], last) : null;
  var t = (w === null || w >= B - 0.3) ? A + (0.08 + 0.7 * i / Math.max(1, ITEMS.length)) * (B - A) : w;
  t = Math.max(t, last + (i ? 0.18 : 0)); last = t + 0.01;
  var p = '#{{ID}}-p' + i;
  gsap.set(p, { opacity: 0, scale: 0.4, transformOrigin: '44px 44px' });
  gsap.set('#{{ID}}-c' + i, { strokeDashoffset: 1 });
  tl.fromTo(p, { opacity: 0, scale: 0.4 }, { opacity: 1, scale: 1, duration: 0.3, ease: 'back.out(1.8)', immediateRender: false }, q(t));
  tl.fromTo('#{{ID}}-c' + i, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.16, ease: 'power2.out', immediateRender: false }, q(t + 0.08));
  if (BUMP !== 1) {
    tl.fromTo('#fxcam', { scale: 1 }, { scale: BUMP, duration: 0.06, ease: 'power2.out', immediateRender: false }, q(t));
    tl.to('#fxcam', { scale: 1, duration: 0.2, ease: 'power2.inOut' }, q(t + 0.06));
  }
  tl.to(p, { opacity: 0, x: 60, duration: 0.18, ease: 'power2.in' }, q(B - 0.22 + 0.03 * i));
});
tl.set('#fxcam', { scale: 1 }, q(B));

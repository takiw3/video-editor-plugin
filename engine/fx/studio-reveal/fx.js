/* studio-reveal (layer: behind; needs a CUT_WINDOWS entry over the window). Their room turns into a studio.
   Beat by beat:
     A          lights out: the room cuts to the dark ground in DARK seconds
     ON_ON      the left softbox flickers on (4 frames), the right one LAG later
     SIGN       the sign flickers and lights: filled accent, light type
     B - 0.15   the studio drops away, back to the room
   Reach for it on "studio", "set", "production", "level up", a reveal.
   Supply: SIGN text (a plain label). PANELS sit beside the head; move them if the head is off centre.
   Sound: a switch-off on A, a switch-off (reversed feel) or click on each panel, a ding on the sign.
   Change only these constants: */
var SIGN = 'ON AIR';
var ON_ON = 'reveal', ON_AT = 0.18;          // the first panel lights on this word (fallback: fraction of the window)
var DARK = 0.14;                             // seconds for the lights to go out
var LAG = 0.2;                               // the second panel, after the first
var SIGN_AFTER = 0.45;                       // the sign, after the first panel

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function flick(sel, t, to) {
  var f = Math.round(t * FPS), seq = [0.35, 0, 0.8, 0.2, 1];
  seq.forEach(function (o, k) { tl.set(sel, { opacity: to === undefined ? o : o * to }, fq(f + k)); });
}
document.getElementById('{{ID}}-sign').textContent = SIGN;
gsap.set(['#{{ID}}-l', '#{{ID}}-r'], { opacity: 0 });
tl.fromTo('#{{ID}}-g', { opacity: 0 }, { opacity: 1, duration: DARK, ease: 'none', immediateRender: false }, q(A));
var w = wordAt(ON_ON, A), t = (w === null || w >= B) ? A + ON_AT * (B - A) : Math.max(w, A + DARK + 0.05);
flick('#{{ID}}-l', t);
flick('#{{ID}}-r', t + LAG);
var ts = Math.min(t + SIGN_AFTER, B - 0.4);
flick('#{{ID}}-sign', ts);
tl.set('#{{ID}}-sign', { backgroundColor: 'var(--c-accent)', color: 'var(--c-light)' }, q(ts + 5 / FPS));
tl.to('#{{ID}}-g', { opacity: 0, duration: 0.15, ease: 'power1.in' }, q(B - 0.15));

/* phone-mockup (layer: cam). The video becomes a post playing on a phone.
   Beat by beat:
     A          the frame shrinks into the phone (0.45 s, eased): the full frame scales to K and tilts TILT, the dark
                ground comes up around it
     + 0.35     the UI fades up on the screen: side actions, the handle, the progress bar running
     hold       a slow push on the phone
     B - 0.4    it grows back to the full frame
   Reach for it on "phone", "on your feed", "when you post it", "scrolling".
   Supply: HANDLE (the creator's real handle, or '' for none).
   Sound: a whoosh-soft in, the same out.
   Change only these constants: */
var HANDLE = '';                 // '@yourhandle' or '' to leave it off
var K = 0.42;                    // the phone's scale
var TILT = -3;                   // degrees
var CENTER = [540, 1010];        // where the phone's centre lands
var PUSH = 1.05;                 // slow push while it holds

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
var h = document.getElementById('{{ID}}-h');
h.textContent = HANDLE; if (!HANDLE) h.style.display = 'none';
gsap.set('#{{ID}}-dev', { transformOrigin: '540px 960px' });
gsap.set('#{{ID}}-ui', { opacity: 0 });
gsap.set('#{{ID}}-pf', { scaleX: 0 });
var X = CENTER[0] - 540, Y = CENTER[1] - 960, tOut = Math.max(A + 0.8, B - 0.4);
tl.fromTo('#{{ID}}-g', { opacity: 0 }, { opacity: 1, duration: 0.3, ease: 'none', immediateRender: false }, q(A));
tl.fromTo('#{{ID}}-dev', { x: 0, y: 0, scale: 1, rotation: 0 }, { x: X, y: Y, scale: K, rotation: TILT, duration: 0.45, ease: 'power3.inOut', immediateRender: false }, q(A));
if (tOut - A > 0.5) tl.fromTo('#{{ID}}-dev', { scale: K }, { scale: K * PUSH, duration: tOut - A - 0.45, ease: 'none', immediateRender: false }, q(A + 0.45));
tl.fromTo('#{{ID}}-ui', { opacity: 0 }, { opacity: 1, duration: 0.2, ease: 'none', immediateRender: false }, q(A + 0.35));
tl.fromTo('#{{ID}}-pf', { scaleX: 0 }, { scaleX: 1, duration: Math.max(0.2, B - A - 0.4), ease: 'none', immediateRender: false }, q(A + 0.35));
tl.to('#{{ID}}-ui', { opacity: 0, duration: 0.12, ease: 'none' }, q(tOut));
tl.fromTo('#{{ID}}-dev', { x: X, y: Y, scale: K * PUSH, rotation: TILT }, { x: 0, y: 0, scale: 1, rotation: 0, duration: 0.4, ease: 'power3.inOut', immediateRender: false }, q(tOut));
tl.to('#{{ID}}-g', { opacity: 0, duration: 0.3, ease: 'none' }, q(tOut + 0.1));

/* broll-overlay (layer: top). Show the thing they're talking about, and show that it's B-roll.
   Beat by beat:
     A          the timeline drops in above (two tracks building left to right), the card slides up (0.35 s)
     hold       the clip plays; the playhead runs across both tracks
     B - 0.3    the card slides back down, the timeline folds away
   Reach for it whenever they mention their screen, a product, a place: anything a clip shows better.
   Supply: the clip: `ve py fx/<id>/gen.py <project> <id> <clip file> [start seconds]` cuts it into this folder,
   points the card at it and turns the placeholder chip off. Labels below are plain labels.
   Sound: a whoosh-soft on the slide up and down.
   Change only these constants: */
var PLACEHOLDER = true;                 // gen.py sets this false when the real clip is in
var TITLE = 'B-ROLL';                   // the card's title bar
var TRACKS = ['B-ROLL', 'TALKING HEAD'];

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
document.getElementById('{{ID}}-t').textContent = TITLE;
document.getElementById('{{ID}}-l1').textContent = TRACKS[0];
document.getElementById('{{ID}}-l2').textContent = TRACKS[1];
if (!PLACEHOLDER) gsap.set('#{{ID}}-ph-chip', { display: 'none' });

tl.fromTo('#{{ID}}-card', { y: 1300 }, { y: 0, duration: 0.35, ease: 'power3.out', immediateRender: false }, q(A));
tl.fromTo('#{{ID}}-tlb', { opacity: 0, y: -20 }, { opacity: 1, y: 0, duration: 0.25, ease: 'power3.out', immediateRender: false }, q(A + 0.05));
tl.fromTo(['#{{ID}}-b1', '#{{ID}}-b2'], { scaleX: 0 }, { scaleX: 1, duration: 0.35, ease: 'power3.out', stagger: 0.06, immediateRender: false }, q(A + 0.1));
var fA = Math.round((A + 0.15) * FPS), fE = Math.round((B - 0.3) * FPS);
for (var f = fA; f <= fE; f++) tl.set('#{{ID}}-ph', { x: 690 * (f - fA) / Math.max(1, fE - fA) }, fq(f));
tl.to('#{{ID}}-card', { y: 1300, duration: 0.3, ease: 'power3.in' }, q(B - 0.3));
tl.to('#{{ID}}-tlb', { opacity: 0, y: -20, duration: 0.2, ease: 'power2.in' }, q(B - 0.25));

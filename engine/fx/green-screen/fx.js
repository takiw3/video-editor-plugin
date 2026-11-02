/* green-screen (layer: behind; needs a CUT_WINDOWS entry over the window). They're suddenly on a green screen.
   Beat by beat:
     DOWN_ON    the green pulls down from the top in DROP frames (eased), a darker hem leading
     hold       green behind them, soft folds
     B - DROP   it rolls back up
   Reach for it on "green screen", "any background", "put me anywhere".
   Supply: nothing.
   Sound: a whoosh-soft down, the same up.
   Change only these constants: */
var CHROMA = '#1FC24A';           // chroma green: the subject of the effect, not a brand colour
var DOWN_ON = 'green', DOWN_AT = 0.04;
var DROP = 7;                     // frames for the pull down (and the roll up)

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function io(p) { return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; }
gsap.set('#{{ID}}-g', { backgroundColor: CHROMA });
var w = wordAt(DOWN_ON, A), t = (w === null || w >= B - 0.5) ? A + DOWN_AT * (B - A) : w;
var f0 = Math.round(t * FPS), fB = Math.round(B * FPS);
tl.set('#{{ID}}-g', { clipPath: 'inset(0px 0px 1920px 0px)' }, q(A));
for (var k = 1; k <= DROP; k++) {
  tl.set('#{{ID}}-g', { clipPath: 'inset(0px 0px ' + (1920 * (1 - io(k / DROP))).toFixed(1) + 'px 0px)' }, fq(f0 + k - 1));
  tl.set('#{{ID}}-g', { clipPath: 'inset(0px 0px ' + (1920 * io(k / DROP)).toFixed(1) + 'px 0px)' }, fq(fB - DROP + k - 1));
}
gsap.set('#{{ID}}-hem', { y: 0 });

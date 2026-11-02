/* checklist (layer: top; hide the captions over it with KARAOKE["hide"], or put it on "over"). Everything, ticked.
   Beat by beat:
     A          the dark ground comes up (0.2 s), the list lands in two columns, every box empty
     A + 0.35   boxes tick one after another until B - 0.4 (accent fill, a check), the counter counting with them
     B - 0.2    the ground drops away
   Reach for it at the end of a list video ("that's all 20"), a recap, "everything you need".
   Supply: nothing for a list video: ITEMS [] lists the other effects in this video in the order they play. Or give
   your own items (their words). LINE is an optional line under the counter, their words.
   Sound: a tick on every box (or a clicks-run across), a ding on the last.
   Change only these constants: */
var ITEMS = [];                  // [] = the names of the other effects in this video
var LINE = '';                   // an optional line under the counter
var ROW = 86;                    // row height
var START = 0.35;                // the first tick, after A

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function nice(id) {
  var s = id.replace(/-\d+$/, '').replace(/-/g, ' ');
  return s.charAt(0).toUpperCase() + s.slice(1);
}
var items = ITEMS.length ? ITEMS : FXS.filter(function (f) { return f.id !== '{{ID}}' && f.at < A && !/front$|transitions$/.test(f.id); })
  .sort(function (a, b) { return a.at - b.at; }).map(function (f) { return nice(f.id); });
if (!items.length) items = ['Item one', 'Item two', 'Item three'];
var per = Math.ceil(items.length / 2), list = document.getElementById('{{ID}}-list');
document.getElementById('{{ID}}-of').textContent = '/ ' + items.length;
var ln = document.getElementById('{{ID}}-ln'); ln.textContent = LINE; if (!LINE) ln.style.display = 'none';
items.forEach(function (label, i) {
  var r = document.createElement('div');
  r.className = '{{ID}}-r'; r.id = '{{ID}}-r' + i;
  r.setAttribute('data-layout-allow-overlap', '');
  r.style.left = (i < per ? 0 : 480) + 'px'; r.style.top = ((i % per) * ROW) + 'px';
  r.innerHTML = '<span class="{{ID}}-bx" id="{{ID}}-b' + i + '"><svg viewBox="0 0 26 26"><path d="M5 13.5l5 5L21 7"/></svg></span>' + label;
  list.appendChild(r);
});

tl.fromTo('#{{ID}}-g', { opacity: 0 }, { opacity: 1, duration: 0.2, ease: 'none', immediateRender: false }, q(A));
tl.fromTo(['#{{ID}}-top', '#{{ID}}-ln', '#{{ID}}-list'], { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.3, ease: 'power3.out', stagger: 0.05, immediateRender: false }, q(A + 0.05));
var t0 = A + START, t1 = Math.max(t0 + 0.1, B - 0.4), dt = (t1 - t0) / Math.max(1, items.length);
items.forEach(function (label, i) {
  var t = t0 + dt * i, b = '#{{ID}}-b' + i;
  tl.set(b, { backgroundColor: 'var(--c-accent)', borderColor: 'var(--c-accent)' }, q(t));
  tl.set(b + ' svg', { opacity: 1 }, q(t));
  tl.set('#{{ID}}-r' + i, { color: 'var(--c-light)' }, q(t));
  tl.fromTo(b, { scale: 1.3 }, { scale: 1, duration: 0.16, ease: 'power3.out', immediateRender: false }, q(t));
  tl.set('#{{ID}}-n', { textContent: String(i + 1) }, q(t));
});
tl.to('#{{ID}}-g', { opacity: 0, duration: 0.2, ease: 'none' }, q(B - 0.2));

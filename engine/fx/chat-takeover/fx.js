/* chat-takeover (layer: cam). The video is handed to an AI chat, then comes back out.
   Beat by beat:
     A          the dark ground cuts in, the chat window rises (0.25 s), the frame shrinks into the attachment
                (0.4 s, eased) and keeps playing in sync
     TYPE_ON    the instruction types into the message, character by character, a cursor at its end
     B - 0.38   the attachment grows back out to the full frame, the chat drops away
   Reach for it on "I told the AI", "I asked Claude", "I just typed", any line about prompting.
   Supply: PROMPT in their words. '' takes the video's first sentence (what they said first, usually the ask).
   NAME is a plain label for the assistant.
   Sound: a whoosh-soft at A, typing under the text, a whoosh-soft out.
   Change only these constants: */
var PROMPT = '';                 // their instruction; '' = the video's first sentence
var NAME = 'AI';
var TYPE_ON = '', TYPE_AT = 0.12;
var CPS = 34;                    // characters per second (it never types past B - 0.5)
var ATT = [587, 520, 0.36];      // the attachment: left, top, scale of the full frame (0.36 = 389 x 691)

var FPS = 30;
function fq(f) { return Math.max(0, f / FPS - 0.002); }
function first() {
  var out = [];
  for (var i = 0; i < WORDS.length; i++) { out.push(WORDS[i][2]); if (/[.!?]$/.test(WORDS[i][2]) || out.length > 18) break; }
  return out.join(' ') || 'Edit my video.';
}
var text = PROMPT || first();
document.getElementById('{{ID}}-nm').textContent = NAME;
var card = document.getElementById('{{ID}}-card');
gsap.set('#{{ID}}-att', { transformOrigin: '0px 0px' });
gsap.set('#{{ID}}-cur', { opacity: 0 });
tl.fromTo('#{{ID}}-g', { opacity: 0 }, { opacity: 1, duration: 0.12, ease: 'none', immediateRender: false }, q(A));
tl.fromTo(card, { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.25, ease: 'power3.out', immediateRender: false }, q(A + 0.08));
tl.fromTo('#{{ID}}-att', { x: 0, y: 0, scale: 1, borderRadius: '0px' },
          { x: ATT[0], y: ATT[1], scale: ATT[2], borderRadius: '60px', duration: 0.4, ease: 'power3.inOut', immediateRender: false }, q(A));

var w = TYPE_ON ? wordAt(TYPE_ON, A) : null, t0 = (w === null || w >= B - 0.6) ? A + TYPE_AT * (B - A) + 0.25 : w;
var tEnd = B - 0.5, n = text.length, dt = Math.min(1 / CPS, Math.max(0.012, (tEnd - t0) / Math.max(1, n)));
tl.set('#{{ID}}-cur', { opacity: 1 }, q(t0));
for (var i = 1; i <= n; i++) tl.set('#{{ID}}-tx', { textContent: text.slice(0, i) }, q(t0 + i * dt));
tl.set('#{{ID}}-cur', { opacity: 0 }, q(t0 + n * dt + 0.15));

var tOut = B - 0.38;
tl.fromTo('#{{ID}}-att', { x: ATT[0], y: ATT[1], scale: ATT[2], borderRadius: '60px' },
          { x: 0, y: 0, scale: 1, borderRadius: '0px', duration: 0.38, ease: 'power3.inOut', immediateRender: false }, q(tOut));
tl.to(card, { opacity: 0, y: 60, duration: 0.2, ease: 'power2.in' }, q(tOut));
tl.to('#{{ID}}-g', { opacity: 0, duration: 0.1, ease: 'none' }, q(B - 0.1));

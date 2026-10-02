# A Focused Mastering Curriculum for AI-Generated Tracks (Suno) — Lean Version

**Philosophy:** you're not learning "mastering" in general — you're learning to **fix a specific set of recurring problems in Suno tracks**. You have ~600 tracks (rated from 1 to 5 stars), which is the best possible training material, because you'll be learning on real, existing problems instead of theoretical exercises.

This curriculum follows the same logic as the tutorial we discussed earlier (Underdog — Processing Hi-Hats): **diagnose by careful listening first, then treat with a tool matched to that specific problem, then move to overall tonal balance.**

---

## Step Zero: Organize Your Training Material

Before starting, sort your 600 tracks (even a rough pass is fine):

| Category | How to use it in training |
|---|---|
| **5-star / 4-star** | Use as sonic "targets" after cleanup — some can also work as internal reference tracks for other tracks in the same style |
| **3-star — "close but flawed"** | Your best training material — usually has one or two clearly identifiable problems you can diagnose and fix |
| **1–2 star** | Don't waste time fixing these, but **use them to train your ear to quickly recognize severe defects** (A/B them against a 5-star track in the same style) |

**Foundational exercise:** before any technical learning, spend an hour listening to 10 tracks (5-star + 1-2 star) alternating between them, and try to describe the difference in plain words (not jargon). This builds a personal "problem map" that the rest of the curriculum will translate into technical terms.

---

## Common Defects in Suno Tracks (and How to Recognize Them)

This table is your "diagnostic curriculum" — every time something bothers you in a track, come back here and match what you're hearing to a row:

| Defect | How it sounds | Technical term | Where it's fixed |
|---|---|---|---|
| Harsh hi-hats/cymbals (the one we already covered) | "Stings" or "pierces" the ear at high frequencies | Harshness / sibilant resonance (usually 4–6kHz or 8–12kHz) | Notch EQ on the channel, before mastering |
| "Muddy" or "muffled" sound | Mix feels foggy, instruments blur together | Muddiness (usually 200–500Hz) | Broad EQ cut in the low-mids |
| "Boxy" sound | Feels like it's coming from inside a cardboard box | Boxiness (usually 300–600Hz) | Similar narrow notch to muddiness |
| Weak or "weightless" bass | Bass is present but lacks power | Weak low-end / lacking weight | Gentle low shelf boost (60–120Hz) or light saturation |
| Bloated or overpowering bass | Bass masks everything else, feels too heavy | Boominess (usually 80–200Hz) | Precise EQ cut in the bloated area |
| "Metallic" or "glassy" extreme highs | Purely artificial feel, resembles aliasing | Brittleness / digital artifacts (8kHz+) | Gentle high shelf cut or broadband de-esser |
| Vocal has a "hissy" quality on S/Sh sounds | Bothersome specifically on words with sibilants | Sibilance (vocal-specific, 5–8kHz) | De-esser on the vocal channel |
| Reverb/delay tails sound "off" or synthetic | Unnatural ringing at the end of notes | Artifact reverb tails / smearing | Hard to fully fix in mastering — dynamic EQ can sometimes tame it |
| Track feels "flat," everything at the same intensity | No difference between quiet and loud sections | Over-compression / lack of dynamics (sometimes baked in by Suno itself) | Avoid adding more compression in mastering — let it breathe |
| Sound feels "narrow," not wide | Instruments feel centered with no sense of width | Narrow stereo image | Gentle Utility widening (carefully, without losing mono compatibility) |
| Sound "wobbles" or thins out on a single speaker (mono) | Some elements disappear or weaken in mono | Poor mono compatibility | Check with Utility's mono button + phase correction |
| Sudden peaks or slight "crackle" | Sounds like it's about to clip | Clipping / near-clipping artifacts | Proper limiter settings, or lower gain staging before mastering |

> **Important note:** not all of these are fixable in mastering. Some (like artifact reverb tails or synthetic vocal issues) come from Suno's generation process itself and are hard to fix after export — an important distinction to learn early so you don't get discouraged.

---

## Curriculum Structure — 6 Modules, Each Practiced on Your Own Real Tracks

### Module 1: Ear Training (the most important module in the whole curriculum)
**Goal:** be able to locate any annoying frequency within seconds.

- Pick 5 tracks from your "3-star" category with an obvious problem
- On each track: load EQ Eight, boost gain heavily on a narrow band, and sweep it slowly from 200Hz to 15kHz until the annoying part "jumps out" at you
- Note down the approximate frequency for each problem you find
- Repeat until you can predict the rough location before sweeping

**Mastery benchmark:** you can pinpoint the annoying frequency within ±1kHz in under 30 seconds of sweeping.

### Module 2: Corrective EQ (fixing, not shaping)
**Goal:** fix the issues in the table above (harshness, muddiness, boxiness) without affecting the rest of the mix.

- Apply notch cuts (3–6dB, medium-narrow Q) at the locations you found in Module 1
- Rule: treat the individual channel (drums, vocal) before mastering — not the master bus
- On the same track, compare before/after: did the harshness go away without losing the track's "sparkle"?

### Module 3: Tonal Shaping (Shelving)
**Goal:** after cleanup, learn to shape the overall character (dark/bright) to taste.

- Low shelf and high shelf only — you don't need more than this
- Apply to 3 tracks from different styles you have, and notice how the sonic "personality" shifts

### Module 4: Dynamics (Glue Compression + Limiting)
**Goal:** understand the difference between "gluing" elements together (compression) and "raising loudness" (limiting) — don't confuse the two.

- Light-ratio Glue Compressor (2:1 or less) on the master bus
- Limiter at the very end, monitor LUFS (use the free Youlean Loudness Meter)
- Rough target: around -14 LUFS for general listening (not a strict rule, just a sane starting point)
- **Diagnostic exercise:** take a track that feels "flat and lifeless" from the defect table — try reducing any compression that's already baked in rather than adding more

### Module 5: Stereo & Mono Compatibility
**Goal:** make sure your tracks work correctly on any playback device.

- Check 5 tracks with the mono button on Utility — does any important element disappear?
- Try light widening on a track that feels "narrow" from the table, and watch its effect on mono

### Module 6: Reference-Based Mastering (putting it all together)
**Goal:** combine all previous modules into a complete end-to-end workflow.

Full workflow (in order):
```
1. Diagnose (Module 1) → identify problems by ear
2. Corrective EQ (Module 2) → notch the offending frequencies on the channel
3. Tonal EQ (Module 3) → shape the overall character
4. Dynamics (Module 4) → glue + limiting
5. Stereo check (Module 5) → confirm compatibility
6. Reference match → matchering, or manual A/B ear-matching against a suitable reference track
```

- Pick a 5-star track in the same style (epic symphonic-rock, for example) as an internal reference for weaker tracks in that same style
- Apply the full workflow to 10 tracks from your "3-star" category, and evaluate: how many moved up to "4-star" quality after processing?

---

## Things You **Don't** Need to Learn (Skip These Confidently)

- Complex multiband compression
- Advanced sidechain compression (unless you run into an actual need for it later)
- Mixing from scratch (instrument placement, full manual panning) — Suno already gives you a finished mix
- Complex analog emulation / tape saturation chains
- Advanced Mid/Side processing (useful only once you've mastered the basics above)
- Any course titled "Complete Mastering Engineer Course" — these are built for professional music production, and 70% of it doesn't apply to you

## Tools You Actually Need

- **Ableton Live** (which you already have): EQ Eight, Glue Compressor, Limiter, Utility, Spectrum
- **Youlean Loudness Meter** (free) — for measuring LUFS
- **matchering** (Python, free) — for automated reference matching, as discussed in our earlier conversation

---

## How to Measure Your Progress

Instead of a certificate or a test, you already have a real benchmark: **take 20 tracks from your "3-star" category, apply the full curriculum once you're done, and see how many of them now feel like they deserve 4–5 stars by your own judgment.** This is the best possible measure since it's based on your own ear and taste, not an external standard.

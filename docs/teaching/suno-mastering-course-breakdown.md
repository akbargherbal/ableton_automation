# Suno Mastering Course — Lesson-by-Lesson Breakdown
### (Content brief for an LLM to write full lesson text from)

---

## How to Use This Document

This is not the course itself — it's a **spec sheet**. Each lesson below lists the exact points that must be covered, the terminology that must be defined, the examples that must be used, and the misconceptions that must be addressed. Feed one lesson section at a time to an LLM with a prompt like: *"Write the full lesson content based on this breakdown."*

### Learner Profile (give this to the LLM as context for every lesson)

- Hobbyist, not a professional. No formal music training, doesn't play an instrument.
- Primary activity: generating full tracks with Suno (AI music generation), not composing or recording from scratch.
- Has ~600 self-generated tracks rated 1–5 stars, used as practice material.
- Already owns Ableton Live — no budget assumption for paid plugins.
- Explicitly does NOT want a full "audio engineering" education — only what applies to cleaning up and mastering an already-finished AI-generated mix.
- Prior context already covered by the learner (do not re-explain from scratch, can be referenced as known): matchering is a reference-matching tool, not intelligent mastering; harsh hi-hats are called "harshness" or "sibilant frequencies," usually 4–6kHz; the underlying tutorial referenced throughout is "Underdog — Processing Hi-Hats."

### Global Rules for Every Lesson

- Every technical term must be defined the first time it's used, in plain language, before being used again.
- Every concept must include at least one concrete example phrased as "on one of your Suno tracks, this would sound like..."
- Every lesson must explicitly state what is OUT of scope for that lesson (to prevent scope creep into unrelated topics).
- Every lesson ends with one hands-on exercise the learner performs on their own tracks — never a generic downloaded sample.
- Do not recommend any tool beyond stock Ableton devices, Youlean Loudness Meter (free), and matchering (Python) unless the lesson explicitly says otherwise.

---

## Lesson 1: What Mastering Is (and Isn't) for an AI-Generated Track

**Objective:** the learner understands the boundary between mixing, mastering, and cleanup/repair — and where their actual problems fall.

**Must cover:**
- Definition of mastering: balancing loudness, frequency balance, stereo width, and preventing clipping across the *entire* finished mix as one block.
- Why mastering has no "awareness" of individual instruments or specific problem frequencies — it moves broad strokes only.
- The three-stage mental model: Cleanup/Repair → Mastering → Reference Matching, and why order matters (cleaning after mastering amplifies problems instead of fixing them).
- Why a Suno track is a special case: there's no multitrack mixing step, so "mastering" here really means "cleanup + balance + loudness" applied to a single finished stereo file.

**Must define:** mastering, mixing, RMS, clipping, stereo width.

**Must address (misconception):** "Mastering can fix any problem in a track." Explicitly state this is false and explain why (see Module 4's defect table split into fixable-by-mastering vs. not).

**Exercise:** the learner picks one 5-star and one 2-star track and writes down, in plain words, what they think mastering could and couldn't fix in each.

---

## Lesson 2: Ear Training — The EQ Sweep Technique

**Objective:** the learner can locate an annoying frequency in a track within 30 seconds.

**Must cover:**
- Step-by-step mechanics of the sweep technique: load EQ Eight, boost gain heavily (+10 to +15dB) on a narrow band (high Q), sweep slowly across the frequency spectrum while soloing/looping the problem section, stop when the annoyance "jumps out."
- Why this technique works: exaggeration makes a subtle problem audible before you commit to cutting it.
- Frequency range landmarks the learner should memorize as reference points: sub-bass (20–60Hz), bass (60–250Hz), low-mids (250–500Hz), mids (500Hz–2kHz), upper-mids (2–4kHz), presence (4–6kHz), brilliance (6–12kHz), air (12kHz+).
- Why this is described as the single most valuable skill in the whole curriculum — every later lesson depends on it.

**Must define:** Q (bandwidth), gain, frequency band, sweep.

**Must address (misconception):** "You need trained/professional ears to do this." Reframe as a trainable mechanical skill, not innate talent.

**Exercise:** using 3 tracks with a known annoyance, the learner sweeps and logs the approximate frequency for each, then checks their guess against the defect table from Lesson 4.

---

## Lesson 3: Corrective EQ — Notching Without Collateral Damage

**Objective:** the learner can remove an identified problem frequency without dulling the rest of the track.

**Must cover:**
- Difference between corrective EQ (fixing a problem) and tonal EQ (shaping character) — this lesson is only about the former.
- How to convert a located frequency (from Lesson 2) into a cut: invert the gain to negative, use a medium-narrow Q, start at 3dB and increase only as needed up to ~6dB.
- Why corrective EQ should happen on the *individual channel* (e.g., the drum bus) before mastering, not on the master bus — mastering-stage EQ affects everything at once.
- How to verify the fix worked: A/B before/after on the isolated element, then A/B on the full mix to confirm nothing else was damaged.

**Must define:** notch, corrective EQ vs. tonal EQ, channel/bus.

**Must address (misconception):** "Bigger cuts always fix problems better." Explain why over-cutting causes a hollow, lifeless sound and why the smallest effective cut is preferred.

**Exercise:** the learner fully treats one 3-star track's identified problem from Lesson 2, and rates the result 1–5 for "problem gone" and 1–5 for "rest of the mix unaffected."

---

## Lesson 4: The Suno Defect Catalog

**Objective:** the learner has a reference map connecting what they hear to a named problem and a fix category.

**Must cover, as a structured table or list, each with a one-line audible description, technical name, frequency range, and fix path:**
- Harshness / sibilant resonance (hi-hats, cymbals) — 4–6kHz, 8–12kHz
- Muddiness — 200–500Hz
- Boxiness — 300–600Hz
- Weak/weightless bass — needs 60–120Hz shelf boost
- Boominess (bloated bass) — 80–200Hz
- Brittleness/digital artifacts — 8kHz+
- Vocal sibilance (S/Sh sounds) — 5–8kHz
- Artifact reverb tails / smearing — not tied to one frequency, mostly a generation artifact
- Flatness / over-compression — a dynamics problem, not a frequency problem
- Narrow stereo image
- Poor mono compatibility
- Clipping / near-clipping artifacts

**Must explicitly separate:** defects fixable in mastering/cleanup vs. defects baked into the Suno generation that mastering cannot meaningfully fix (reverb artifacts, certain vocal warbling) — and state plainly that accepting this limitation is part of the skill.

**Must define:** each technical term listed above, in one sentence.

**Exercise:** the learner picks 5 different 3-star tracks and assigns each one a primary defect from the catalog, purely by ear, before doing any technical analysis.

---

## Lesson 5: Tonal Shaping with Shelving EQ

**Objective:** the learner can intentionally shape brightness/darkness after cleanup is done, as a taste decision rather than a repair.

**Must cover:**
- Difference between a shelf and a bell/notch (shelf affects everything above or below a point; bell/notch affects a narrow band).
- Low shelf (below ~5kHz): effect described as darker/warmer/duller depending on direction.
- High shelf (above ~5kHz): effect described as brighter/airier, with a warning about tipping into harshness if pushed too far (linking back to Lesson 3's territory).
- Why this step comes *after* corrective EQ, never before (shaping on top of unfixed problems exaggerates them).

**Must define:** shelf filter, bell filter (for contrast only).

**Must address (misconception):** "Brighter always sounds more professional/higher quality." Present this as a taste trap, not a rule.

**Exercise:** the learner applies a subtle shelf move to 3 tracks of different genres/styles they've made and notes which direction fit each style's mood best.

---

## Lesson 6: Dynamics — Glue Compression and Why Less Is More

**Objective:** the learner understands what compression is for at the mastering stage and applies exactly one simple technique (bus glue compression) correctly.

**Must cover:**
- What compression fundamentally does: reduces the volume difference between loud and quiet parts of the signal.
- The single technique needed here: light-ratio (2:1 or less) glue compression on the master bus, with attack/release set slow enough to avoid pumping.
- Why this lesson deliberately excludes multiband, parallel, and sidechain compression — state this exclusion explicitly and why (unnecessary complexity for this use case).
- How over-compression connects back to the "flatness" defect from Lesson 4, and why sometimes the fix is *removing* compression that Suno already baked in, not adding more.

**Must define:** ratio, attack, release, gain reduction, pumping.

**Must address (misconception):** "More compression = more professional sound." Directly counter this with the flatness/loudness-war framing.

**Exercise:** the learner takes one track that feels "flat" and one that feels "too dynamic/inconsistent," and applies glue compression only where it's actually needed, explaining their reasoning for each.

---

## Lesson 7: Loudness and Limiting

**Objective:** the learner can bring a track to a competitive loudness level without destroying its dynamics or introducing distortion.

**Must cover:**
- Difference between peak level (a momentary measurement) and LUFS (a perceived-loudness measurement used by streaming platforms).
- Why streaming platforms normalize loudness (~-14 LUFS as a rough reference point, not a hard rule) and what that means practically for how loud to master.
- How to use a limiter correctly: as the last device in the chain, to catch peaks and raise the floor, not as a tool to flatten the whole track.
- How to read Youlean Loudness Meter's integrated LUFS reading.

**Must define:** peak, LUFS, true peak, ceiling, limiter vs. compressor (contrast briefly).

**Must address (misconception):** "Louder always sounds better, push the limiter as hard as possible." Explain diminishing returns and the audible cost (fatigue, loss of dynamics) of overdoing it.

**Exercise:** the learner masters one track to three different loudness targets (e.g., -16, -14, -11 LUFS) and compares perceived quality, not just loudness, at each.

---

## Lesson 8: Stereo Field and Mono Compatibility

**Objective:** the learner can check and adjust the stereo width of a track without breaking its mono playback.

**Must cover:**
- What "stereo width" perceptually means (sense of space vs. everything centered).
- How to widen carefully using Ableton's Utility device.
- Why mono compatibility matters (real-world playback: phone speakers, some venues, one earbud) and how phase cancellation can make elements disappear in mono even if they sound fine in stereo.
- How to check mono compatibility using Utility's mono button as a diagnostic, not just a creative tool.

**Must define:** stereo width, mono compatibility, phase cancellation (plain-language version, no deep phase math).

**Must address (misconception):** "Wider is always better." State the risk of overly wide, unnatural-sounding masters and mono playback failures.

**Exercise:** the learner checks 5 tracks in mono, notes which elements weaken or disappear, and makes one corrective width adjustment on the worst offender.

---

## Lesson 9: Reference-Based Mastering (Putting It All Together)

**Objective:** the learner can execute the full six-stage workflow end-to-end and use a reference track (their own 5-star track or matchering) to validate the result.

**Must cover:**
- The complete ordered workflow, restated as a single checklist: diagnose (Lesson 2) → corrective EQ (Lesson 3) → tonal EQ (Lesson 5) → dynamics (Lesson 6) → loudness/limiting (Lesson 7) → stereo check (Lesson 8) → reference match.
- How to choose an internal reference track: same genre, similar instrumentation density, similar dynamic range, high perceived quality (their own 5-star tracks qualify).
- Two ways to reference-match: automated (matchering, Python library) vs. manual ear-matching via level-matched A/B switching.
- Why level-matched A/B is essential (louder always sounds "better" to the ear even when it isn't — a false-positive trap).

**Must define:** reference track, A/B testing, level-matching.

**Must address (misconception):** "If it sounds louder in the A/B comparison, it's actually better." This is the single most important misconception to dismantle in the entire course — dedicate real explanation space to it.

**Exercise:** the learner runs the full workflow on 10 of their 3-star tracks and records, per track, a before/after self-rating (1–5 stars) plus which specific defect from Lesson 4's catalog was addressed.

---

## Lesson 10 (Capstone): Building a Personal Mastering Checklist

**Objective:** the learner consolidates everything into a repeatable personal checklist they can run on any new Suno track going forward.

**Must cover:**
- A condensed, printable version of the 6-stage workflow from Lesson 9, written as short imperative checklist items (not prose).
- Guidance on how to know when a track needs the full workflow vs. a lighter pass (e.g., a track with no obvious defects from the Lesson 4 catalog might only need loudness/limiting).
- A short "when to stop" section: diminishing returns, and the risk of over-processing a track that was already close to done.
- Explicit list of what remains permanently out of scope for this learner (multiband compression, full manual mixing, complex M/S processing, analog emulation chains) as a boundary reminder.

**Must NOT introduce any new technical concept** — this lesson only organizes and condenses Lessons 1–9.

**Exercise:** the learner writes their own one-page checklist in their own words, then tests it cold on a brand-new Suno track they haven't rated yet.

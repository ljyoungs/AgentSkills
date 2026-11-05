# AgentSkills repository guidance

This is the user's shared skill collection. Keep standalone packages under
`skills/<category>/<skill-name>/`. Update both `catalog.json` and the root README
when adding, moving or renaming a skill. Add categories when a real package needs
them; do not create empty category trees.

Read the selected package before changing it. Preserve existing skill behavior
when the task is classification or navigation. Keep legacy migration notes for
moved public paths. Do not copy private project records or raw third-party assets
into a package. Research references do not grant redistribution rights; retain
accurate file-level licenses and provenance.

The narrative package contains original text guidance, not a media-generation
runtime. Distinguish authored examples, logged forward-test outputs, and actual
audience performance. Describe the inputs, conditions and limits of any real
evaluation; examples or format checks alone are not an independent evaluation.
Do not run the legacy social-media automation merely to validate this repository.

Before pushing, run `python scripts/validate_catalog.py` and
`python -m unittest discover -s tests -v`. For the narrative package, also run the
available skill-creator format validator. These checks do not validate real
platform actions or model behavior. Commit only this repository's intended
changes; never force-push over concurrent user work.

User choice (2026-11-05): publish only photo-beat-video as the video skill in
this repository. Keep its image-to-video helper inside that package; do not
restore a standalone image-to-video skill or catalog entry without a new request.
Validate with synthetic media and simulated provider responses; do not consume
GPU quota or use private photos merely to test a package update. An anonymous
client, a logged-in browser, and a reachable schema are distinct states, not
evidence of available quota.

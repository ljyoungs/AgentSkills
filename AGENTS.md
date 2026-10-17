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
runtime. Review its examples and material-specific conclusions without claiming
an independent evaluation or actual audience performance. Do not run the legacy
social-media automation merely to validate this repository.

Before pushing, run `python scripts/validate_catalog.py` and
`python -m unittest discover -s tests -v`. For the narrative package, also run the
available skill-creator format validator. These checks do not validate real
platform actions or model behavior. Commit only this repository's intended
changes; never force-push over concurrent user work.

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_catalog import validate


class CatalogChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.package = self.root / "skills/writing/story"
        self.package.mkdir(parents=True)
        self.catalog = {
            "schema_version": 1,
            "categories": [{"id": "writing"}],
            "skills": [
                {
                    "id": "story",
                    "category": "writing",
                    "path": "skills/writing/story",
                    "activation_name": "story",
                    "distribution": "standalone",
                }
            ],
        }
        (self.root / "README.md").write_text(
            "[story](skills/writing/story/)", encoding="utf-8"
        )
        (self.package / "SKILL.md").write_text(
            "---\nname: story\ndescription: Write stories\n---\nUse the supplied facts.\n",
            encoding="utf-8",
        )
        (self.package / "README.md").write_text(
            "[Instructions](SKILL.md)", encoding="utf-8"
        )
        (self.package / "LICENSE").write_text("MIT", encoding="utf-8")
        self.save()

    def save(self):
        (self.root / "catalog.json").write_text(
            json.dumps(self.catalog), encoding="utf-8"
        )

    def test_complete_standalone_package(self):
        self.assertEqual(validate(self.root), [])

    def test_missing_reference_is_reported(self):
        (self.package / "README.md").write_text(
            "[Example](missing.md)", encoding="utf-8"
        )
        self.assertTrue(any("Broken" in e for e in validate(self.root)))

    def test_link_outside_package_is_not_portable(self):
        (self.package / "README.md").write_text(
            "[Project](../../../README.md)", encoding="utf-8"
        )
        self.assertTrue(any("not standalone" in e for e in validate(self.root)))

    def test_private_asset_reference_is_rejected(self):
        (self.package / "README.md").write_text(
            "C:/Users/example/voice_experiments/clip.mp3", encoding="utf-8"
        )
        self.assertTrue(any("private" in e for e in validate(self.root)))

    def test_unlisted_skill_is_reported(self):
        other = self.root / "skills/writing/other"
        other.mkdir()
        (other / "SKILL.md").write_text("---\nname: other\n---\n", encoding="utf-8")
        self.assertTrue(any("Uncatalogued" in e for e in validate(self.root)))

    def test_duplicate_or_escaping_entry_is_reported(self):
        self.catalog["skills"].append(dict(self.catalog["skills"][0]))
        self.catalog["skills"][0]["path"] = "../../unrelated"
        self.save()
        errors = validate(self.root)
        self.assertTrue(any("Duplicate skill" in e for e in errors))
        self.assertTrue(any("Noncanonical" in e for e in errors))


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class ParameterDisclosureTests(unittest.TestCase):
    def test_cli_arguments_do_not_embed_defaults(self):
        for path in (ROOT / "src").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(
                "default=",
                text,
                msg=f"{path.name} embeds argparse defaults",
            )

    def test_docs_do_not_include_original_acquisition_parameters(self):
        combined = "\n".join(
            [
                read("README.md"),
                read("docs/workflow.md"),
                read("docs/source_files.md"),
            ]
        )
        forbidden = [
            "129",
            "579",
            "0.011",
            "70",
            "42",
            "800",
            "300",
            "360",
        ]
        for token in forbidden:
            self.assertNotIn(
                token,
                combined,
                msg=f"documentation still includes {token}",
            )


if __name__ == "__main__":
    unittest.main()

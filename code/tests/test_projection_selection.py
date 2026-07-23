import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from projection_io import find_projection_files  # noqa: E402


def touch(root: Path, name: str) -> None:
    (root / name).write_bytes(b"")


class ProjectionSelectionTests(unittest.TestCase):
    def test_number_does_not_match_inside_longer_digit_runs(self):
        """An index must not match timestamp digits elsewhere in the name.

        With plain substring matching, requesting 173 would select the first
        file whose *timestamp* contains "173", i.e. the blockId#129 image.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            touch(root, "Pic_2023_11_09_173600_blockId#129.jpeg")
            touch(root, "Pic_2023_11_09_173635_blockId#173.jpeg")
            touch(root, "Pic_2023_11_09_174129_blockId#541.jpeg")

            selected = find_projection_files(root, 129, 173, 44)
            names = [p.name for p in selected]
            self.assertEqual(
                names,
                [
                    "Pic_2023_11_09_173600_blockId#129.jpeg",
                    "Pic_2023_11_09_173635_blockId#173.jpeg",
                ],
            )

    def test_ambiguous_standalone_match_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            touch(root, "a_129_first.jpeg")
            touch(root, "b_129_second.jpeg")
            with self.assertRaises(ValueError):
                find_projection_files(root, 129, 129, 1)

    def test_zero_padded_names_are_matched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            touch(root, "slice_0129.tif")
            selected = find_projection_files(root, 129, 129, 1)
            self.assertEqual([p.name for p in selected], ["slice_0129.tif"])

    def test_missing_number_raises_instead_of_silently_skipping(self):
        """A gap in the sequence must fail loudly.

        Silently dropping one projection would re-spread the remaining ones
        over the angular range and misassign every angle after the gap.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            touch(root, "blockId#129.jpeg")
            touch(root, "blockId#133.jpeg")  # 131 is missing
            with self.assertRaises(ValueError) as ctx:
                find_projection_files(root, 129, 133, 2)
            self.assertIn("131", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

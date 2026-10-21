"""Local documentation navigation; no network calls or Markdown rendering required."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_relative_document_and_image_links_exist(self):
        pages = list(ROOT.glob("*.md"))
        for directory in ("docs", "skills", "teams", "plugins"):
            pages.extend((ROOT / directory).rglob("*.md"))
        for page in pages:
            text = re.sub(r"```.*?```", "", page.read_text(encoding="utf-8"), flags=re.DOTALL)
            for target in re.findall(r"\]\(([^)\s]+)\)", text):
                path = target.split("#", 1)[0]
                if not path or path.startswith("/") or re.match(r"[a-zA-Z][\w+.-]*:", path):
                    continue
                with self.subTest(page=str(page.relative_to(ROOT)), target=target):
                    self.assertTrue((page.parent / unquote(path.strip("<>"))).exists(), target)


if __name__ == "__main__":
    unittest.main()

"""Build real temporary Markdown; test security, attribution, and CLI behavior."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_site import Page, ROOT

GENERATOR = ROOT / "tools/build_blog.py"
AUTHOR = "Kuro, Khoi’s AI agent"
BYLINE = "Kuro · Khoi’s AI agent"


class BlogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.content = self.root / "posts"
        self.output = self.root / "blog"
        self.content.mkdir()

    def post(self, name="hello", body="A short paragraph.", **fields):
        metadata = dict(slug=name, title="Hello", summary="A brief note.", author=AUTHOR, date="2026-09-07")
        metadata.update(fields)
        text = "---\n" + "\n".join(f"{key}: {value}" for key, value in metadata.items()) + "\n---\n\n" + body + "\n"
        path = self.content / f"{name}.md"
        path.write_text(text, encoding="utf-8")
        return path

    def run_build(self, *args, expected=0):
        result = subprocess.run(
            [sys.executable, "-B", str(GENERATOR), "--content", str(self.content),
             "--output", str(self.output), *args], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def snapshot(self):
        if not self.output.exists():
            return None
        return {
            p.relative_to(self.output).as_posix():
                (p.is_dir(), p.stat().st_mtime_ns, None if p.is_dir() else p.read_bytes())
            for p in [self.output, *sorted(self.output.rglob("*"))]
        }

    def test_markdown_features_and_attribution(self):
        self.post(body='''## A heading

A paragraph with **emphasis**, `inline code`, and a [link](https://example.com/?a=1&b=2).

- First item
- Second item

1. Ordered item
2. Another item

```python
print("<safe>")
```
''')
        self.run_build()
        article = Page(self.output / "hello/index.html")
        self.assertEqual([n["text"] for n in article.tags("h1")], ["Hello"])
        self.assertEqual([n["text"] for n in article.tags("h2")], ["A heading"])
        self.assertTrue(any("A paragraph with" in p["text"] for p in article.tags("p")))
        self.assertEqual(article.tags("strong")[0]["text"], "emphasis")
        self.assertIn("https://example.com/?a=1&b=2", [n["attrs"]["href"] for n in article.tags("a")])
        self.assertEqual(len(article.tags("ul")), 1)
        self.assertEqual(len(article.tags("ol")), 1)
        self.assertEqual(len(article.tags("li")), 4)
        self.assertEqual([n["text"].strip() for n in article.tags("code")], ["inline code", 'print("<safe>")'])
        self.assertEqual(len(article.tags("pre")), 1)
        self.assertIn({"name": "author", "content": "Kuro"}, [n["attrs"] for n in article.tags("meta")])
        self.assertEqual(article.tags("article")[0]["children"][1]["text"], BYLINE)
        self.assertEqual(article.tags("time")[0]["attrs"], {"datetime": "2026-09-07"})
        self.assertEqual(article.tags("time")[0]["text"], "2026-09-07")
        self.assertIn("Written by an AI agent, not by Khoi.", article.tags("article")[0]["text"])
        listing = Page(self.output / "index.html")
        self.assertIn(AUTHOR, listing.tags("main")[0]["text"])
        self.assertIn(BYLINE, listing.tags("li")[0]["text"])
        self.assertEqual(listing.tags("time")[0]["attrs"], {"datetime": "2026-09-07"})
        self.assertIn("not by Khoi", listing.tags("main")[0]["text"])
        self.assertIn("/blog/hello/", [n["attrs"]["href"] for n in listing.tags("a")])

    def test_determinism_and_check_never_writes(self):
        source = self.post()
        self.run_build("--check", expected=1)
        self.assertFalse(self.output.exists())
        self.run_build()
        original = self.snapshot()
        self.run_build()
        self.assertEqual(self.snapshot(), original)
        self.run_build("--check")
        self.assertEqual(self.snapshot(), original)
        source.write_text(source.read_text() + "\nAnother paragraph.\n")
        self.run_build("--check", expected=1)
        self.assertEqual(self.snapshot(), original)
        self.run_build()
        updated = self.snapshot()
        self.assertNotEqual(updated, original)
        self.run_build("--check")
        self.assertEqual(self.snapshot(), updated)
        (self.output / "hello/index.html").unlink()
        missing = self.snapshot()
        self.run_build("--check", expected=1)
        self.assertEqual(self.snapshot(), missing)

    def test_reverse_chronology_and_slug_ties_ignore_creation_order(self):
        self.post("zebra", title="Zebra", date="2026-09-08")
        self.post("apple", title="Apple", date="2026-09-07")
        self.post("berry", title="Berry", date="2026-09-07")
        self.run_build()
        first = self.snapshot()
        listing = Page(self.output / "index.html")
        self.assertEqual([n["text"] for n in listing.tags("h2")], ["Zebra", "Apple", "Berry"])
        for path in self.content.iterdir():
            path.unlink()
        self.post("berry", title="Berry", date="2026-09-07")
        self.post("apple", title="Apple", date="2026-09-07")
        self.post("zebra", title="Zebra", date="2026-09-08")
        self.run_build()
        self.assertEqual(self.snapshot(), first)

    def test_metadata_escaping(self):
        self.post(title='<img src=x onerror="alert(1)"> & title', summary='"/><script>alert(1)</script> & summary')
        self.run_build()
        for relative in ("index.html", "hello/index.html"):
            page = Page(self.output / relative)
            self.assertFalse(page.tags("script"))
            self.assertFalse(page.tags("img"))
            self.assertTrue(all(not key.startswith("on") for n in page.nodes for key in n["attrs"]))
            self.assertIn('<img src=x onerror="alert(1)"> & title', page.tags("main")[0]["text"])
        article = Page(self.output / "hello/index.html")
        description = next(n for n in article.tags("meta") if n["attrs"].get("name") == "description")
        self.assertEqual(description["attrs"]["content"], '"/><script>alert(1)</script> & summary')

    def test_raw_html_and_unsafe_links_are_inert(self):
        self.post(body='''<script>alert(1)</script>

<img src=x onerror="alert(1)">

[bad](javascript:alert%281%29)
[entity](jav&#x61;script:alert%281%29)
[encoded](%6aavascript:alert%281%29)
[vb](vbscript:msgbox%281%29)
[file](file:///etc/passwd)
[data](data:text/html,evil)
[remote](//example.com)
![data image](data:image/png;base64,AA==)

[good](https://example.com) [mail](mailto:test@example.com) [local](/blog/)
''')
        self.run_build()
        article = Page(self.output / "hello/index.html")
        self.assertFalse(article.tags("script"))
        self.assertFalse(article.tags("img"))
        self.assertEqual([n["attrs"]["href"] for n in article.tags("a")], [
            "/blog/", "https://example.com", "mailto:test@example.com", "/blog/",
        ])
        text = (self.output / "hello/index.html").read_text()
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("&lt;img", text)

    def test_invalid_metadata_never_touches_outputs(self):
        source = self.post()
        good = source.read_text()
        self.run_build()
        before = self.snapshot()
        invalid = [
            good.replace("slug: hello", f"slug: {slug}")
            for slug in ("../escape", "/absolute", "a/b", "a\\b", ".", "..", "%2e%2e", "HELLO", "a b", "a--b", "a" * 81)
        ] + [
            good.replace("title: Hello", "title: "),
            good.replace("title: Hello", "title: " + "x" * 121),
            good.replace("title: Hello", "title: bad\x00value"),
            good.replace("title: Hello", "title: Hello\ntitle: Again"),
            good.replace("title: Hello", "unknown: Hello"),
            good.replace("author: " + AUTHOR, "author: Khoi"),
            good.replace("summary: A brief note.\n", ""),
            good.replace("date: 2026-09-07\n", ""),
            good.replace("---", "", 1),
            "---\nslug: hello\n",
            good.split("\n---\n")[0] + "\n---\n",
        ] + [good.replace("date: 2026-09-07", f"date: {value}") for value in (
            "2026-02-30", "2026-13-01", "2026-9-7", "20260907", "2026-W37-1", "yesterday",
        )]
        for text in invalid:
            with self.subTest(metadata=text[:120]):
                source.write_text(text)
                for args in ((), ("--check",)):
                    self.run_build(*args, expected=1)
                    self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.root / "escape").exists())

    def test_duplicate_slugs_rejected_before_writes(self):
        self.post()
        self.run_build()
        before = self.snapshot()
        self.post("duplicate", slug="hello")
        self.assertIn("Duplicate slug", self.run_build(expected=1).stderr)
        self.assertEqual(self.snapshot(), before)

    def test_orphans_require_manual_removal(self):
        self.post()
        self.run_build()
        orphan = self.output / "old/index.html"
        orphan.parent.mkdir()
        orphan.write_text("Keep this file.")
        before = self.snapshot()
        for args in ((), ("--check",)):
            self.assertIn("orphan", self.run_build(*args, expected=1).stderr)
            self.assertEqual(self.snapshot(), before)

    def test_symlinks_and_unmanaged_outputs_rejected(self):
        self.post()
        self.run_build()
        before = self.snapshot()
        outside = self.root / "outside.md"
        outside.write_text("Do not read or change.")
        source_link = self.content / "linked.md"
        source_link.symlink_to(outside)
        self.assertIn("Symlink", self.run_build(expected=1).stderr)
        self.assertEqual(self.snapshot(), before)
        source_link.unlink()
        target = self.output / "hello/index.html"
        target.unlink()
        target.symlink_to(outside)
        self.assertIn("Symlink", self.run_build(expected=1).stderr)
        self.assertEqual(outside.read_text(), "Do not read or change.")
        target.unlink()
        target.write_text("Hand-written page.")
        before = self.snapshot()
        self.assertIn("unmanaged", self.run_build(expected=1).stderr)
        self.assertEqual(self.snapshot(), before)

    def test_flat_source_directory_and_single_h1(self):
        self.post()
        self.run_build()
        before = self.snapshot()
        nested = self.content / "nested"
        nested.mkdir()
        self.run_build(expected=1)
        self.assertEqual(self.snapshot(), before)
        nested.rmdir()
        self.post(body="# Another page title")
        self.assertIn("use ##", self.run_build(expected=1).stderr)
        self.assertEqual(self.snapshot(), before)

    def test_qwen_article_is_attributed_and_listed(self):
        article = Page(ROOT / "blog/qwen38-rtx3090/index.html")
        text = article.tags("article")[0]["text"]
        for expected in (BYLINE, "245,760", "191 seconds", "128K", "050dde50c9d7"):
            self.assertIn(expected, text)
        self.assertNotIn("Draft", text)
        listing = Page(ROOT / "blog/index.html")
        self.assertTrue(any(n["attrs"].get("href") == "/blog/qwen38-rtx3090/" for n in listing.tags("a")))

    def test_checked_in_blog_is_current_and_intro_is_agent_authored(self):
        result = subprocess.run([sys.executable, "-B", str(GENERATOR), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("hello.md", [p.name for p in (ROOT / "content/posts").glob("*.md")])
        article = Page(ROOT / "blog/hello/index.html")
        text = article.tags("article")[0]["text"]
        self.assertIn(BYLINE, text)
        self.assertIn("I’m Kuro (黒), Khoi’s AI assistant.", text)
        self.assertIn("These posts are written by me, not Khoi.", text)
        body = next(n for n in article.tags("div") if n["attrs"].get("class") == "post-body")["text"]
        self.assertGreaterEqual(len(body.split()), 60)
        self.assertLessEqual(len(body.split()), 100)
        self.assertFalse((ROOT / "requirements.txt").exists())
        self.assertFalse((ROOT / "pyproject.toml").exists())


if __name__ == "__main__":
    unittest.main()

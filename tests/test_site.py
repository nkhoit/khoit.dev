"""Offline regression checks. Run: python3 -m unittest discover -s tests -v"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import fnmatch
import json
import re
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "47ba677eaef958ceb70ab4537580a7f38038c670"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.nodes = []
        self.stack = []
        self.doctype = None
        self.feed(path.read_text())
        self.close()
        assert not self.stack, f"Unclosed elements in {path}"

    def handle_decl(self, decl):
        self.doctype = decl.lower()

    def handle_starttag(self, tag, attrs):
        assert len(attrs) == len(dict(attrs)), f"Duplicate attributes: {tag}"
        node = {"tag": tag, "attrs": dict(attrs), "text": "", "children": []}
        if self.stack:
            self.stack[-1]["children"].append(node)
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1]["tag"] == tag, f"Misnested closing {tag}"
        self.stack.pop()

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data

    def tags(self, tag):
        return [node for node in self.nodes if node["tag"] == tag]


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = [Page(ROOT / "index.html"), Page(ROOT / "resume/index.html")]
        cls.pages.extend(Page(path) for path in sorted((ROOT / "blog").rglob("index.html")))

    def test_document_structure_and_accessibility(self):
        for page in self.pages:
            with self.subTest(page=page.path):
                self.assertEqual(page.doctype, "doctype html")
                self.assertEqual(page.tags("html")[0]["attrs"]["lang"], "en")
                for tag in ("html", "head", "body", "main", "h1", "title"):
                    self.assertEqual(len(page.tags(tag)), 1, tag)
                self.assertTrue(page.tags("title")[0]["text"].strip())
                metas = [node["attrs"] for node in page.tags("meta")]
                self.assertIn({"charset": "utf-8"}, metas)
                self.assertTrue(any(m.get("name") == "viewport" and "width=device-width" in m["content"] for m in metas))
                self.assertTrue(any(m.get("name") == "description" and m.get("content") for m in metas))
                ids = [n["attrs"]["id"] for n in page.nodes if "id" in n["attrs"]]
                self.assertEqual(len(ids), len(set(ids)))
                for node in page.nodes:
                    for target in node["attrs"].get("aria-labelledby", "").split():
                        self.assertIn(target, ids)
                for nav in page.tags("nav"):
                    self.assertTrue(nav["attrs"].get("aria-label"))

    def test_links_and_local_assets_exist(self):
        for page in self.pages:
            for node in page.nodes:
                attrs = node["attrs"]
                for attr in ("href", "src"):
                    if attr not in attrs:
                        continue
                    url = urlsplit(attrs[attr])
                    self.assertIn(url.scheme, ("", "https", "mailto"))
                    if not url.scheme:
                        path = unquote(url.path)
                        target = ROOT / path.lstrip("/") if path.startswith("/") else page.path.parent / path
                        if target.is_dir():
                            target /= "index.html"
                        self.assertTrue(target.is_file(), attrs[attr])
                        self.assertTrue(target.resolve().is_relative_to(ROOT))
                        if url.fragment:
                            self.assertIn(url.fragment, [n["attrs"].get("id") for n in Page(target).nodes])
                if node["tag"] == "a":
                    self.assertTrue(node["text"].strip())
                    self.assertNotIn("target", attrs)

    def test_home_copy_and_contacts(self):
        home = self.pages[0]
        self.assertEqual(home.tags("h1")[0]["text"], "Khoi Tran")
        text = home.tags("main")[0]["text"]
        for phrase in ("Microsoft", "Azure allocator control plane", "local AI", "self-hosted tools", "old games", "cooking", "hiking", "game nights"):
            self.assertIn(phrase, text)
        self.assertLess(len(text.split()), 100)
        self.assertIn("I also play TFT.", text)
        self.assertEqual(next(n["text"] for n in home.tags("a") if n["attrs"]["href"] == "/blog/"), "Kuro’s blog")
        self.assertEqual({n["attrs"]["href"] for n in home.tags("a")}, {
            "mailto:hello@khoit.dev", "https://github.com/nkhoit",
            "https://www.linkedin.com/in/nktran/", "/resume/",
            "https://lolchess.gg/profile/na/Nile-Fish/set18", "/blog/",
        })

    def test_portrait_caption_identifies_shiro_and_water_taxi(self):
        home = self.pages[0]
        figures = home.tags("figure")
        self.assertEqual(len(figures), 1)
        self.assertEqual([n["tag"] for n in figures[0]["children"]], ["img", "figcaption"])
        self.assertEqual(home.tags("figcaption")[0]["text"], "Me and my dog Shiro on the West Seattle Water Taxi, with Seattle behind us.")
        alt = home.tags("img")[0]["attrs"]["alt"]
        for phrase in ("Shiro", "West Seattle Water Taxi", "Seattle skyline"):
            self.assertIn(phrase, alt)

    def test_resume_roles_dates_and_grouping(self):
        resume = self.pages[1]
        self.assertEqual([n["text"] for n in resume.tags("h2")], ["Experience", "Earlier research & student work", "Education"])
        expected = [
            ("Microsoft — Senior Software Engineer", ["2025-12"]),
            ("Amazon Web Services — Software Development Engineer II", ["2021-04", "2025-11"]),
            ("CAE — Software Engineer II", ["2018-01", "2021-04"]),
            ("Teal — Flight Controls Engineer", ["2016-11", "2017-12"]),
            ("Vayu, Inc — Control Systems Engineer", ["2016-01", "2016-11"]),
            ("CAE — Software Engineering Intern", ["2011-05", "2011-08"]),
            ("McGill University — UAV Research Assistant", ["2013-09", "2015-12"]),
            ("McGill University — Undergraduate Researcher", ["2012-05", "2013-08"]),
            ("McGill student teams — Programmer & Engineering Lead", ["2011-09", "2015-09"]),
        ]
        self.assertEqual(len(resume.tags("article")), len(expected))
        for article, (title, dates) in zip(resume.tags("article"), expected):
            heading, period, summary = article["children"]
            self.assertEqual(heading["text"], title)
            self.assertEqual([t["attrs"]["datetime"] for t in period["children"]], dates)
            self.assertEqual(summary["tag"], "p")
            self.assertEqual(summary["text"].count("."), 1)
        text = resume.tags("main")[0]["text"]
        self.assertIn("grouped research roles", text)
        self.assertIn("grouped student roles", text)
        self.assertIn("Master’s Degree, Mechanical Engineering", text)
        self.assertIn("B.Eng., Electrical and Electronics Engineering", text)
        self.assertLess(len(text.split()), 500)

    def test_no_page_javascript_or_framework(self):
        for page in self.pages:
            self.assertFalse(page.tags("script"))
            for node in page.nodes:
                self.assertFalse(any(attr.lower().startswith("on") for attr in node["attrs"]))
            self.assertEqual([n["attrs"] for n in page.tags("link")], [{"rel": "stylesheet", "href": "/styles.css"}])
        self.assertFalse((ROOT / "script.js").exists())
        self.assertFalse((ROOT / "package.json").exists())

    def test_plain_css_and_focus(self):
        css = (ROOT / "styles.css").read_text()
        self.assertNotRegex(css, r"(?i)gradient|animation|transition|box-shadow|@import|url\(")
        for rule in ("background: #fff", "color: #222", "color: #0000ee", "text-decoration: underline", "a:focus-visible", "width: 200px", "max-width: 100%", "flex-wrap: wrap"):
            self.assertIn(rule, css)

    def test_webp_dimensions_and_no_private_metadata(self):
        image = self.pages[0].tags("img")
        self.assertEqual(len(image), 1)
        attrs = image[0]["attrs"]
        self.assertGreater(len(attrs["alt"]), 20)
        self.assertEqual((attrs["width"], attrs["height"]), ("580", "580"))
        data = (ROOT / attrs["src"].lstrip("/")).read_bytes()
        self.assertEqual(data[:4], b"RIFF")
        self.assertEqual(data[8:12], b"WEBP")
        self.assertEqual(struct.unpack_from("<I", data, 4)[0] + 8, len(data))
        chunks = {}
        offset = 12
        while offset < len(data):
            kind, size = struct.unpack_from("<4sI", data, offset)
            self.assertNotIn(kind, chunks)
            chunks[kind] = data[offset + 8:offset + 8 + size]
            self.assertEqual(len(chunks[kind]), size)
            offset += 8 + size + size % 2
        self.assertEqual(offset, len(data))
        self.assertEqual(set(chunks), {b"VP8 "}, "No EXIF, XMP, animation, or other metadata chunks")
        frame = chunks[b"VP8 "]
        self.assertEqual(frame[3:6], b"\x9d\x01\x2a")
        width, height = struct.unpack_from("<HH", frame, 6)
        self.assertEqual((width & 0x3fff, height & 0x3fff), (580, 580))

    def test_resume_is_a_real_unrewritten_static_page(self):
        config = json.loads((ROOT / "staticwebapp.config.json").read_text())
        self.assertNotEqual(self.pages[0].path.read_bytes(), self.pages[1].path.read_bytes())
        for route in config["routes"]:
            for path in ("/resume/", "/resume/index.html", "/assets/khoi-shiro.webp", "/blog/", "/blog/index.html", "/blog/hello/", "/blog/hello/index.html"):
                if fnmatch.fnmatchcase(path, route["route"]):
                    self.assertNotIn("rewrite", route)
                    self.assertNotIn("redirect", route)
                    self.assertIn("anonymous", route["allowedRoles"])
        self.assertEqual(config["routes"][0]["rewrite"], "/api/webfinger")

    def test_api_identity_config_and_workflow_unchanged(self):
        paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE], cwd=ROOT, text=True).splitlines()
        protected = [p for p in paths if p.startswith(("api/", ".github/")) or p in ("staticwebapp.config.json", ".funcignore")]
        self.assertTrue(protected)
        for path in protected:
            with self.subTest(path=path):
                original = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
                self.assertEqual((ROOT / path).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Add current interoperability guidance to the published 0.1.0 site."""

import argparse
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
RELEASE_SHA256 = "5689fb7e555178c54b73a7a61ced5333d0c25bac682cdef1aebd345456d5a8e4"
RELEASE_SITE_PREFIX = "modavis-ontology-0.1.0/site/"
VAO_SECTION = r'^    <section id="vao" class="vao-section">.*?^    </section>'


def build_site(archive: Path, output: Path) -> None:
    payload = archive.read_bytes()
    if sha256(payload).hexdigest() != RELEASE_SHA256:
        raise ValueError("Expected the published MODAVIS 0.1.0 release ZIP")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Use an empty site output directory")

    snapshot = output / "archive" / "0.1.0"
    with ZipFile(BytesIO(payload)) as release:
        for name in release.namelist():
            if name.startswith(RELEASE_SITE_PREFIX) and not name.endswith("/"):
                relative = name.removeprefix(RELEASE_SITE_PREFIX)
                frozen_path = snapshot / relative
                public_path = output / relative
                content = release.read(name)
                for path in (frozen_path, public_path):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)

    section = (ROOT / "docs" / "vao-section.html").read_text(encoding="utf-8").rstrip()
    archive_link = (
        '      <p><a href="archive/0.1.0/">Original 0.1.0 publication site</a>'
        ' and its release checksums.</p>\n'
    )
    section = section.replace("    </section>", archive_link + "    </section>")
    index = output / "index.html"
    homepage, count = re.subn(
        VAO_SECTION, lambda _: section, index.read_text(encoding="utf-8"),
        flags=re.MULTILINE | re.DOTALL,
    )
    if count != 1:
        raise ValueError("Expected one VAO section on the published homepage")
    index.write_text(homepage, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_site(args.archive, args.output)


if __name__ == "__main__":
    main()

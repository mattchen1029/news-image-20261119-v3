# Entry point: renders the 19 November 2026 front page and writes entry.png.
# Standard library only, no network, deterministic output.
# Before writing the final file it builds the image twice into temp
# directories and refuses to continue unless both runs are byte-identical.
import hashlib
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import render


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    # determinism check: two independent builds must match byte for byte
    hashes = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "entry.png")
            render.build(p)
            hashes.append(_sha256(p))
    if hashes[0] != hashes[1]:
        print("ERROR: builds are not byte-identical", file=sys.stderr)
        sys.exit(1)
    out_path = os.path.join(out_dir, "entry.png")
    size = render.build(out_path)
    if size > 1048576:
        print("ERROR: entry.png exceeds 1 MiB", file=sys.stderr)
        sys.exit(1)
    print("wrote %s (%d bytes, %d stories, sha256 %s)"
          % (out_path, size, render.N_STORIES, hashes[0]))


if __name__ == "__main__":
    main()

"""Read complete library paths from Linux maps, including spaces in mounts."""
from pathlib import Path


def library_paths(text, name):
    paths = set()
    for line in text.splitlines():
        fields = line.split(None, 5)
        if len(fields) == 6 and name in Path(fields[5]).name:
            paths.add(Path(fields[5]))
    return paths

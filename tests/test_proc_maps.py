from pathlib import Path
import unittest

from smokes.compat.proc_maps import library_paths


class LibraryMapsTests(unittest.TestCase):
    def test_complete_path_with_spaces_and_multiple_segments(self):
        path = '/media/External Disk/runtime/libamdhip64.so.7'
        text = '\n'.join([
            f'1000-2000 r--p 00000000 00:01 123 {path}',
            f'2000-3000 r-xp 00001000 00:01 123 {path}',
            '3000-4000 rw-p 00000000 00:00 0',
            '4000-5000 r--p 00000000 00:01 124 /runtime/libunrelated.so',
        ])
        self.assertEqual(library_paths(text, 'libamdhip64.so'), {Path(path)})

    def test_absent_library(self):
        self.assertEqual(library_paths('1000-2000 rw-p 0 00:00 0 [heap]', 'libamdhip64.so'), set())

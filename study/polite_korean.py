"""Apply the report's requested 합니다/입니다 register without editing code."""
import argparse
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re

ENDINGS = {
    '않는다': '않습니다', '있다': '있습니다', '없다': '없습니다',
    '아니다': '아닙니다', '다르다': '다릅니다', '따른다': '따릅니다',
    '늘린다': '늘립니다', '남긴다': '남깁니다', '보여준다': '보여줍니다',
    '본다': '봅니다', '다룬다': '다룹니다', '같다': '같습니다',
    '짧다': '짧습니다', '한다': '합니다', '된다': '됩니다',
    '최대다': '최대입니다', '수다': '수입니다', '배다': '배입니다',
    '활성화다': '활성화입니다', '프로세스다': '프로세스입니다',
    '자료다': '자료입니다', '예제다': '예제입니다', '사례다': '사례입니다',
    '근거다': '근거입니다', '창이다': '창입니다', '이다': '입니다',
}
ENDING = re.compile(r'[가-힣]*다(?=[.!?](?:\s|$|[<”’"\)\]]))')


def prose(text):
    def replace(match):
        word = match.group()
        if word.endswith('니다'):
            return word
        for old in sorted(ENDINGS, key=len, reverse=True):
            if word.endswith(old):
                return word[:-len(old)] + ENDINGS[old]
        if len(word) > 1 and word[-2] in '았었였됐쳤겼웠했':
            return word[:-1] + '습니다'
        if word == '다':
            return '입니다'
        return word
    return ENDING.sub(replace, text)


def markdown(text):
    output = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker.group(1)[0]
            elif marker.group(1)[0] == fence:
                fence = None
            output.append(line)
            continue
        if fence or line.lstrip().startswith(('<!--', '#')):
            output.append(line)
            continue
        # Keep inline code, link destinations, HTML attributes and URLs verbatim.
        protected = re.compile(r'(`+).*?\1|\]\([^\n]*?\)|<[^>]*>|https?://[^\s<>]+')
        parts = []
        start = 0
        for m in protected.finditer(line):
            parts.extend((prose(line[start:m.start()]), m.group()))
            start = m.end()
        parts.append(prose(line[start:]))
        output.append(''.join(parts))
    return ''.join(output)


class _HTMLProse(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0]
        for m in re.finditer('\n', source):
            self.lines.append(m.end())
        self.skip = []
        self.edits = []

    def handle_starttag(self, tag, attrs):
        if tag in ('pre', 'code', 'script', 'style'):
            self.skip.append(tag)

    def handle_endtag(self, tag):
        if self.skip and tag == self.skip[-1]:
            self.skip.pop()

    def handle_data(self, data):
        if self.skip:
            return
        changed = prose(data)
        if changed != data:
            line, col = self.getpos()
            start = self.lines[line - 1] + col
            self.edits.append((start, start + len(data), changed))


def html(text):
    parser = _HTMLProse(text)
    parser.feed(text)
    for start, end, changed in reversed(parser.edits):
        text = text[:start] + changed + text[end:]
    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('report'))
    args = parser.parse_args()
    target = args.data_dir / 'confluence-report.md'
    before = target.read_bytes().decode('utf-8')
    after = markdown(before)
    target.write_bytes(after.encode('utf-8'))
    print('Applied Korean polite register; remaining endings:',
          Counter(m.group() for m in ENDING.finditer(after)
                  if not m.group().endswith('니다')))

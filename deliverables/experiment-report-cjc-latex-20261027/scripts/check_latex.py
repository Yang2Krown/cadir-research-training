#!/usr/bin/env python3
"""Validate compilation, numbering and preserved results in the CjC report."""
from pathlib import Path
import hashlib
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[1]


def main():
    log = (ROOT / 'main.log').read_text(errors='replace')
    for marker in ['Missing character:', 'There were undefined references',
                   'There were undefined citations', 'LaTeX Error:', 'Undefined control sequence']:
        assert marker not in log, marker
    overfull = re.findall(r'Overfull \\[hv]box[^\n]*', log)
    assert not overfull, overfull
    figures = json.loads((ROOT / 'evidence/figure-sources.json').read_text())
    assert len(figures) == 13
    for row in figures:
        data = (ROOT / row['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        assert len(data) == row['bytes']
    aux = (ROOT / 'main.aux').read_text()
    toc = (ROOT / 'main.toc').read_text()
    for number in range(1, 14):
        assert '\\newlabel{fig:' + str(number) + '}' in aux
    assert '\\newlabel{tab:lm-clusters}' in aux
    bibliography = (ROOT / 'main.bbl').read_text()
    assert bibliography.count('\\bibitem') == 7
    pages = fitz.open(ROOT / 'main.pdf')
    fulltext = ''.join(p.get_text() for p in pages)
    assert '\ufffd' not in fulltext
    for text in ['0.66951870448635153', '0.74188542311548167',
                 '0.291506398370853', '0.269345381294258',
                 '0.343414049181671', '0.356463934525198']:
        assert text in fulltext.replace('\n', '').replace(' ', ''), text
    dual_column_pages = []
    for i, page in enumerate(pages):
        left, right = 0, 0
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                x0, y0, x1, y1 = line['bbox']
                if not 100 < y0 < 720 or x1 - x0 < 100:
                    continue
                if x0 < 100 and x1 < 295:
                    left += 1
                elif x0 > 300 and x1 < 555:
                    right += 1
        if left >= 15 and right >= 15:
            dual_column_pages.append(i + 1)
    assert len(dual_column_pages) >= 5
    bad_bounds = []
    for i, page in enumerate(pages):
        for b in page.get_text('blocks'):
            if b[0] < -1 or b[1] < -1 or b[2] > page.rect.width + 1 or b[3] > page.rect.height + 1:
                bad_bounds.append(i + 1)
    assert not bad_bounds, bad_bounds
    result = dict(page_count=len(pages), pdf_bytes=(ROOT / 'main.pdf').stat().st_size,
                  pdf_sha256=hashlib.sha256((ROOT / 'main.pdf').read_bytes()).hexdigest(),
                  pdf_figure_sources=13, bibliography_entries=7,
                  dual_column_pages=dual_column_pages, missing_glyphs=0,
                  undefined_references=0, undefined_citations=0, overfull_boxes=0,
                  result_scope='Existing scientific data reused; typesetting and source integrity checked')
    (ROOT / 'evidence/build-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()

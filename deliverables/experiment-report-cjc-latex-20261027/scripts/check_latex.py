#!/usr/bin/env python3
"""Validate compilation, numbering and preserved results in the CjC report."""
from pathlib import Path
import hashlib
import json
import re
import fitz
import argparse

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--display-only', action='store_true', help='Check the portable source ZIP using its prepared display PDFs.')
    args = parser.parse_args()
    log = (ROOT / 'main.log').read_text(errors='replace')
    for marker in ['Missing character:', 'There were undefined references',
                   'There were undefined citations', 'LaTeX Error:', 'Undefined control sequence']:
        assert marker not in log, marker
    overfull = re.findall(r'Overfull \\[hv]box[^\n]*', log)
    assert not overfull, overfull
    figures = json.loads((ROOT / 'evidence/figure-sources.json').read_text())
    assert len(figures) == 13
    originals_checked = 0
    for row in figures:
        source = ROOT / row['file']
        if not source.exists():
            assert args.display_only, row['file']
            continue
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        assert len(data) == row['bytes']
        originals_checked += 1
    layout = json.loads((ROOT / 'evidence/figure-layout.json').read_text())
    assert len(layout) == 13
    for row in layout:
        path = ROOT / row['display']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['display_sha256']
        crop = fitz.Rect(row['crop_box'])
        ink = fitz.Rect(row['ink_box'])
        assert crop.contains(ink)
        display = fitz.open(path)
        assert abs(display[0].rect.width-crop.width) < 0.02
        assert abs(display[0].rect.height-crop.height) < 0.02
    aux = (ROOT / 'main.aux').read_text()
    toc = (ROOT / 'main.toc').read_text()
    for number in range(1, 14):
        assert '\\newlabel{fig:' + str(number) + '}' in aux
    assert '\\newlabel{tab:lm-clusters}' in aux
    figure_pages = {int(n): int(page) for n, page in re.findall(
        r'\\newlabel\{fig:(\d+)\}\{\{[^}]*\}\{(\d+)\}', aux)}
    assert figure_pages[2] == figure_pages[3]
    assert figure_pages[8] == figure_pages[9]
    assert figure_pages[5] == figure_pages[6]
    assert figure_pages[12] == figure_pages[13]
    angle = json.loads((ROOT / 'evidence/angle-readable.json').read_text())
    assert hashlib.sha256((ROOT / angle['file']).read_bytes()).hexdigest() == angle['sha256']
    assert hashlib.sha256((ROOT / angle['display']).read_bytes()).hexdigest() == angle['display_sha256']
    bibliography = (ROOT / 'main.bbl').read_text()
    assert bibliography.count('\\bibitem') == 15
    reference_records = json.loads((ROOT / 'evidence/reference-verification.json').read_text())
    assert len(reference_records) == 15
    assert all(r['language'] == 'English' for r in reference_records)
    assert sum(2024 <= r['year'] <= 2026 for r in reference_records) == 9
    for r in reference_records:
        assert r'\bibcite{' + r['key'] + '}' in aux
        assert r'\citation{' + r['key'] + '}' in aux
    history = json.loads((ROOT / 'evidence/history-readable.json').read_text())
    assert history['coordinate_rows'] == 39522 and history['history_edges'] == 23
    assert history['stage_clusters'] == [8, 6, 7]
    assert history['stage_cells'] == [1882, 1882, 1882]
    for output in history['outputs']:
        assert hashlib.sha256((ROOT / output['file']).read_bytes()).hexdigest() == output['sha256']
    for label in ['initial', 'merge', 'split']:
        assert r'\newlabel{fig:history-' + label + '}' in aux
    pages = fitz.open(ROOT / 'main.pdf')
    fulltext = ''.join(p.get_text() for p in pages)
    assert '\ufffd' not in fulltext
    first_page = pages[0].get_text().replace('\n', '').replace(' ', '')
    for text in ['2026年10月','October2026','孙良坤','李思言','ChatGPT6.1Sol','南京农业大学']:
        assert text in first_page, text
    assert 'Vol.' not in first_page and 'No.' not in first_page
    assert '计算机学报格式' not in first_page
    for text in ['0.66951870448635153', '0.74188542311548167',
                 '0.291506398370853', '0.269345381294258',
                 '0.343414049181671', '0.356463934525198']:
        assert text in fulltext.replace('\n', '').replace(' ', ''), text
    command_layout = None
    for i, page in enumerate(pages):
        blocks = page.get_text('blocks')
        if 'source activate.sh' not in page.get_text():
            continue
        commands = ['cd /workspace/cadir-env', 'bash complete-setup.sh',
                    'source activate.sh', 'Rscript --version']
        command_blocks = [b for b in blocks if any(c in b[4] for c in commands)]
        assert all(any(c in b[4] for b in command_blocks) for c in commands)
        top = min(b[1] for b in command_blocks)
        bottom = max(b[3] for b in command_blocks)
        above = [b for b in blocks if b[2] < 295 and b[3] <= top]
        below = [b for b in blocks if b[2] < 295 and b[1] >= bottom]
        before_gap = top - max(b[3] for b in above)
        after_gap = min(b[1] for b in below) - bottom
        assert before_gap < 25 and after_gap < 25
        command_layout = dict(page=i+1, before_gap_pt=before_gap, after_gap_pt=after_gap)
    assert command_layout is not None
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
                  pdf_figure_sources=13, bibliography_entries=15,
                  english_references=15, references_2024_2026=9,
                  history_display_figures=4, enlarged_history_panels=21,
                  original_figures_checked=originals_checked,
                  figure_pages=figure_pages, command_layout=command_layout,
                  dual_column_pages=dual_column_pages, missing_glyphs=0,
                  undefined_references=0, undefined_citations=0, overfull_boxes=0,
                  result_scope='Existing scientific data reused; typesetting and source integrity checked')
    (ROOT / 'evidence/build-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()

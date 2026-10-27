#!/usr/bin/env python3
"""Check the assembled document against preserved scientific tables."""
from pathlib import Path
import csv
import hashlib
import json
import re
import statistics
import zipfile
import fitz
from docx import Document

ROOT = Path(__file__).resolve().parents[1]


def table(path):
    with path.open() as f:
        return list(csv.DictReader(f, delimiter='\t'))


def main():
    md = (ROOT / '实验报告.md').read_text()
    manifest = json.loads((ROOT / 'evidence/材料来源索引.json').read_text())
    for item in manifest['files']:
        data = (ROOT / item['path']).read_bytes()
        assert len(data) == item['bytes'], item['path']
        assert hashlib.sha256(data).hexdigest() == item['sha256'], item['path']
    metrics = json.loads((ROOT / 'evidence/LM/metrics.json').read_text())
    md_numbers = [float(x) for x in re.findall(r'0\.\d+', md)]
    for key in ['ARI', 'NMI']:
        assert any(abs(v - metrics[key]) < 1e-14 for v in md_numbers)
    cells = table(ROOT / 'evidence/LM/cluster_annotation_reference_map.tsv')
    assert sum(int(x['ncells']) for x in cells) == 1882
    genes = table(ROOT / 'evidence/LM/all_gene_assignments.tsv')
    assert len(genes) == 6000
    ranks = table(ROOT / 'evidence/LM/all_gene_ranks.tsv')
    assert len(ranks) == 1200
    for x in cells:
        assert x['predicted_annotation'] in md
    rows = table(ROOT / 'evidence/HSC/all-seed-presented-values.tsv')
    assert len(rows) == 10
    for row in rows:
        for key in ['ARI', 'NMI_max_entropy']:
            assert f'{float(row[key]):.6f}' in md
    summaries = {}
    for method in ['cadir', 'pca_snn_louvain']:
        group = [x for x in rows if x['method'] == method]
        assert len(group) == 5 and all(x['success'] == 'TRUE' for x in group)
        summaries[method] = {}
        for key in ['ARI', 'NMI_max_entropy', 'core_elapsed_seconds']:
            value = statistics.median(float(x[key]) for x in group)
            assert str(value) in md
            summaries[method][key] = value
    images = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', md)
    assert len(images) == 13 and all((ROOT / p).is_file() for p in images)
    document = Document(ROOT / '实验报告.docx')
    assert len(document.inline_shapes) == 13
    assert len(document.element.xpath('.//m:oMath')) >= 10
    pdf = fitz.open(ROOT / '实验报告.pdf')
    norm = lambda s: ''.join(s.split())
    expected_toc = json.loads((ROOT / 'evidence/目录页码.json').read_text())
    actual_toc = {norm(t): p for _, t, p in pdf.get_toc()}
    assert all(actual_toc[norm(t)] == p for t, p in expected_toc.items())
    pages = []
    for i, page in enumerate(pdf):
        blocks = page.get_text('blocks')
        outside = [b for b in blocks if b[0] < -1 or b[1] < -1 or
                   b[2] > page.rect.width + 1 or b[3] > page.rect.height + 1]
        assert not outside, (i + 1, outside)
        pages.append(dict(page=i + 1, text_chars=len(page.get_text()),
                          placed_images=len(page.get_image_info()), out_of_bounds_blocks=0))
    assert sum(x['placed_images'] for x in pages) == 13
    text = ''.join(p.get_text() for p in pdf)
    assert '\ufffd' not in text
    result = dict(scope='Report assembly, saved-table consistency and document layout; existing scientific acceptance reused',
                  source_files_checked=len(manifest['files']), figure_count=13,
                  hsc_rows=10, hsc_summary=summaries, lm_ranked_genes=1200,
                  office_math_objects=len(document.element.xpath('.//m:oMath')),
                  page_count=len(pdf), toc_entries=len(expected_toc), pages=pages)
    (ROOT / 'evidence/报告一致性检查.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'evidence/PDF页面检查.json').write_text(
        json.dumps({'page_count': len(pdf), 'pages': pages}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'pages'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

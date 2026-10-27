#!/usr/bin/env python3
"""Fit existing vector plots to the report; preserve data, axes and legends."""
from pathlib import Path
import hashlib
import json
import fitz
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / 'layout/figures'
    target.mkdir(parents=True, exist_ok=True)
    rows = []
    for source in sorted((ROOT / 'figures').glob('*.pdf')):
        doc = fitz.open(source)
        page = doc[0]
        scale = 2
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        difference = ImageChops.difference(image, Image.new('RGB', image.size, 'white'))
        mask = difference.convert('L').point(lambda v: 255 if v > 1 else 0)
        narrow = source.name in ['Fig3B_Bcell_principal.pdf','Fig3C_endothelial_principal.pdf',
                                 'S1D_Bcell_standard.pdf','S1E_endothelial_standard.pdf']
        header_bottom = 44 if narrow else 0
        if narrow:
            mask.paste(0, (0, 0, pix.width, header_bottom*scale))
        box = mask.getbbox()
        assert box is not None
        ink = fitz.Rect(*(v / scale for v in box))
        padding = 6
        crop = fitz.Rect(max(0, ink.x0-padding), max(header_bottom, ink.y0-padding),
                         min(page.rect.width, ink.x1+padding), min(page.rect.height, ink.y1+padding))
        output = fitz.open()
        new_page = output.new_page(width=crop.width, height=crop.height)
        new_page.show_pdf_page(new_page.rect, doc, 0, clip=crop, keep_proportion=True)
        path = target / source.name
        output.save(path, garbage=4, deflate=True)
        output.close()
        rows.append(dict(source='figures/'+source.name, display='layout/figures/'+source.name,
                         source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                         display_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         source_box=list(page.rect), ink_box=list(ink), crop_box=list(crop),
                         operation=('Repeated heading moved to caption; axes/data/legends retained; equal scaling' if narrow else
                                    'Exterior white margins only; equal scaling'), original_retained=True))
    (ROOT / 'evidence/figure-layout.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n')
    print('Prepared', len(rows), 'PDF display margins.')


if __name__ == '__main__':
    main()

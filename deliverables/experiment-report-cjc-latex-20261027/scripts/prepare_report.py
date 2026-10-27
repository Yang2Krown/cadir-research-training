#!/usr/bin/env python3
"""Convert the completed report into the user-selected CjC template."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'experiment-report-20261027/实验报告.md'
REPO = ROOT.parents[1]
LM = 'ab68da7ef154f133ec436275fcf11396f37f884a'
HSC = '091a8a4585cabc59a5504380398892bac49044f4'
TEMPLATE = '69e5409cd9ad26c92348896494dd3a18b78a0fbe'
CITES = {str(i): name for i, name in enumerate(
    ['kohl2026', 'tabulamuris2018', 'nestorowa2016', 'huber2015',
     'lun2016', 'blondel2008', 'hubert1985'], 1)}
FIGURES = ['Fig3A_association_top5', 'Fig3B_Bcell_principal',
           'Fig3C_endothelial_principal', 'Fig3D_actual_split_merge_history',
           'S1A_direction_angle_heatmap', 'S1B_direction_projection_matrix',
           'S1C_reference_sankey', 'S1D_Bcell_standard', 'S1E_endothelial_standard',
           'HSC_04-common-cohort', 'HSC_01-all-seed-ARI-NMI',
           'HSC_02-cadir-seed2358-reference-share',
           'HSC_02-pca_snn_louvain-seed2358-reference-share']


def escape(s):
    chars = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
             '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
             '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(chars.get(c, c) for c in s)


def text(s):
    s = s.replace('本次两组比较中的最大角度变化为', '两组比较中的最大角度变化为')
    if '/' in s and re.fullmatch(r'[A-Za-z0-9_/.\-]+', s):
        return r'\nolinkurl{' + s + '}'
    parts = re.split(r'(\[[1-7]\]|图(?:1[0-3]|[1-9])(?!\d)|表1(?!\d))', s)
    result = []
    for x in parts:
        if re.fullmatch(r'\[[1-7]\]', x):
            result.append(r'\cite{' + CITES[x[1:-1]] + '}')
        elif re.fullmatch(r'图(?:1[0-3]|[1-9])', x):
            result.append(r'图~\ref{fig:' + x[1:] + '}')
        elif x == '表1':
            result.append(r'表~\ref{tab:lm-clusters}')
        else:
            # Permit wrapping for long identifiers in narrow journal columns.
            tokens = re.split(r'([A-Za-z0-9]{18,})', x)
            result.extend(r'\seqsplit{' + escape(t) + '}' if re.fullmatch(r'[A-Za-z0-9]{18,}', t)
                          else escape(t) for t in tokens)
    return re.sub(r'([\u3400-\u9fff])(?=\d)', r'\1\\allowbreak{}', ''.join(result))


def plain(items):
    out = []
    for item in items:
        kind, value = item['t'], item.get('c')
        if kind == 'Str': out.append(value)
        elif kind in ['Space', 'SoftBreak', 'LineBreak']: out.append(' ')
        elif kind in ['Strong', 'Emph', 'SmallCaps']: out.append(plain(value))
        elif kind == 'Code': out.append(value[1])
        elif kind == 'Link': out.append(plain(value[1]))
    return ''.join(out)


def math_formula(s):
    if s.startswith(r'\mathrm{ARI}='):
        s = (r'\begin{gathered} A=\sum_i\binom{a_i}{2},\quad B=\sum_j\binom{b_j}{2},'
             r'\quad Q=\sum_{ij}\binom{n_{ij}}{2},\\'
             r'W=\binom{N}{2},\qquad'
             r'\mathrm{ARI}=\frac{Q-AB/W}{\tfrac12(A+B)-AB/W}.\end{gathered}')
    elif s.startswith(r'I(C;Y)='):
        s = s.replace(r',\qquad\mathrm{NMI}', r',\\\mathrm{NMI}')
        s = r'\begin{gathered}' + s + r'\end{gathered}'
    return '\n\\begin{equation}\n\\fitmath{' + s + '}\n\\end{equation}\n'


def inline(items):
    out = []
    for item in items:
        kind, value = item['t'], item.get('c')
        if kind == 'Str': out.append(text(value))
        elif kind in ['Space', 'SoftBreak']: out.append(' ')
        elif kind == 'LineBreak': out.append(r'\\ ')
        elif kind == 'Strong': out.append(r'\textbf{' + inline(value) + '}')
        elif kind == 'Emph': out.append(r'\emph{' + inline(value) + '}')
        elif kind == 'Code':
            parts = re.split(r'([\u3400-\u9fff]+)', value[1])
            out.append(''.join(escape(p) if re.fullmatch(r'[\u3400-\u9fff]+', p)
                               else r'{\ttfamily\nolinkurl{' + p + '}}' for p in parts if p))
        elif kind == 'Math':
            formula = value[1].replace(r'\mathbf{\Phi}', r'\boldsymbol{\Phi}').replace(
                r'\mathbf{\Gamma}', r'\boldsymbol{\Gamma}')
            out.append('$' + formula + '$' if value[0]['t'] == 'InlineMath' else math_formula(formula))
        elif kind == 'Link': out.append(r'\href{' + value[2][0].replace('%', r'\%') + '}{' + inline(value[1]) + '}')
        elif kind == 'Quoted': out.append('“' + inline(value[1]) + '”')
        elif kind == 'RawInline': out.append(value[1])
        else: raise ValueError('Unhandled inline: ' + kind)
    return ''.join(out)


class Renderer:
    def __init__(self):
        self.pending_table = None
        self.table_number = 0
        self.figure_count = 0
        self.in_appendix = False

    def table(self, value):
        self.table_number += 1
        _, _, cols, head, bodies, foot = value
        rows = list(head[1])
        for body in bodies:
            rows.extend(body[2])
            rows.extend(body[3])
        rows.extend(foot[1])
        n = len(cols)
        cells = []
        for row in rows:
            cells.append([self.blocks(c[4]).strip().replace('\n\n', ' ') for c in row[1]])
        defaults = {1: '实验数据与规模', 2: '实际软件环境', 6: '固定成果与独立检查提交',
                    7: '代码与输入输出索引', 8: '已完成工作记录', 9: '团队分工与工时记录'}
        caption = self.pending_table or defaults.get(self.table_number, '实验结果')
        label = 'tab:lm-clusters' if '逐簇结果' in caption else 'tab:' + str(self.table_number)
        self.pending_table = None
        env = 'table' if self.in_appendix else 'table*'
        spec = ('>{\\raggedright\\arraybackslash}X' * n)
        lines = [f'\\begin{{{env}}}[!htbp]', r'\centering\zihao{-5}',
                 r'\caption{' + escape(caption) + r'}\label{' + label + '}',
                 r'\begin{tabularx}{\linewidth}{' + spec + '}', r'\toprule']
        for i, row in enumerate(cells):
            lines.append(' & '.join(row) + r' \\')
            if i == 0: lines.append(r'\midrule')
        lines.extend([r'\bottomrule', r'\end{tabularx}', f'\\end{{{env}}}'])
        return '\n'.join(lines) + '\n\n'

    def figure(self, caption, source):
        self.figure_count += 1
        n = self.figure_count
        name = Path(source).stem + '.pdf'
        cap = re.sub(r'^图\d+[\s\u3000]*', '', plain(caption)).rstrip('。')
        return (r'\begin{figure*}[!tbp]' + '\n' + r'\centering' + '\n' +
                r'\includegraphics[width=0.96\textwidth,height=0.72\textheight,keepaspectratio]{figures/' + name + '}\n' +
                r'\caption{' + escape(cap) + r'}\label{fig:' + str(n) + '}\n' +
                r'\end{figure*}' + '\n\n')

    def blocks(self, blocks):
        out = []
        for block in blocks:
            kind, value = block['t'], block.get('c')
            if kind == 'Header':
                level, _, content = value
                title = re.sub(r'^\d+(?:\.\d+)*\s+', '', plain(content))
                if title.startswith('附录'):
                    if not self.in_appendix:
                        out.append(r'\clearpage\onecolumn\appendix' + '\n')
                        self.in_appendix = True
                    title = re.sub(r'^附录[A-Z]\s+', '', title)
                elif self.in_appendix:
                    title = re.sub(r'^[A-Z]\.\d+\s+', '', title)
                if title == 'Background':
                    out.append(r'\clearpage\section*{Background}\addcontentsline{toc}{section}{Background}' + '\n')
                else:
                    out.append('\\' + ('section' if level == 1 else 'subsection') + '{' + escape(title) + '}\n')
            elif kind in ['Para', 'Plain']:
                raw = plain(value)
                if re.match(r'^表[123][\s\u3000]', raw):
                    self.pending_table = re.sub(r'^表\d+[\s\u3000]*', '', raw)
                    continue
                image = next((x for x in value if x['t'] == 'Image'), None)
                if image:
                    out.append(self.figure(image['c'][1], image['c'][2][0]))
                else:
                    out.append(inline(value) + '\n\n')
            elif kind == 'Figure':
                cap = value[1][1]
                para = value[2][0]
                image = next(x for x in para['c'] if x['t'] == 'Image')
                out.append(self.figure(image['c'][1], image['c'][2][0]))
            elif kind == 'CodeBlock':
                out.append(r'\begin{Verbatim}[fontsize=\fontsize{7.7}{10}\selectfont,breaklines=true,breakanywhere=true,frame=single]' +
                           '\n' + value[1] + '\n' + r'\end{Verbatim}' + '\n\n')
            elif kind == 'Table': out.append(self.table(value))
            elif kind == 'BulletList':
                out.append(r'\begin{itemize}' + '\n')
                for part in value: out.append(r'\item ' + self.blocks(part))
                out.append(r'\end{itemize}' + '\n')
            elif kind == 'HorizontalRule': out.append('\n')
            else: raise ValueError('Unhandled block: ' + kind)
        return ''.join(out)


def main():
    document = json.loads(subprocess.run(['pandoc', str(SOURCE), '-t', 'json'],
                                        check=True, capture_output=True, text=True).stdout)
    grouped = {}
    current = None
    for block in document['blocks']:
        if block['t'] == 'Header' and block['c'][0] == 1:
            current = plain(block['c'][2])
            grouped[current] = []
        elif current:
            grouped[current].append(block)
    abstract_cn = [b for b in grouped['摘要'] if not plain(b.get('c', [])).startswith('关键词')]
    abstract_en = [b for b in grouped['Abstract']
                   if not plain(b.get('c', [])).startswith(('Reproduction of CAdir', 'Key words'))]
    r = Renderer()
    (ROOT / 'sections/abstract-cn.tex').write_text(r.blocks(abstract_cn).rstrip() + '\n\\par\n')
    (ROOT / 'sections/abstract-en.tex').write_text(r.blocks(abstract_en).rstrip() + '\n\\par\n')
    body = []
    appendix = []
    for title, blocks in grouped.items():
        if title in ['摘要', 'Abstract', '参考文献']: continue
        header = {'t': 'Header', 'c': [1, ['', [], []], [{'t':'Str','c':title}]]}
        target = appendix if title.startswith('附录') or title == 'Background' else body
        target.extend([header] + blocks)
    (ROOT / 'sections/body.tex').write_text(r.blocks(body).rstrip() + '\n\\par\n')
    (ROOT / 'sections/appendices.tex').write_text(r.blocks(appendix).rstrip() + '\n\\par\n')
    records = []
    for name in FIGURES:
        if name.startswith('HSC_'):
            path = ('cases/nestorowa_hsc/fair-experiment/results/6cc7b3d-20261027-attempt-01/'
                    'presentation/' + name.removeprefix('HSC_') + '.pdf')
            commit = HSC
        else:
            path = 'cases/tabula_muris_limb/fig3_completion/figures/' + name + '.pdf'
            commit = LM
        data = subprocess.run(['git', '-C', str(REPO), 'show', commit + ':' + path],
                              capture_output=True, check=True).stdout
        output = ROOT / 'figures' / (name + '.pdf')
        output.write_bytes(data)
        records.append({'file':str(output.relative_to(ROOT)), 'commit':commit,
                        'source_path':path, 'bytes':len(data),
                        'sha256':hashlib.sha256(data).hexdigest()})
    (ROOT / 'evidence/figure-sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    (ROOT / 'evidence/content-source.json').write_text(json.dumps({
        'report_commit':'b7d968ad8d30f366383c2b3afc97a5c2e5b2bfa5',
        'report_path':str(SOURCE.relative_to(REPO)),
        'report_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'template_repository':'https://github.com/strive-yang/CHINESE-JOURNAL-OF-COMPUTERS--Latex-Template',
        'template_commit':TEMPLATE, 'figures':r.figure_count,
        'transformation':'Report content to CjC sections; equivalent compact ARI notation; existing vector figures; BibTeX citations'
    },ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'figures':r.figure_count,'tables':r.table_number,'output':str(ROOT)},ensure_ascii=False))


if __name__ == '__main__':
    main()

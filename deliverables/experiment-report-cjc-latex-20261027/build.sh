#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# A normal TeX Live / MiKTeX installation already supplies these packages.
# The isolated cloud dependency directory is used only when CTeX is absent.
if ! kpsewhich ctex.sty >/dev/null; then
  cjc_texmf="${CJC_TEXMF:-/workspace/cjc-tex-deps-20261027/extracted/usr/share/texlive/texmf-dist}"
  if [[ ! -d "$cjc_texmf/tex/latex/ctex" ]]; then
    echo 'Install the TeX Live Chinese language collection (ctex and xeCJK).' >&2
    exit 1
  fi
  export TEXINPUTS="$cjc_texmf/tex//:${TEXINPUTS:-}"
  export OPENTYPEFONTS="$cjc_texmf/fonts/opentype//:${OPENTYPEFONTS:-}"
fi
mkdir -p evidence
xelatex -halt-on-error -interaction=nonstopmode -file-line-error main.tex > evidence/xelatex-pass1.txt 2>&1
bibtex main > evidence/bibtex.txt 2>&1
xelatex -halt-on-error -interaction=nonstopmode -file-line-error main.tex > evidence/xelatex-pass2.txt 2>&1
xelatex -halt-on-error -interaction=nonstopmode -file-line-error main.tex > evidence/xelatex-pass3.txt 2>&1
echo 'Compiled main.pdf with XeLaTeX + BibTeX.'

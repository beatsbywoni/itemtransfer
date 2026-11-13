#!/bin/bash
# Build the submission files from the Markdown sources. Usage: bash build.sh
set -e
cd "$(dirname "$0")"
pandoc ../manuscript/manuscript.md -f markdown-yaml_metadata_block -o manuscript.docx --reference-doc=_reference.docx --resource-path=../manuscript
pandoc ../supplement/supplement.md -f markdown-yaml_metadata_block -o supplement.docx --reference-doc=_reference.docx --resource-path=../supplement
python3 format_docx.py manuscript.docx --spacing 2.0 --table-pt 8.5
python3 format_docx.py supplement.docx --landscape --spacing 1.15 --table-pt 8
soffice --headless --convert-to pdf manuscript.docx supplement.docx >/dev/null 2>&1
ls -la *.docx *.pdf

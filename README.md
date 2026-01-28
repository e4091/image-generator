# image-generator

Image pattern generator.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Solid color

```bash
python src/image_generator.py solid --color 10,20,30 --size 1080x2340 --output output/solid
```

### Checker patterns (1x1, 2x2, 4x4)

```bash
python src/image_generator.py checker --block 1 --color 120,200,80 --output output/checker_1
python src/image_generator.py checker --block 2 --channels r --color 120,200,80 --output output/checker_r_2
python src/image_generator.py checker --block 4 --channels g --color 120,200,80 --output output/checker_g_4
```

### Alternating lines

```bash
python src/image_generator.py lines --line-height 8 --color 50,100,150 --output output/lines
```

### Gradation patterns

```bash
python src/image_generator.py gradient --channels r --direction horizontal --output output/grad_r_h
python src/image_generator.py gradient --channels rgb --direction vertical --descending --output output/grad_rgb_v_desc
python src/image_generator.py gradient --channels rg --direction diag_lr --output output/grad_rg_diag_lr
python src/image_generator.py gradient --channels br --direction diag_rl --descending --output output/grad_br_diag_rl_desc
```

Outputs are written as PNG by default. Use `--formats png,bmp,ppm_p3,ppm_p6` to request other formats.

### PPM to PNG conversion

```bash
python src/image_generator.py convert --input output/pattern.ppm
python src/image_generator.py convert --input output/pattern.ppm --output output/pattern_converted.png
```

### HTML to Markdown conversion

```bash
python src/image_generator.py html2md --input docs/page.html
python src/image_generator.py html2md --input docs/page.html --output docs/page.md
```
## Verilog documentation generator

Generate a Mermaid diagram and Markdown documentation from a Verilog file:

```bash
python src/verilog_docgen.py --input path/to/design.v --output-dir output/verilog_docs
```

The output markdown is written to `output/verilog_docs/verilog_design.md` by default.

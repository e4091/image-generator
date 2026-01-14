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
python src/image_generator.py checker --block 2 --color 120,200,80 --output output/checker_2
python src/image_generator.py checker --block 4 --color 120,200,80 --output output/checker_4
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

Outputs are written as both PNG and BMP by default. Use `--formats png` or `--formats bmp` to limit outputs.

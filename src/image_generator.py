#!/usr/bin/env python3
"""Image pattern generator."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image


@dataclass(frozen=True)
class RGB:
    r: int
    g: int
    b: int

    def clamp(self) -> "RGB":
        return RGB(*(max(0, min(255, v)) for v in (self.r, self.g, self.b)))

    def invert(self) -> "RGB":
        return RGB(255 - self.r, 255 - self.g, 255 - self.b)


@dataclass(frozen=True)
class Size:
    width: int
    height: int


def parse_rgb(value: str) -> RGB:
    parts = [int(p) for p in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("RGB must be in R,G,B format.")
    return RGB(*parts).clamp()


def parse_size(value: str) -> Size:
    parts = [int(p) for p in value.lower().split("x")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("Size must be in WIDTHxHEIGHT format.")
    return Size(parts[0], parts[1])


def build_solid(size: Size, color: RGB) -> Image.Image:
    return Image.new("RGB", (size.width, size.height), (color.r, color.g, color.b))


def apply_channel_mask(color: RGB, channels: str) -> RGB:
    channels = channels.lower()
    return RGB(
        color.r if "r" in channels else 0,
        color.g if "g" in channels else 0,
        color.b if "b" in channels else 0,
    )


def invert_channels(color: RGB, channels: str) -> RGB:
    channels = channels.lower()
    return RGB(
        255 - color.r if "r" in channels else 0,
        255 - color.g if "g" in channels else 0,
        255 - color.b if "b" in channels else 0,
    )


def build_checker(size: Size, color: RGB, block: int, channels: str) -> Image.Image:
    masked_color = apply_channel_mask(color, channels)
    image = Image.new("RGB", (size.width, size.height))
    pixels = image.load()
    inverted = invert_channels(masked_color, channels)
    for y in range(size.height):
        for x in range(size.width):
            if ((x // block) + (y // block)) % 2 == 0:
                pixels[x, y] = (masked_color.r, masked_color.g, masked_color.b)
            else:
                pixels[x, y] = (inverted.r, inverted.g, inverted.b)
    return image


def build_lines(size: Size, color: RGB, line_height: int) -> Image.Image:
    image = Image.new("RGB", (size.width, size.height))
    pixels = image.load()
    inverted = color.invert()
    for y in range(size.height):
        use_primary = (y // line_height) % 2 == 0
        current = color if use_primary else inverted
        for x in range(size.width):
            pixels[x, y] = (current.r, current.g, current.b)
    return image


def gradient_value(position: int, total: int, descending: bool) -> int:
    if total <= 1:
        return 0
    ratio = position / (total - 1)
    if descending:
        ratio = 1 - ratio
    return int(round(ratio * 255))


def build_gradient(
    size: Size,
    channels: str,
    direction: str,
    descending: bool,
) -> Image.Image:
    image = Image.new("RGB", (size.width, size.height))
    pixels = image.load()

    def sample_value(x: int, y: int) -> int:
        if direction == "horizontal":
            return gradient_value(x, size.width, descending)
        if direction == "vertical":
            return gradient_value(y, size.height, descending)
        if direction == "diag_lr":
            total = size.width + size.height - 1
            return gradient_value(x + y, total, descending)
        if direction == "diag_rl":
            total = size.width + size.height - 1
            return gradient_value((size.width - 1 - x) + y, total, descending)
        raise ValueError(f"Unknown direction: {direction}")

    channels = channels.lower()
    for y in range(size.height):
        for x in range(size.width):
            value = sample_value(x, y)
            r = value if "r" in channels else 0
            g = value if "g" in channels else 0
            b = value if "b" in channels else 0
            pixels[x, y] = (r, g, b)
    return image


def save_ppm(image: Image.Image, output: Path, variant: str) -> None:
    width, height = image.size
    max_value = 255
    pixels = list(image.getdata())
    header = f"P{variant}\n{width} {height}\n{max_value}\n"
    if variant == "3":
        body = " ".join(str(value) for pixel in pixels for value in pixel)
        output.write_text(header + body + "\n", encoding="ascii")
    elif variant == "6":
        output.write_bytes(header.encode("ascii") + bytes([value for pixel in pixels for value in pixel]))
    else:
        raise ValueError(f"Unknown PPM variant: {variant}")


def save_outputs(image: Image.Image, output: Path, formats: Iterable[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        target = output.with_suffix(f".{fmt}")
        if fmt == "ppm_p3":
            save_ppm(image, target, "3")
        elif fmt == "ppm_p6":
            save_ppm(image, target, "6")
        else:
            image.save(target, format=fmt.upper())


def parse_formats(value: str) -> list[str]:
    formats = [part.strip().lower() for part in value.split(",") if part.strip()]
    allowed = {"png", "bmp", "ppm_p3", "ppm_p6"}
    for fmt in formats:
        if fmt not in allowed:
            raise argparse.ArgumentTypeError("Formats must be png, bmp, ppm_p3, or ppm_p6.")
    return formats


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--size", default="1080x2340", type=parse_size)
    common.add_argument("--color", default="255,0,0", type=parse_rgb)
    common.add_argument("--output", default="output/pattern")
    common.add_argument("--formats", default="png", type=parse_formats)

    parser = argparse.ArgumentParser(description="Generate image patterns.", parents=[common])
    subparsers = parser.add_subparsers(dest="pattern", required=True)

    subparsers.add_parser("solid", help="Solid color fill.", parents=[common])

    checker = subparsers.add_parser("checker", help="Checker pattern.", parents=[common])
    checker.add_argument("--block", type=int, default=2)
    checker.add_argument(
        "--channels",
        default="rgb",
        choices=["r", "g", "b", "rg", "gb", "br", "rgb"],
        help="Limit checker colors to selected channels.",
    )

    lines = subparsers.add_parser("lines", help="Alternating line pattern.", parents=[common])
    lines.add_argument("--line-height", type=int, default=1)

    gradient = subparsers.add_parser("gradient", help="Channel gradients.", parents=[common])
    gradient.add_argument("--channels", required=True, choices=["r", "g", "b", "rg", "gb", "br", "rgb"])
    gradient.add_argument(
        "--direction",
        default="horizontal",
        choices=["horizontal", "vertical", "diag_lr", "diag_rl"],
    )
    gradient.add_argument("--descending", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    size = args.size
    color = args.color

    if args.pattern == "solid":
        image = build_solid(size, color)
    elif args.pattern == "checker":
        image = build_checker(size, color, args.block, args.channels)
    elif args.pattern == "lines":
        image = build_lines(size, color, args.line_height)
    elif args.pattern == "gradient":
        image = build_gradient(size, args.channels, args.direction, args.descending)
    else:
        raise ValueError(f"Unknown pattern: {args.pattern}")

    save_outputs(image, Path(args.output), args.formats)


if __name__ == "__main__":
    main()

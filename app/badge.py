"""
Dynamic SVG health badge generator for repository README shields.
"""

from pathlib import Path


class BadgeGenerator:
    """Generates crisp SVG status badges for code health scores."""

    @staticmethod
    def get_color_for_score(score: float) -> str:
        """Return hex color code based on health score threshold."""
        if score >= 8.5:
            return "#4c1"  # Bright Green
        elif score >= 7.5:
            return "#a4a61d"  # Yellow-Green
        elif score >= 6.0:
            return "#fe7d37"  # Orange
        else:
            return "#e05d44"  # Red

    @classmethod
    def generate_svg(cls, score: float, label: str = "code health") -> str:
        """Generate standalone SVG XML string representing health score badge."""
        color = cls.get_color_for_score(score)
        score_text = f"{score:.1f} / 10"

        # Calculate approximate text widths
        label_width = len(label) * 6 + 18
        value_width = len(score_text) * 6 + 18
        total_width = label_width + value_width

        label_center_x = label_width / 2
        value_center_x = label_width + (value_width / 2)

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label}: {score_text}">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="a">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#a)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text x="{int(label_center_x * 10)}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)">{label}</text>
    <text x="{int(label_center_x * 10)}" y="140" transform="scale(.1)">{label}</text>
    <text x="{int(value_center_x * 10)}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)">{score_text}</text>
    <text x="{int(value_center_x * 10)}" y="140" transform="scale(.1)">{score_text}</text>
  </g>
</svg>"""
        return svg

    @classmethod
    def export_badge_file(cls, score: float, output_path: Path, label: str = "code health") -> Path:
        """Write SVG badge string to disk."""
        output_path = Path(output_path).resolve()
        svg_content = cls.generate_svg(score, label=label)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(svg_content, encoding="utf-8")
        return output_path

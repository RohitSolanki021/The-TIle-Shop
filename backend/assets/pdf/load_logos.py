"""
Load and encode brand logos for PDF generation
"""
import base64
import os
from pathlib import Path

LOGO_DIR = Path(__file__).parent.parent / "brand_logos"

def get_logo_base64(logo_name: str) -> str:
    """Get base64 encoded logo"""
    logo_path = LOGO_DIR / f"{logo_name}.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

def get_all_logos():
    """Get all logos as base64 encoded data URIs"""
    logos = {
        'main_logo': get_logo_base64('main_logo')
    }
    
    # Load all brand logos (15 logos)
    for i in range(1, 16):
        logo_name = f'brand_{i:02d}'
        logos[logo_name] = get_logo_base64(logo_name)
    
    return logos

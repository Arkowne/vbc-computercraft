import os
from pathlib import Path
import lib.bmi as bmi

def convert_png_folder_to_bmi(png_dir, output_dir, width=None, height=None, 
                              blur_sigma=0.5, contrast_alpha=1.5, contrast_beta=0,
                              unsharp_sigma=1.0, unsharp_amount=1.5, unsharp_threshold=0):
    png_dir = Path(png_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    png_files = sorted(png_dir.glob("*.png"))
    if not png_files:
        print(f"❌ No PNG files found in {png_dir}")
        return

    for idx, png_file in enumerate(png_files):
        output_file = output_dir / f"frame_{idx:05}.bmi"
        bmi.image_to_bmi(
            infile=str(png_file),
            outfile=str(output_file),
            width=width,
            height=height,
            blur_sigma=blur_sigma,
            contrast_alpha=contrast_alpha,
            contrast_beta=contrast_beta,
            unsharp_sigma=unsharp_sigma,
            unsharp_amount=unsharp_amount,
            unsharp_threshold=unsharp_threshold,
            silent=True,
        )
    print(f"✅ Conversion complete: {len(png_files)} .bmi files generated in {output_dir}")

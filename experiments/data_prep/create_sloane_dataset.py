#!/usr/bin/env python3
"""
Create Hugging Face dataset from Sloane index cards.

Dataset: British Library Sloane Manuscript Index Cards
Source: https://bl.iro.bl.uk/concern/datasets/30d16800-bcb2-4d86-8ffe-22f623424860
"""

import argparse
import os
import zipfile
from pathlib import Path

import requests
from datasets import Dataset
from datasets import Image as HFImage
from huggingface_hub import HfApi
from tqdm import tqdm

# Source URLs for all Sloane collections
SLOANE_SOURCES = {
    "sloane_ms_3972_c_1_jpegs.zip": "https://bl.iro.bl.uk/downloads/4c9c2b07-df76-4def-9636-5664918d67de?locale=en",
    "sloane_ms_3972_c_2_jpegs.zip": "https://bl.iro.bl.uk/downloads/7e6e201a-c619-4a93-ad40-5ac7fa59d428?locale=en",
    "sloane_ms_3972_c_3_jpegs.zip": "https://bl.iro.bl.uk/downloads/dd4ccdef-5a36-45a9-b96c-27069ac3a75a?locale=en",
    "sloane_ms_3972_c_4_jpegs.zip": "https://bl.iro.bl.uk/downloads/de5cab3b-b925-4fdc-952b-76aa29d0ccf2?locale=en",
    "sloane_ms_3972_c_5_jpegs.zip": "https://bl.iro.bl.uk/downloads/deb11521-7a33-4151-befc-a5c8488c738e?locale=en",
    "sloane_ms_3972_c_6_jpegs.zip": "https://bl.iro.bl.uk/downloads/800ed4cf-420b-4c06-a7c5-9b3fa20fea3b?locale=en",
    "sloane_ms_3972_c_7_jpegs.zip": "https://bl.iro.bl.uk/downloads/f63476df-8064-4df8-b486-2e96db3da350?locale=en",
    "sloane_ms_3972_c_8_jpegs.zip": "https://bl.iro.bl.uk/downloads/9facb091-4336-4d7c-a81d-5b58271752a6?locale=en",
    "sloane_ms_3972_d_jpegs.zip": "https://bl.iro.bl.uk/downloads/cdf99562-ce9d-4bea-8355-98eb1cfdc53f?locale=en",
}


def download_file(url: str, filepath: Path):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(filepath, "wb") as f:
        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc=f"Downloading {filepath.name}",
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))


def prepare_data(data_dir: Path, collections_to_use: list = None):
    """Download and extract Sloane collections if needed."""

    data_dir.mkdir(parents=True, exist_ok=True)

    # Determine which collections to process
    if collections_to_use:
        sources = {
            k: v
            for k, v in SLOANE_SOURCES.items()
            if any(c in k for c in collections_to_use)
        }
    else:
        sources = SLOANE_SOURCES

    for filename, url in sources.items():
        zip_path = data_dir / filename

        # Check if already extracted by looking for any JPG files
        # This is more robust than trying to predict the exact directory name
        if zip_path.exists():
            # Check if we have extracted files already
            base_pattern = filename.replace(".zip", "").replace("_", "*")
            existing_dirs = list(data_dir.glob(f"{base_pattern}*/"))
            if existing_dirs and any(existing_dirs[0].glob("*.jpg")):
                print(f"✓ {filename} already extracted")
                continue

        # Download if needed
        if not zip_path.exists():
            print(f"Downloading {filename}...")
            download_file(url, zip_path)

        # Extract
        print(f"Extracting {filename}...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(data_dir)


def create_dataset(data_dir: Path, max_samples: int = None):
    """Create dataset from Sloane index card images."""

    data = []

    # Find all JPG files recursively
    img_files = sorted(data_dir.rglob("*.jpg"))

    # Apply max_samples limit if specified
    if max_samples:
        img_files = img_files[:max_samples]

    for page_idx, img_path in tqdm(enumerate(img_files), desc="Processing images"):
        # Get collection name from parent directory
        collection_name = img_path.parent.name

        # Extract page number from filename
        # Format: sloane_ms_3972_c!2_224.jpg -> page 224
        page_num = None
        try:
            page_num = int(img_path.stem.split("_")[-1])
        except Exception:
            pass

        data.append(
            {
                "image": str(img_path),
                "filename": img_path.name,
                "collection": collection_name,
                "page_number": page_num,
                "page_index_in_directory": page_idx,
                "source": "British Library Sloane Manuscripts",
            }
        )

    # Create dataset without explicit features first
    dataset = Dataset.from_list(data)

    # Cast the image column from paths to Image type
    dataset = dataset.cast_column("image", HFImage())

    return dataset


def main():
    parser = argparse.ArgumentParser(description="Create Sloane index cards dataset")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./sloane_data"),
        help="Directory to store downloaded and extracted data",
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        default=None,
        help="Collections to include (e.g., c_1 c_2 c_5)",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum total number of samples (for testing)",
    )
    parser.add_argument(
        "--push-to-hub", action="store_true", help="Push dataset to Hugging Face Hub"
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default="davanstrien/sloane-index-cards",
        help="Repository ID on Hugging Face Hub",
    )
    parser.add_argument(
        "--private", action="store_true", help="Make the dataset private on Hub"
    )

    args = parser.parse_args()

    # Download and prepare data
    print(f"Preparing data in {args.data_dir}")
    prepare_data(args.data_dir, args.collections)

    # Create dataset
    print("Creating dataset from images")
    dataset = create_dataset(args.data_dir, args.max_samples)

    print("\n📊 Dataset Statistics:")
    print(f"Total samples: {len(dataset)}")

    # Count by collection
    collection_counts = {}
    for collection in dataset["collection"]:
        collection_counts[collection] = collection_counts.get(collection, 0) + 1
    print("\nBy collection:")
    for collection, count in sorted(collection_counts.items()):
        print(f"  {collection}: {count} samples")

    # Save locally
    local_path = Path("sloane_index_cards_dataset")
    dataset.save_to_disk(local_path)
    print(f"\n💾 Dataset saved locally to {local_path}")

    # Push to Hub if requested
    if args.push_to_hub:
        print(f"\n📤 Pushing to Hub: {args.repo_id}")
        dataset.push_to_hub(
            args.repo_id,
            private=args.private,
            commit_message="Upload Sloane manuscript index cards dataset",
        )

        # Create dataset card
        card_content = """---
task_categories:
- image-to-text
- text-extraction
language:
- en
tags:
- ocr
- handwriting-recognition
- historical-documents
- library-science
- index-cards
size_categories:
- n<1K
---

# Sloane Manuscript Index Cards Dataset

## Dataset Description

This dataset contains digitized index cards from the British Library's Sloane Manuscript collection. The cards represent a catalog system used to index the Sloane manuscripts, one of the founding collections of the British Museum (now British Library).

### Dataset Sources

- **Repository:** British Library Digital Collections
- **Original Dataset:** [Sloane Catalogues Dataset](https://bl.iro.bl.uk/concern/datasets/30d16800-bcb2-4d86-8ffe-22f623424860)
- **License:** CC Public Domain Mark 1.0

## Dataset Structure

The dataset contains index cards from multiple collections (c_1 through c_8 and d). The cards are primarily handwritten historical catalog entries, with some collections containing typewritten divider pages or forms.

### Data Fields

- `image`: The index card image
- `filename`: Original filename  
- `collection`: Source collection identifier (e.g., sloane_ms_3972_c!2_jpegs)
- `page_number`: Page number extracted from filename
- `source`: Source attribution

### Content Types

The cards contain various types of catalog information including:
- Author names and biographical information
- Manuscript titles and descriptions
- Shelfmarks and reference numbers
- Cross-references to other manuscripts
- Historical notes and annotations

## Use Cases

This dataset is ideal for:
- Testing OCR and handwriting recognition models on historical documents
- Evaluating Vision-Language Models (VLMs) on catalog cards
- Training models for library catalog digitization
- Information extraction from semi-structured historical documents
- Benchmarking on challenging handwritten text from multiple time periods

## Example Usage

```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("davanstrien/sloane-index-cards")

# Filter by collection
c2_cards = dataset.filter(lambda x: 'c_2' in x['collection'])

# Access an image
sample = dataset[0]
image = sample['image']  # PIL Image
```

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{sloane_index_cards_2024,
  title={Sloane Manuscript Index Cards Dataset},
  author={British Library},
  year={2024},
  publisher={Hugging Face},
  note={Derived from British Library Digital Collections}
}
```

## Acknowledgments

Thanks to the British Library for making these historical materials available under an open license. This dataset was created as part of research into AI applications for GLAM (Galleries, Libraries, Archives, and Museums) institutions.
"""

        api = HfApi()
        api.upload_file(
            path_or_fileobj=card_content.encode(),
            path_in_repo="README.md",
            repo_id=args.repo_id,
            repo_type="dataset",
            commit_message="Add comprehensive dataset card",
        )

        print(
            f"✅ Dataset successfully pushed to https://huggingface.co/datasets/{args.repo_id}"
        )


if __name__ == "__main__":
    main()

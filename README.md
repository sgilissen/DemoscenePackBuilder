# DemoscenePackBuilder
Easily build and download demoscene packs.
Powered by [Demozoo](https://www.demozoo.org) data.

## Installation
For now, a Python venv is needed.
Create a virtualenv, pip install requirements.txt

## Usage
``````
usage: dpbuilder.py [-h] [-lp] [-p PLATFORM | -pid PLATFORM_ID] [-cp COMPETITION_PLACE] [-rd RELEASE_DATE] [-o OUTPUT_DIR]

A simple demoscene pack generator, powered by the Demozoo.org API.

options:
  -h, --help            show this help message and exit
  -lp, --list_platforms
                        List all available platforms on Demozoo.
  -p PLATFORM, --platform PLATFORM
                        Filter by platform. Use quotes for platforms with spaces.For example: 'Amiga AGA' or 'ZX Spectrum'
  -pid PLATFORM_ID, --platform_id PLATFORM_ID
                        Filter by Demozoo platform ID.
  -cp COMPETITION_PLACE, --competition_place COMPETITION_PLACE
                        Minimum place in the competition.
  -rd RELEASE_DATE, --release_date RELEASE_DATE
                        Minimum release date (YYYY-MM-DD)
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Base output directory. Defaults to the users home directory, in the DPBuilder folder.

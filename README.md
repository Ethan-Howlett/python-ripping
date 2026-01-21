# Media Ripping Scripts

This repository contains scripts for automating DVD/Blu-ray ripping using MakeMKV with intelligent title selection and automatic movie metadata lookup.

## Files Overview

### `makemkv.py`
A Python script that automates the process of ripping DVDs and Blu-rays using MakeMKV. The script:

- **Scans the disc** using MakeMKV to identify available titles
- **Looks up movie information** from The Movie Database (TMDB) API to get official titles and release years
- **Intelligently selects the best title** to rip:
  - If there's a large size difference (>5 GB) between the two largest titles, it selects the largest (likely Director's Cut/Extended version)
  - If the size difference is small, it selects the smaller title (likely Theatrical version)
- **Creates organized folders** with proper naming: `Movie Title (Year)`
- **Rips the selected title** to an MKV file
- **Renames the output file** to match the folder name for easy identification
- **Displays progress** with a real-time progress bar during the rip process

### `rip.bat`
A simple Windows batch file that runs `makemkv.py` and pauses the window so you can view the output. This makes it easy to double-click and run the script without needing to open a terminal manually.

## Prerequisites

1. **Python 3.x** - Make sure Python is installed and accessible from your command line
2. **MakeMKV** - Download and install from [https://www.makemkv.com/](https://www.makemkv.com/)
3. **Python packages** - Install required dependencies:
   ```bash
   pip install python-dotenv requests
   ```
4. **TMDB API Key** - Get a free API key from [https://www.themoviedb.org/](https://www.themoviedb.org/)
   - Sign up for a free account
   - Go to Settings → API → Request an API Key
   - Copy your API key

## Setup Instructions

### Step 1: Create a `.env` file

Create a `.env` file in the same directory as `makemkv.py` with the following variables:

1. **TMDB_API_KEY** - Your TMDB API key (required)
2. **MAKEMKVCON_PATH** - Full path to your MakeMKV executable (required)
3. **RIP_OUTPUT_ROOT** - Root folder where all ripped movies will be saved (required)

### Step 2: Fill out the `.env` file

Open the `.env` file and replace the placeholder values with your actual configuration:

- **TMDB_API_KEY**: Paste your TMDB API key
- **MAKEMKVCON_PATH**: 
  - Windows: Usually `C:\Program Files (x86)\MakeMKV\makemkvcon.exe`
  - macOS/Linux: `makemkvcon` (if MakeMKV is in your system PATH)
- **RIP_OUTPUT_ROOT**: Set this to where you want your ripped movies stored
  - Example: `D:\Movies` or `C:\Users\YourName\Videos\Ripped Movies`

See `example.env` for a template with the correct variable names.

### Step 3: Verify MakeMKV Installation

Make sure MakeMKV is installed and the path in `MAKEMKVCON_PATH` is correct. You can test this by running:
```bash
"C:\Program Files (x86)\MakeMKV\makemkvcon.exe" -r info disc:0
```

## Usage

### Windows (Recommended)
1. Insert your DVD or Blu-ray disc
2. Double-click `rip.bat`
3. Wait for the script to complete (this may take a while depending on disc size)

### Command Line
Alternatively, you can run the script directly:
```bash
python makemkv.py
```

## How It Works

1. The script scans the disc at index 0 (first optical drive)
2. Extracts the disc title from MakeMKV's output
3. Searches TMDB for the movie to get the official title and release year
4. Creates a folder named `Movie Title (Year)` in your output directory
5. Analyzes all available titles and selects the best one based on size
6. Rips the selected title to an MKV file
7. Renames the output file to match the folder name

## Output Structure

All ripped movies will be organized in your `RIP_OUTPUT_ROOT` directory like this:

```
RIP_OUTPUT_ROOT/
├── The Martian (2015)/
│   └── The Martian (2015).mkv
├── Inception (2010)/
│   └── Inception (2010).mkv
└── ...
```

## Troubleshooting

### "TMDB_API_KEY is not set"
- Make sure you've created a `.env` file
- Verify the variable name is exactly `TMDB_API_KEY` (case-sensitive)
- Check that the `.env` file is in the same directory as `makemkv.py`

### "MAKEMKVCON_PATH is not set"
- Create or update your `.env` file with the correct path to `makemkvcon.exe`
- Use forward slashes `/` or double backslashes `\\` in Windows paths
- Example: `C:/Program Files (x86)/MakeMKV/makemkvcon.exe`

### "Command not found: makemkvcon"
- Verify MakeMKV is installed
- Check that the path in `MAKEMKVCON_PATH` is correct
- Make sure the path uses the correct executable name (`makemkvcon.exe` on Windows)

### Script can't find the disc
- Make sure a disc is inserted in your optical drive
- The script uses disc index 0 by default (first drive)
- If you have multiple drives, you may need to modify `DISC_INDEX` in the script

### TMDB search fails
- Check your internet connection
- Verify your API key is correct
- The script will fall back to using the disc title if TMDB lookup fails

## Notes

- The script assumes you want to rip from disc index 0 (the first optical drive)
- If you have multiple optical drives, you may need to modify the `DISC_INDEX` variable in the script
- The title selection logic prioritizes theatrical versions when sizes are similar, and extended/director's cuts when there's a significant size difference
- Large discs may take a long time to rip - be patient!

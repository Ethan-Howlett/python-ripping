import os
import re
import sys
import subprocess
import requests # Used for TMDB API calls
from dotenv import load_dotenv

# --- ⚙️ CONFIGURATION ---
load_dotenv()
# 1. Get a free API key from https://www.themoviedb.org/
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY is not set")

# 2. Set the path to your makemkvcon executable
#    Windows: r"C:\Program Files (x86)\MakeMKV\makemkvcon.exe"
#    macOS/Linux: "makemkvcon" (if in system PATH)
MAKEMKVCON_PATH = os.getenv("MAKEMKVCON_PATH")
if not MAKEMKVCON_PATH:
    raise ValueError("MAKEMKVCON_PATH is not set")

# 3. Set the root folder where all your new movie folders will be created
RIP_OUTPUT_ROOT = os.getenv("RIP_OUTPUT_ROOT")
if not RIP_OUTPUT_ROOT:
    raise ValueError("RIP_OUTPUT_ROOT is not set")

# 4. Set the disc index (0 is usually the first optical drive)
DISC_INDEX = 0

# --- SCRIPT LOGIC ---

def run_command(command):
    """A helper function to run shell commands and return their output."""
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        return result.stdout
    except FileNotFoundError:
        print(f"❌ ERROR: Command not found: '{command[0]}'. Is it in your system's PATH?")
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Command failed: {' '.join(command)}")
        print(f"         STDERR: {e.stderr}")
        return None

def get_movie_details_from_tmdb(disc_title):
    """Searches TMDB for a movie title and returns its name and year."""
    if not TMDB_API_KEY or TMDB_API_KEY == "YOUR_TMDB_API_KEY_HERE":
        return None # Skip if API key is not set

    print(f"🔍 Searching TMDB for '{disc_title}'...")
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': disc_title.replace('_', ' ') # Clean up title for searching
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()

        if data['results']:
            # Assume the first result is the correct one
            movie = data['results'][0]
            title = movie['title']
            year = movie['release_date'].split('-')[0] if movie.get('release_date') else 'N/A'
            print(f"✅ Found: {title} ({year})")
            return {'title': title, 'year': year}
    except requests.RequestException as e:
        print(f"❌ ERROR: Could not connect to TMDB: {e}")

    print("⚠️ TMDB search failed. Will use the title from the disc.")
    return None

def rip_disc():
    """Main function to scan, name, and rip the disc."""
    # 1. Get disc information from makemkvcon
    print(f"🔎 Scanning disc at index: {DISC_INDEX}...")
    info_command = [MAKEMKVCON_PATH, "-r", "info", f"disc:{DISC_INDEX}"]
    disc_info = run_command(info_command)

    if not disc_info:
        print("🛑 Aborting script.")
        return

    # 2. Extract the disc title (e.g., "THE_MARTIAN")
    disc_title = "UnknownMovie"
    match = re.search(r'CINFO:2,0,"(.*?)"', disc_info)
    if match:
        disc_title = match.group(1)

    # 3. Get official movie details from TMDB
    movie_details = get_movie_details_from_tmdb(disc_title)

    # Sanitize folder name to remove characters invalid for file systems
    if movie_details:
        folder_name = f"{movie_details['title']} ({movie_details['year']})"
        sanitized_folder_name = re.sub(r'[\\/*?:"<>|]', "", folder_name)
    else:
        sanitized_folder_name = re.sub(r'[\\/*?:"<>|]', "", disc_title)

    # 4. Create the destination folder
    destination_folder = os.path.join(RIP_OUTPUT_ROOT, sanitized_folder_name)
    print(f"📁 Creating movie folder: {destination_folder}")
    os.makedirs(destination_folder, exist_ok=True)

    # 5. Find all titles and sort by size to get the two largest
    titles = []
    for line in disc_info.splitlines():
        match = re.search(r'TINFO:(\d+),11,0,"(\d+)"', line)
        if match:
            title_id = int(match.group(1))
            size_bytes = int(match.group(2))
            titles.append({'id': title_id, 'size': size_bytes})
    
    if not titles:
        print("❌ ERROR: Could not find any titles to rip.")
        return
    
    # Sort by size (largest first)
    titles.sort(key=lambda x: x['size'], reverse=True)
    
    # Determine which title to rip based on size comparison
    selected_title = titles[0]  # Default to largest
    
    if len(titles) >= 2:
        largest = titles[0]
        second_largest = titles[1]
        size_diff_gb = (largest['size'] - second_largest['size']) / 1e9
        
        print(f"📊 Found two largest titles:")
        print(f"   Title {largest['id']}: {largest['size'] / 1e9:.2f} GB")
        print(f"   Title {second_largest['id']}: {second_largest['size'] / 1e9:.2f} GB")
        print(f"   Size difference: {size_diff_gb:.2f} GB")
        
        if size_diff_gb > 5:
            # Large difference: the biggest is likely director's cut, use it
            selected_title = largest
            print(f"✅ Selecting largest title (likely Director's Cut/Extended)")
        else:
            # Small difference: the smaller is likely theatrical version
            selected_title = second_largest
            print(f"✅ Selecting smaller title (likely Theatrical version)")
    else:
        print(f"📊 Only one title found")
    
    print(f"✅ Final selection: Title ID {selected_title['id']} ({selected_title['size'] / 1e9:.2f} GB)")

    # 6. Rip the main title to the new folder
    print(f"🎬 Starting rip. This will take a while...")
    print(f"📂 Output folder: {destination_folder}")
    print(f"🔧 Command: {' '.join([MAKEMKVCON_PATH, '-r', 'mkv', f'disc:{DISC_INDEX}', str(selected_title['id']), destination_folder])}")
    
    rip_command = [
        MAKEMKVCON_PATH,
        "-r",
        "mkv",
        f"disc:{DISC_INDEX}",
        str(selected_title['id']),
        destination_folder
    ]

    # Run the rip command.
    try:
        process = subprocess.Popen(
            rip_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1,
        )

        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line.startswith('PRGV'):
                try:
                    parts = line.split(':')[1].split(',')
                    current = int(parts[0])
                    total = int(parts[1])
                    if total > 0:
                        percent = (current / total) * 100
                        # Print a dynamic progress bar on a single line
                        progress_bar = '#' * int(percent / 4)
                        sys.stdout.write(f'\r   [{progress_bar:<25}] {percent:.1f}% completed')
                        sys.stdout.flush()
                except (ValueError, IndexError):
                    pass
            # elif line.startswith('MSG:'):
            #     # Print important messages from MakeMKV
            #     print(f"\n   ℹ️  {line}")
            elif 'Saving' in line or 'saved' in line or 'Copy complete' in line:
                # Print save-related messages
                print(f"\n   ℹ️  {line}")

        process.wait()
        print()
        if process.returncode == 0:
            print("\n✨ Rip process completed!")
            
            # Verify the file was actually created
            mkv_files = [f for f in os.listdir(destination_folder) if f.endswith('.mkv')]
            
            if mkv_files:
                print(f"✅ Successfully created {len(mkv_files)} file(s):")
                for mkv_file in mkv_files:
                    file_path = os.path.join(destination_folder, mkv_file)
                    file_size_gb = os.path.getsize(file_path) / 1e9
                    print(f"   📁 {mkv_file} ({file_size_gb:.2f} GB)")
                
                # Rename the .mkv file to match the folder name
                if len(mkv_files) == 1:
                    old_file_path = os.path.join(destination_folder, mkv_files[0])
                    new_file_name = f"{sanitized_folder_name}.mkv"
                    new_file_path = os.path.join(destination_folder, new_file_name)
                    
                    if mkv_files[0] != new_file_name:
                        try:
                            os.rename(old_file_path, new_file_path)
                            print(f"\n🔄 Renamed file to: {new_file_name}")
                        except Exception as e:
                            print(f"\n⚠️ Warning: Could not rename file: {e}")
                    else:
                        print(f"\n✅ File already has correct name: {new_file_name}")
                elif len(mkv_files) > 1:
                    print(f"\n⚠️ Multiple .mkv files found - skipping rename to avoid overwriting")
                
                print(f"\n📂 Location: {destination_folder}")
            else:
                print(f"⚠️ WARNING: Rip completed but no .mkv files found in:")
                print(f"   {destination_folder}")
                print(f"\n🔍 Checking what files exist in the folder:")
                all_files = os.listdir(destination_folder)
                if all_files:
                    for f in all_files:
                        print(f"   - {f}")
                else:
                    print("   (folder is empty)")
        else:
            print(f"\n❌ ERROR: Ripping process failed with return code {process.returncode}.")

        
    except FileNotFoundError:
        print(f"❌ ERROR: Command not found: '{rip_command[0]}'. Is it in your system's PATH?")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred during the rip: {e}")

if __name__ == "__main__":
    # Ensure the root output directory exists before starting
    os.makedirs(RIP_OUTPUT_ROOT, exist_ok=True)
    rip_disc()

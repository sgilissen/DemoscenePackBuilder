import errno

import requests
import argparse
import sys
from tqdm import tqdm
from datetime import datetime
from os import path, makedirs, remove, listdir, rmdir

DEMOZOO_API_ENDPOINT = 'https://demozoo.org/api/v1/'
DEMOZOO_PRODS_ENDPOINT = 'productions/'
DEMOZOO_PLATFORMS_ENDPOINT = 'platforms/'
FIELDS = ['release_date', 'title', 'author_nicks', 'download_links', 'demozoo_url', 'url']


def parse_date(date_string):
    try:
        # Adjust the format to match the expected date format
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD.")

def dir_path(string):
    if path.isdir(string):
        return string
    else:
        try:
            makedirs(string)
            return string
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise



def fuzzy_search(query, platforms):
    query_lower = query.lower()
    best_match = None
    best_match_length = float('inf')  # Start with a large number

    for platform_id, platform_name in platforms.items():
        platform_name_lower = platform_name.lower()
        if query_lower in platform_name_lower:
            current_length = len(platform_name_lower)
            if current_length < best_match_length:
                best_match = (platform_id, platform_name)
                best_match_length = current_length

    return best_match

def get_platforms():
    print('Fetching platform data...')
    try:
        req = requests.get(DEMOZOO_API_ENDPOINT + DEMOZOO_PLATFORMS_ENDPOINT)
        data = req.json()['results']
        # Sort platforms by ID
        data.sort(key=lambda x: x['id'])
        # Sanitize data into a single dict
        platforms = {}

        for platform in data:
            platforms[platform['id']] = platform['name']

        return platforms
    except requests.exceptions.ConnectionError:
        print("There was an error connecting to Demozoo. :(")

def get_prods_list(**kwargs):
    platform_id = 0
    filters = []

    if 'platform_id' in kwargs and kwargs['platform_id'] is not None:
        print(f"Using Demozoo platform ID {kwargs['platform_id']}: {get_platforms()[kwargs['platform_id']]} ")
        platform_id = kwargs['platform_id']
    elif 'platform' in kwargs and kwargs['platform'] is not None:
        match_platform = fuzzy_search(kwargs['platform'], get_platforms())
        print(f'Matched with Demozoo platform ID {match_platform[0]}: {match_platform[1]}')
        platform_id = match_platform[0]

    # Set up filters
    # Platform type
    filters.append(f"platform={platform_id}")
    # Production type (currently hardcoded to "demo")
    filters.append(f"production_type=1")
    if 'release_date' in kwargs and kwargs['release_date'] is not None:
        filters.append(f"released_since={datetime.strftime(kwargs['release_date'], '%Y-%m-%d')}")

    if 'competition_place' in kwargs and kwargs['competition_place'] is not None:
        filters.append(f"competition_placing_min={kwargs['competition_place']}")

    # join the fields to a string
    fields = ','.join(FIELDS)

    # join the filters to a string
    filters_str = '&'.join(filters)

    print('Fetching data from Demozoo...')
    fetch_url = DEMOZOO_API_ENDPOINT + DEMOZOO_PRODS_ENDPOINT + '?' + filters_str + "&fields=" + fields
    print(fetch_url)
    req = requests.get(fetch_url)
    data = req.json()
    results = []
    entry_count = data['count']
    print(f'Found {entry_count} entries.')
    next_url = data['next']
    current_page = 1
    if next_url is not None:
        while next_url is not None:
            results.extend(data['results'])
            print(f'Fetching page {current_page}')
            req = requests.get(next_url)
            data = req.json()
            next_url = data['next']
            current_page += 1
        results.extend(data['results'])
    else:
        results.extend(data['results'])

    print(f'Fetched {len(results)} entries.')

    return results

def download_prod(prod, cur_prod=1, total_prods=1, root_dir=None):
    prod_name = prod['title']
    if len(prod['author_nicks']) > 0:
        author_field = prod['author_nicks'][0]['name']
    else:
        author_field = '_UNSORTED'

    download_links = []
    print(len(download_links))
    if len(prod['download_links']) > 0:
        for link in prod['download_links']:
            download_links.append(link['url'])
    else:
        return

    release_date = prod['release_date']
    if author_field == '_UNSORTED':
        by_author = f' (group or author unknown, fill will be downloaded to _UNSORTED folder)'
    else:
        by_author = f' by {author_field}'
    print(f'[{cur_prod} of {total_prods}] Downloading "{prod_name}"{by_author} ({release_date[:4]})...')

    folder_path = path.join(root_dir, release_date[:4], author_field)
    # Create the folder if it doesn't exist
    makedirs(folder_path, exist_ok=True)

    file_name = path.basename(download_links[0])
    # Ensure file_name is not empty
    if not file_name:
        print("Invalid file name extracted from URL.")
        return

    file_path = path.join(str(folder_path), str(file_name))

    num_links = len(download_links)
    cur_link = 1
    for url in download_links:
        try:
            print(f'Trying to download file from URL {cur_link}')
            req = requests.get(url, stream=True, timeout=10)
            req.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
            total_size = int(req.headers.get('content-length', 0))
            block_size = 1024
            with tqdm(total=total_size, unit='B', unit_scale=True) as progress_bar:
                with open(file_path, 'wb') as f:
                    for chunk in req.iter_content(chunk_size=block_size):
                        progress_bar.update(len(chunk))
                        f.write(chunk)

            if total_size != 0 and progress_bar.n != total_size:
                if num_links > 0 and cur_link < num_links:
                    print(f"File is incomplete... Trying next URL (currently {cur_link} of {num_links}).")
                    cur_link += 1
                remove(file_path)  # Delete the incomplete file
                print(f"Deleted incomplete file: {file_path}")

                # Check if the folder is empty
                if not listdir(str(folder_path)):
                    rmdir(folder_path)  # Delete the empty folder
                    print(f"Deleted empty folder: {folder_path}")
                continue

            print(f"Succesfully downloaded {file_name}!")

            break  # Exit the loop since the download was successful
        except Exception as e:
            print(f"Failed to download {url}: {e}")

            continue



def main(arguments):
    if arguments.list_platforms:
        platforms = get_platforms()
        print('--- Available platforms: ---')
        print('ID - Name')
        for platform in platforms:
            print(platform, platforms[platform])

    else:
        # Remove unused arguments
        for arg in ['list_platforms']: delattr(arguments, arg)
        # Get prods list using remaining arguments
        args_dict = vars(arguments)
        prods = get_prods_list(**args_dict)

        total_num_prods = len(prods)
        for num, prod in enumerate(prods, start=1):
            download_prod(prod, cur_prod=num, total_prods=total_num_prods, root_dir=arguments.output_dir)

        print("")
        print("--- All done! :) ---")


if __name__ == '__main__':
    # Create the parser
    parser = argparse.ArgumentParser(description="A simple demoscene pack generator, powered by the Demozoo.org API.")

    # Add arguments
    parser.add_argument("-lp",
                        "--list_platforms",
                        action="store_true",
                        help="List all available platforms on Demozoo."
                        )

    # Create a mutually exclusive group
    arg_group = parser.add_mutually_exclusive_group()

    arg_group.add_argument("-p",
                       "--platform",
                       type=str,
                       help="Filter by platform. Use quotes for platforms with spaces."
                            "For example: 'Amiga AGA' or 'ZX Spectrum'"
                       )

    arg_group.add_argument("-pid",
                       "--platform_id",
                       type=int,
                       help="Filter by Demozoo platform ID."
                       )

    parser.add_argument("-cp",
                        "--competition_place",
                        type=int,
                        help="Minimum place in the competition."
                        )

    parser.add_argument("-rd",
                        "--release_date",
                        type=parse_date,
                        help="Minimum release date (YYYY-MM-DD)",
                        )

    parser.add_argument("-o",
                        "--output_dir",
                        type=dir_path,
                        default=path.join(path.expanduser('~'), 'DPBuilder'),
                        help="Base output directory. Defaults to the users home directory, in the DPBuilder folder.",
                        )

    # Parse the arguments
    args = parser.parse_args()

    if not (args.platform or args.platform_id):
        print("Error: Please specify either --platform/-p or --platform_id/-pid.")
        sys.exit(1)

    # Check if no arguments were provided
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Call the main function with the parsed arguments
    main(args)


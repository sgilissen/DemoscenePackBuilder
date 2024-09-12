import errno
from time import sleep
from zipfile import ZipFile

import requests
import argparse
import sys

from pyunpack import Archive
from tqdm import tqdm
from datetime import datetime
from os import path, makedirs, remove, listdir, rmdir

from bs4 import BeautifulSoup
import pandas as pd

def get_prod_list():
    print("Fetching data from whdload.de...")
    root_url = "https://www.whdload.de/demos/"
    endpoint = "allv.html"
    data = requests.get(root_url + endpoint).text

    soup = BeautifulSoup(data, "html.parser")

    table = soup.find('table')
    df = pd.DataFrame(
        columns=['Name', 'DownloadURL', 'Info', 'Bytes', 'Date', 'DC', 'Author / Contact', 'BitWorld', 'ADA', 'Pouët',
                 'Images'])

    for row in table.find_all('tr'):
        columns = row.find_all('td')

        if columns != []:
            name = columns[0].text.strip()
            download_url = root_url + columns[0].find('a')['href']
            info = columns[1].text.strip()
            date = columns[2].text.strip()
            byte_count = columns[3].text.strip()
            dc = columns[4].text.strip()
            author = columns[5].text.strip()
            bitworld = columns[6].text.strip()
            ada = columns[7].text.strip()
            pouet = columns[8].text.strip()
            images = columns[9].text.strip()

            df = pd.concat([df, pd.DataFrame([{
                'Name': name,
                'DownloadURL': download_url,
                'Info': info,
                'Bytes': byte_count,
                'Date': date,
                'DC': dc,
                'Author / Contact': author,
                'BitWorld': bitworld,
                'ADA': ada,
                'Pouët': pouet,
                'Images': images
            }])], ignore_index=True)

    print(f'Found {len(df)} entries.\n')
    return df


def download_file(download_url, download_root):
    # Extract the filename from the URL
    filename = download_url.split('/')[-1]

    # Extract the group name from the filename (assuming the filename format is GroupName_Production.lha)
    group_name = filename.split('_')[0]

    # Create the directory for the group if it doesn't exist
    group_dir = path.join(download_root, group_name)
    makedirs(group_dir, exist_ok=True)

    # Full path where the file will be saved
    file_path = path.join(group_dir, filename)

    # Send a GET request to the URL
    response = requests.get(download_url, stream=True)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the total file size from headers
        total_size = int(response.headers.get('content-length', 0))

        # Download the file with a progress bar
        with open(file_path, 'wb') as file, tqdm(
                desc=filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                ncols=80,
                leave=True
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
                bar.update(len(chunk))
    else:
        print(f"Failed to download {download_url}")


if __name__ == '__main__':
    download_dir = path.join(path.expanduser('~'), 'AmigaDemoWHDLoad')

    list_df = get_prod_list()
    # for index, row in list_df.iterrows():
    #     print(row['Name'], row['DownloadURL'])
    for download_url in tqdm(list_df['DownloadURL'], desc="Downloading files"):
        download_file(download_url, download_dir)
        sleep(1) # Sleeping a bit to be nice to the website :)
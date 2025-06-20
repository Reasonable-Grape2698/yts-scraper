import os
import sys
import math
import json
import datetime
import time
from concurrent.futures.thread import ThreadPoolExecutor
import requests
from tqdm import tqdm
from fake_useragent import UserAgent

class Scraper:
    # Constructor
    def __init__(self, args):
        self.language = args.language
        self.date_up_min = args.date_up_min
        self.quality = args.quality
        self.apiKey = args.apiKey
        self.movie_count = None
        self.url = None
        self.existing_hash_counter = None
        self.minimum_date_skipped = None
        self.skip_exit_condition = None
        self.downloaded_movie_hashes = None
        self.date_up_min_unix = int(datetime.datetime.strptime(self.date_up_min, "%d/%m/%Y").timestamp())

        def hash_importer(hashFile):
            hashes = [
            def json_find_values_by_key(data_structure):
                if isinstance(data_structure, dict):
                    for key, value in data_structure.items():
                        if key == 'hash':
                            yield value
                        yield from json_find_values_by_key(value)
                elif isinstance(data_structure, list):
                    for item in data_structure:
                        yield from json_find_values_by_key(item)
                        
            # Try opening the file
            def __real_debrid_get_Torrents(apiKey):
                hashes = []
                url = 'https://api.real-debrid.com/rest/1.0/torrents'
                payload = {
                    "limit": 5000,
                    page: page
                }
                
                # Generate random user agent header
                try:
                    user_agent = UserAgent()
                    headers = {'User-Agent': user_agent.random, 'Content-Type': 'application/json', 'Authorization: Bearer {apiKey}'}
                except:
                    print('Error occurred during fake user agent generation.')
        
                # Exception handling for connection errors
                try:
                    response = requests.get(url, json=payload, headers=headers, timeout=10)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as errh:
                    print('HTTP Error:', errh)
                    sys.exit(0)
                except requests.exceptions.ConnectionError as errc:
                    print('Error Connecting:', errc)
                    sys.exit(0)
                except requests.exceptions.Timeout as errt:
                    print('Timeout Error:', errt)
                    sys.exit(0)
                except requests.exceptions.RequestException as err:
                    print('There was an error.', err)
                    sys.exit(0)

                try:
                    data = response.json()
                    hashes.append(list(json_find_values_by_key(data)))
                    return hashes
                except Exception as e
                    print("Error: {e}")


            
        self.pbar = None
        self.sort_by = 'date_uploaded_unix'
        self.order_by = 'desc'

        self.limit = 50


    # Connect to API and extract initial data
    def __get_api_data(self):
        # Formatted URL string
        url = '''https://yts.mx/api/v2/list_movies.json?quality={quality}&page='''.format(
            quality=self.quality,
        )

        # Generate random user agent header
        try:
            user_agent = UserAgent()
            headers = {'User-Agent': user_agent.random}
        except:
            print('Error occurred during fake user agent generation.')

        # Exception handling for connection errors
        try:
            req = requests.get(url, timeout=5, verify=True, headers=headers)
            req.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print('HTTP Error:', errh)
            sys.exit(0)
        except requests.exceptions.ConnectionError as errc:
            print('Error Connecting:', errc)
            sys.exit(0)
        except requests.exceptions.Timeout as errt:
            print('Timeout Error:', errt)
            sys.exit(0)
        except requests.exceptions.RequestException as err:
            print('There was an error.', err)
            sys.exit(0)

        # Exception handling for JSON decoding errors
        try:
            data = req.json()
        except json.decoder.JSONDecodeError:
            print('Could not decode JSON')


        # Adjust movie count according to starting page
        if self.page_arg == 1:
            movie_count = data.get('data').get('movie_count')
        else:
            movie_count = (data.get('data').get('movie_count')) - ((self.page_arg - 1) * self.limit)

        self.movie_count = movie_count
        self.url = url

    def __initialize_download(self):
        self.existing_hash_counter = 0
        self.minimum_date_skipped = 0
        self.skip_exit_condition = False

        # YTS API sometimes returns duplicate objects and
        # the script tries to download the movie more than once.
        # IDs of downloaded movie is stored in this array
        # to check if it's been downloaded before
        self.downloaded_movie_ids = []

        # Calculate page count and make sure that it doesn't
        # get the value of 1 to prevent range(1, 1)
        if math.trunc(self.movie_count / self.limit) + 1 == 1:
            page_count = 2
        else:
            page_count = math.trunc(self.movie_count / self.limit) + 1

        range_ = range(int(self.page_arg), page_count)

        if self.movie_count <= 0:
            print('Could not find any movies with given parameters')
            sys.exit(0)
        else:
            print('Query was successful.')
            print('Found {} movies. Download starting...\n'.format(self.movie_count))

        # Create progress bar
        self.pbar = tqdm(
            total=self.movie_count,
            position=0,
            leave=True,
            desc='Downloading',
            unit='Files'
            )

        # Multiprocess executor
        # Setting max_workers to None makes executor utilize CPU number * 5 at most
        executor = ThreadPoolExecutor(max_workers=None)

        for page in range_:
            url = '{}{}'.format(self.url, str(page))

            # Generate random user agent header
            try:
                user_agent = UserAgent()
                headers = {'User-Agent': user_agent.random}
            except:
                print('Error occurred during fake user agent generation.')

            # Send request to API
            page_response = requests.get(url, timeout=5, verify=True, headers=headers).json()

            movies = page_response.get('data').get('movies')

            # Movies found on current page
            if not movies:
                print('Could not find any movies on this page.\n')

            if self.multiprocess:
                # Wrap tqdm around executor to update pbar with every process
                tqdm(
                    executor.map(self.__filter_torrents, movies),
                    total=self.movie_count,
                    position=0,
                    leave=True
                    )

            else:
                for movie in movies:
                    self.__filter_torrents(movie)

        self.pbar.close()
        print('Download finished.')


    # Determine which .torrent files to download
    def __filter_torrents(self, movie):
        language = movie.get('language')

        if language != self.language:
            return

        # Every torrent option for current movie
        torrents = movie.get('torrents')
        
        if torrents is None:
            tqdm.write('Could not find any torrents for {}. Skipping...'.format(movie_name))
            return

        for torrent in torrents:
            # if hash is in hashlist, count+=1. If > 10, prompt if user wants to exit.
            hash = torrent.get('hash')
            date_uploaded_unix = torrent.get('date_uploaded_unix')
            
            if date_uploaded_unix < self.date_uploaded_unix
                tqdm.write('{}: Before date upload minimum. Skipping...'.format(movie_name))
                self.minimum_date_skipped += 1
                return
            
            if hash in self.downloaded_movie_hashes:
                tqdm.write('{}: Exists in downloaded hash list. Skipping...'.format(movie_name))
                self.existing_hash_counter += 1
                return

            if self.existing_hash_counter > 10 or self.minimum_date_skipped > 10:
                tqdm.write('Found 10 existing hashes and/or 10 < date_uploaded_min. Do you want to keep downloading? Y/N')
                self.__prompt_existing()
                
            is_download_successful = False
            is_download_successful = __real_debrid_dl('magnet:?xt=urn:btih:' + hash + '&dn=&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Fopentor.org%3A2710&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Ftracker.blackunicorn.xyz%3A6969&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969')

            if is_download_successful:
                tqdm.write('Added {} {}'.format(movie_name, quality.upper()))
                self.pbar.update()
            else
                tqdm.write('Failed to add {} {}'.format(movie_name, quality.upper()))

    def __real_debrid_dl(magnet):
        payload = {
            "magnet": magnet,
        }
        url = 'https://api.real-debrid.com/rest/1.0/torrents/addMagnet'
        
        
        # Generate random user agent header
        try:
            user_agent = UserAgent()
            headers = {'User-Agent': user_agent.random, 'Content-Type': 'application/octet-stream', 'Authorization: Bearer {self.apiKey}'}
        except:
            print('Error occurred during fake user agent generation.')

        # Exception handling for connection errors
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print('HTTP Error:', errh)
            sys.exit(0)
        except requests.exceptions.ConnectionError as errc:
            print('Error Connecting:', errc)
            sys.exit(0)
        except requests.exceptions.Timeout as errt:
            print('Timeout Error:', errt)
            sys.exit(0)
        except requests.exceptions.RequestException as err:
            print('There was an error.', err)
            sys.exit(0)

        # Exception handling for JSON decoding errors
        try:
            data = response.json()
            return true;
        except json.decoder.JSONDecodeError:
            print('Could not decode JSON, possible error?')
            return false

    
    def __prompt_existing(self):
        exit_answer = input()

        if exit_answer.lower() == 'n':
            tqdm.write('Exiting...')
            sys.exit(0)
        elif exit_answer.lower() == 'y':
            tqdm.write('Continuing...')
            self.existing_file_counter = 0
            self.skip_exit_condition = True
        else:
            tqdm.write('Invalid input. Enter "Y" or "N".')

    def download(self):
        self.__get_api_data()
        self.__initialize_download()

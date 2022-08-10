"""
Fast Genius Lyrics (genius.com) Scraper Using Python

Written by Nikhil Nayak
"""
import argparse
import requests
from requests.adapters import HTTPAdapter, Retry
import multiprocessing
import json
from tqdm import tqdm
from bs4 import BeautifulSoup
import time
import traceback



batch_size = 1024
num_threads = 128

class OptionalChain:
    """
    Simulates The Javascript Optional Chaining Operator

    Example:
    .. code-block:: python

    obj = {
        "a": 1,
        "b": {
            "c": 2
        }
    }

    JS: obj?.a?.something # null
    Python: obj.a.something.value() # None

    Note:
    The Subscript operator can also be used 
    Ex: obj["key"].value()
    """

    def __init__(self, obj):
        self.obj = obj
        self.or_ = None
    
    def __getattr__(self, key):
        if type(self.obj) != dict or key not in self.obj:
            return OptionalChain(self.or_)

        return OptionalChain(self.obj[key])

    def __getitem__(self, key):
        return self.__getattr__(key)

    def value(self):
        return self.obj

def _map_kv_array(l):
    """"
    Converts [{"key": x, "value": y}, {"key": a, "value": b}] to {x: y, a: b}
    
    Useful for parsing JSON data from genius.com
    """
    if l == None:
        return None

    out = {}
    for item in l:
        if "values" in item:
            item["value"] = item["values"]
        if "name" in item:
            item["key"] = item["name"]

        out[item["key"]] = item["value"]

    return out


#@profile
def _scrape(song_id, print_json=False):
    """
    Scrapes a song ID from genius.com and returns data about the song
    """
    try:
        sess = requests.Session()
        retry = Retry(
            total=5,
            status_forcelist=[413, 429, 500, 502, 503, 504]
        )
        sess.mount("https://", HTTPAdapter(max_retries=retry))

        res = sess.get(f"https://genius.com/songs/{song_id}")
        if res.status_code != 200:
            print("bad code")
            return None

        text = res.text
        lines = text.split("\n")

        JSON_PREFIX="window.__PRELOADED_STATE__ = JSON.parse('"
        JSON_POSTFIX="');"
        for line in lines:
            line = line.strip()
            if not line.startswith(JSON_PREFIX):
                continue
            json_string = line[len(JSON_PREFIX):-len(JSON_POSTFIX)]

            json_string = json_string.replace("\\\"", "\"")
            json_string = json_string.replace("\\\\\"", "\\\"")
            json_string = json_string.replace("\\'", "'")
            json_string = json_string.replace("\\", "")

            if print_json:
                print(json_string)

            data = OptionalChain(json.loads(json_string))
            dfp = OptionalChain({**_map_kv_array(data.songPage.trackingData.value()), **_map_kv_array(data.songPage.dfpKv.value())})


            pageType = data.songPage.pageType.value()
            lyrics = BeautifulSoup(data.songPage.lyricsData.body.html.value(), "lxml").text

            title = {
                "name": dfp.Title.value(),
                "id": dfp["Song ID"].value()
    
            }

            artist = {
                "name": dfp["Primary Artist"].value(),
                "id": dfp["Primary Artist ID"].value()
            }

            genre = dfp.Tag.value()
            isMusic = dfp["Music?"].value()
            releaseDate = dfp["Release Date"].value()
            language = dfp["Lyrics Language"].value()
            topic = dfp.topic.value()
            url = data.songPage.path.value()

            return {
                "id": song_id,
                "pageType": pageType,
                "lyrics": lyrics,
                "title": title,
                "artist": artist,
                "genre": genre,
                "isMusic": isMusic,
                "releaseDate": releaseDate,
                "language": language,
                "topic": topic,
                "url": url
            }
    except Exception as e:
        print(song_id)
        print(traceback.format_exc())
        return None
        



#_scrape(510, print_json=True)
#quit()

with multiprocessing.Pool(num_threads) as pool:
    i = 0
    while True:
        start = i * batch_size
        end = start + batch_size

        song_ids = list(range(start, end))
        
        start = time.time()
        res = pool.map(_scrape, song_ids)
        
        with open(f"data/{i}.json", "w", encoding="utf-8") as of:
          json.dump(res, of)

        end = time.time()

        print(f"Batch #{i} took {end-start} seconds")

        i += 1

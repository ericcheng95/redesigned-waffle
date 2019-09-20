"""Download replays from the CEA Replay Repository.
Saves records of which links have been downloaded in data/ folder.
Usage: python download_replays.py
If you want to redownload all replays,
  python download_replays.py --r True

And pip install whatever packages you need.

TODO: combine this into one script with replay_organizer.py.
Also TODO: Write a setup file so that people don't have to pip install everything.
"""
import argparse
import requests
import shutil
import json
from consts import CURRENT_SEASON_NAME, ID_DICT_JSON, URL, CURRENT_SEASON
from drive_downloader import GoogleDriveDownloader as gdd
from bs4 import BeautifulSoup, Tag

# Directory where uploaded replays are stored.
replay_directory = "UploadHere/"# + CURRENT_SEASON + "/"

def update_json(id_dict):
  """Updates the json file which checks which files have been downloaded.

  Args:
      id_dict (DICT): Dictionary with url ID as key, 1 as value
  """
  j = json.dumps(id_dict)
  f = open(ID_DICT_JSON, 'w')
  print(j, file=f)
  f.close()


def download_replays(redownload):
  if (redownload):
    shutil.rmtree(replay_directory)
    # clear out the replay folder, redownload.
  response = requests.get(URL)
  response.encoding = 'utf-8'
  soup = BeautifulSoup(response.text, 'html.parser')

  try:
    with open(ID_DICT_JSON, 'r') as f:
      id_dict = json.load(f)
  except:
    print("Could not open %s" % ID_DICT_JSON)
    id_dict = {}
  # Use an empty dict if redownloading all replays
  if redownload:
    id_dict = {}

  count = 0
  for t in soup.find_all(text=CURRENT_SEASON_NAME):
    for item in t.parent.find_next_siblings("h4"):
      if isinstance(item, Tag):
        # Break upon reaching a tag that's not a link
        # (presumably 'Starcraft 2 Spring 2019').
        if 'class' in item.attrs:
          print("End of the line")
          break
        count += 1
        drive_id = item.a.get('href').split("=")[-1]
        print(drive_id)
        if drive_id not in id_dict:
          id_dict[drive_id] = 1
          gdd.download_file_from_google_drive(
              file_id=drive_id, dest_path=replay_directory
              + "temp_dir" + '.zip', new_file_name=str(count) + " ",
              unzip=True)
  update_json(id_dict)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description='Download Replays from CEA Replay Repository')
  parser.add_argument('--r', type=bool, dest='redownload', default=False,
                      help='True/False: Whether to redownload all replays')
  args = parser.parse_args()
  download_replays(args.redownload)

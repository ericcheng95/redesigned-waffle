"""Constants to be used for the current season. Not sure how coding in python
works, but this is essentially the setup file. Currently it has some unused variables,
and is only being used by download_replays.py.

Attributes:
    CURRENT_SEASON (str): Current season; At the start of a new CEA season
    					  rename this to something new, like SeasonFall2020.
    REPLAY_DIRECTORY (str): Directory where replays are to be stored.
    TEAMS_FILE (str): Teams file for the current season. Create the csv in the
    				  season folder.
    CURRENT_SEASON_NAME (str): Current season name. Must match replay vault.
    ID_DICT_JSON (str): Dictionary containing info on which replays have
    					already been downloaded.
    URL (str): URL of the replay vault.
"""

# Current season; At the start of a new CEA season, rename this to something
# new, whether it be Season [N=1] or Fall2020.
CURRENT_SEASON = "Fall2019"

# CSV containing Team->Player information.
TEAMS_FILE = "cea_names.csv"

# Used in download_replays.py to download replays from the replay vault. This is equal to whatever's in the header: i.e
# https://i.imgur.com/pXfIrNs.png : "Starcraft 2 Fall 2019", case sensitive.
CURRENT_SEASON_NAME = "Starcraft 2 Fall 2019"
ID_DICT_JSON = "data/" + CURRENT_SEASON + "_id_dict.json"
URL = 'https://cea.gg/pages/replay-vault'
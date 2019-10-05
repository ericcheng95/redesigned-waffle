# redesigned-waffle
Revolutionizing the new Waffle.

# How to use the revolutionary waffle
1. Clone the repo somewhere onto your computer.
2. Install the dependencies.
```
pip install -r requirements.txt 
```

## To download replays from the replay repo.
```
python download_replays.py
```
The replay organizer only downloads replays it hasn't seen before. To (re)download all replays for the season, use:
```
python download_replays.py --r true
```

## To organize replays into the team folders.
```
python replay_organizer.py
```
There'll be some errors due to a few broken SC2 Replay files, but you can ignore that.

Errors may pop up due to a missing map definition or a missing team name corresponding to a player.
In the event of a missing map definition, update map_dictionary in replay_organizer.py.
In the event of a missing team name, update cea_names.csv by adding the player name to their corresponding team.

## To generate a stats spreadsheet for the season.
```
python stats_compiler.py
```

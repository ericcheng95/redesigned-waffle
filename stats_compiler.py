"""Compiles a CSV with detailed stats on the league.

Attributes:
    REPLAY_DIRECTORY (str): Directory where replays are stored.
"""
import mpyq
import string
import os
import re
import traceback
import json
import csv
import cea_team_name_parser
from consts import TEAMS_FILE
from s2protocol import versions
from collections import Counter

REPLAY_DIRECTORY = "UploadHere/"


class PlayerObject:

  """Contains player statistics.

  Attributes:
      games (GameObject): Struct to store information that we want from a game
      losses (int): Number of losses.
      mmr (int): Maximum mmr of the player. Reports 0 when player is unranked
                 or something went wrong.
      name (str): Name of the player.
      wins (int): Number of wins.
  """

  def __init__(self, name, wins, games):
    self.name = name
    self.wins = wins
    self.games = games

  losses = property(fget=lambda self: len(self.games) - self.wins)
  mmr = property(fget=lambda self: max(game.mmr for game in self.games))

  @property
  def race(self):
    race_counter = Counter([game.race for game in self.games])
    return race_counter.most_common(1)[0][0]

  @property
  def opponents_beaten(self):
    return [game.opponent for game in self.games if game.win]

  @property
  def opponents_lost_to(self):
    return [game.opponent for game in self.games if not game.win]

  @property
  def apm(self):
    apms = [game.apm for game in self.games]
    return sum(apms) / len(apms)


class GameObject:

  """ Struct containing information about a game, given 1 player.

  Attributes:
      duration (int): Length of the game in seconds
      opponent (str): Name of the opponent
      race (str): Selected race
  """

  def __init__(self, opponent, race, win, mmr, apm, duration):
    self.opponent = opponent
    self.race = race
    self.win = win
    self.mmr = mmr
    self.apm = apm
    self.duration = duration


def erase_punctuation(player_name):
  """Player names can come in the form of
    b'&lt;AMZN&gt;<sp/>Feniks'
    so we remove all punctuation and everything
    to the left of it, to remove b' and the tag   
  Args:
      player_name (String): full name of player

  Returns:
      string: name of player, without tag or punctuation
  """
  player_name = player_name.decode('UTF-8')
  return player_name.split('>', 1)[-1]


def race_winrate(directory):
  # Using mypq, load the replay file
  matcher = re.compile(r'\.SC2Replay$', re.IGNORECASE)
  replays = [file for file in os.listdir(directory) if matcher.search(file)]
  print("Found %d replays to scan" % len(replays))

  # KEY: Name. VALUE: PlayerObject
  race_dictionary = {
      "Protoss": "P", "Zerg": "Z", "Terran": "T",
      "异虫": "Z", "星灵": "P", "人类": "T"}
  matchup_dictionary = {"PvZ": 0, "PvT": 0, "ZvT": 0}
  for replay in replays:
    try:
      # necessary stuff from s2protocol
      archive = mpyq.MPQArchive(os.path.join(directory, replay))
      contents = archive.header['user_data_header']['content']
      header = versions.latest().decode_replay_header(contents)
      base_build = header['m_version']['m_baseBuild']
      protocol = versions.build(base_build)

      # get the general info about the replay
      contents = archive.read_file('replay.details')
      result = protocol.decode_replay_details(contents)

      player_list = result['m_playerList']
      # player result is 1 if won, 2 if not.
      player_result = [player_list[0]['m_result'] == 1,
                       player_list[1]['m_result'] == 1]

      # ex: [P, Z]
      player_races = [player_list[0]['m_race'].decode('UTF-8'),
                      player_list[1]['m_race'].decode('UTF-8')]
      player_races = [race_dictionary[race] for race in player_races]
    except:
      print("error")


def get_metadata_key(metadata_json, value, i):
  """Get the value for a specific key from the player metadata.
  The metadata contains values for each player, 0 for player 1,
  1 for player 2.

  Args:
      metadata_json (JSON): Replay metadata file
      value (str): Value to retrieve from. Ex: 'MMR', 'APM'
      i (int): Which player to retrieve metadata for.

  Returns:
      string: Value stored in file.
  """
  return metadata_json['Players'][i][value] if value in metadata_json['Players'][i] else 0


def get_mmr(nickname_dict, mmr_exceptions, opponent):
  opp_nickname = nickname_dict[opponent.name.lower()]
  if opp_nickname in mmr_exceptions:
    return max(mmr_exceptions[opp_nickname], opponent.mmr)
  else:
    return opponent.mmr


def compile_stats(directory, nicknames_dict):
  # Using mypq, load the replay file
  matcher = re.compile(r'\.SC2Replay$', re.IGNORECASE)
  replays = [file for file in os.listdir(directory) if matcher.search(file)]
  print("Found %d replays to scan" % len(replays))

  # KEY: Name. VALUE: PlayerObject
  player_dictionary = {}

  race_dictionary = {
      "Protoss": "P", "Zerg": "Zerg", "Terran": "T", "Rand": "Random",
      "Prot": "Protoss", "Terr": "Terran",
      "异虫": "Z", "星灵": "P", "人类": "T"}

  # Manual MMR overrides. Insert new entries if you want to manually override a player's MMR.
  # ex: { "You" : 6700 }
  mmr_exceptions = {}
  for replay in replays:
    try:
      # necessary stuff from s2protocol
      archive = mpyq.MPQArchive(os.path.join(directory, replay))
      contents = archive.header['user_data_header']['content']
      header = versions.latest().decode_replay_header(contents)
      base_build = header['m_version']['m_baseBuild']
      if base_build == 76811:
        protocol = versions.build(76114)
      else:
        protocol = versions.build(base_build)

      # get the general info about the replay
      contents = archive.read_file('replay.details')
      result = protocol.decode_replay_details(contents)
      player_list = result['m_playerList']

      # get the metadata info about the replay
      metadata_contents = archive.read_file('replay.gamemetadata.json')
      metadata_json = json.loads(metadata_contents.decode('utf-8'))

      # Get MMR, APM for each player
      player_mmr = [get_metadata_key(
          metadata_json, 'MMR', 0), get_metadata_key(metadata_json, 'MMR', 1)]
      player_apm = [get_metadata_key(
          metadata_json, 'APM', 0), get_metadata_key(metadata_json, 'APM', 1)]

      # ex: ["P". "Z"]
      player_races = [get_metadata_key(metadata_json, 'SelectedRace', 0), get_metadata_key(
          metadata_json, 'SelectedRace', 1)]
      player_races = [race_dictionary[race] for race in player_races]

      # string array with 2 player names, i.e [Feniks, DarthNoob]
      player_names = [erase_punctuation(player_list[0]['m_name']),
                      erase_punctuation(player_list[1]['m_name'])]

      # player result is 1 if won, 2 if not.
      player_result = [player_list[0]['m_result'] == 1,
                       player_list[1]['m_result'] == 1]

      # record whether this player won
      for i in [0, 1]:
        player_name = player_names[i]
        game_object = GameObject(opponent=player_names[1 - i], race=player_races[i], win=player_result[i],
                                 mmr=player_mmr[i], apm=player_apm[i], duration=metadata_json['Duration'])
        if player_name in mmr_exceptions:
          game_object.mmr = max(game_object.mmr, mmr_exceptions[player_name])
        if player_name.lower() in nicknames_dict:
          player_name = nicknames_dict[player_name.lower()]
        if player_name in player_dictionary:
          player_dictionary[player_name].games.append(game_object)
          player_dictionary[player_name].wins += player_result[i]
        else:
          player_dictionary[player_name] = PlayerObject(
              player_name, player_result[i], [game_object])
    except:
      print("Error processing replay: %s" % replay)
      traceback.print_exc()

  return player_dictionary


def print_dictionary(player_dictionary):
  # sorted by number of wins, then by winrate
  num_columns = 2
  teams_dict, blah = cea_team_name_parser.init_dictionary(TEAMS_FILE)
  sorted_player_dict = sorted(player_dictionary.items(), key=lambda item: (  # teams_dict[item[1].name.lower()],
      item[1].wins - item[1].losses, len(item[1].games),  -1 * (len(item[1].games) - item[1].wins)))
  for i in range(len(sorted_player_dict)):
    key = sorted_player_dict[i][0]
    value = sorted_player_dict[i][1]
    print("%d : %d %s %s" % (value.wins, value.losses,
                             teams_dict[value.name.lower()] + " " + value.name, value.race))


def make_csv(player_dictionary):
  teams_dict, nickname_dict = cea_team_name_parser.init_dictionary(TEAMS_FILE)
  csv_arr = []
  headers_arr = ["Team Name", "Name", "Wins", "Losses", "MMR", "Race", "APM",
                 "Biggest Win (MMR Diff)", "Biggest Loss (MMR Diff)", "Players Defeated (MMR Diff)", "Players Lost To (MMR Diff)"]
  with open("cea_season_stats.csv", "w", newline='') as my_csv:
    csvWriter = csv.writer(my_csv, delimiter=',')
    csvWriter.writerow(headers_arr)
    for key, value in player_dictionary.items():
      new_entry = []
      # Name
      new_entry.append(teams_dict[value.name.lower()])
      new_entry.append(value.name)

      # Wins
      new_entry.append(int(value.wins))

      # Losses
      new_entry.append(int(value.losses))

      # Rank
      new_entry.append(value.mmr)
      # Race
      new_entry.append(value.race)
      # APM
      new_entry.append(int(value.apm))

      # Retrieve list of opponents beaten / lost to, with MMR differential.
      def opponent_func(opponents_list, descending):
        new_opponents_list = [opp_nickname for opp_nickname in opponents_list]
        new_opponents_list = sorted(new_opponents_list, key=lambda item: (
            player_dictionary[nickname_dict[item.lower()]].mmr), reverse=descending)
        new_opponents_list = [opponent + " ({:+})".format(
            player_dictionary[nickname_dict[opponent.lower()]].mmr - value.mmr) for opponent in new_opponents_list]
        return new_opponents_list

      opponents_beaten = opponent_func(value.opponents_beaten, True)
      opponents_lost_to = opponent_func(value.opponents_lost_to, False)

      # Biggest win
      new_entry.append("" if not opponents_beaten else opponents_beaten[0])

      # Biggest loss
      new_entry.append("" if not opponents_lost_to else opponents_lost_to[0])

      # Opponents beaten / lost to
      new_entry.append(" ; ".join(opponents_beaten))
      new_entry.append(" ; ".join(opponents_lost_to))

      csvWriter.writerow(new_entry)
      csv_arr.append(new_entry)
  print("Done creating CSV");


def print_names(teams_dictionary):
  for key, value in teams_dictionary.items():
    print(key)


if __name__ == "__main__":
  teams_dict, nicknames_dict = cea_team_name_parser.init_dictionary(TEAMS_FILE)
  print(nicknames_dict)
  player_dictionary = compile_stats(REPLAY_DIRECTORY, nicknames_dict)
  make_csv(player_dictionary)

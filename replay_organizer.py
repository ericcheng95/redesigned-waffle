import mpyq
import os
import re
import string
import shutil
import traceback
from s2protocol import versions
from datetime import datetime
from datetime import timedelta
from collections import Counter
from consts import STARTING_DATE

import cea_team_name_parser

REPLAY_DIRECTORY = "UploadHere/"
TEAMS_FILE = "cea_names.csv"
UNKNOWN_TEAM = "TEAM_NOT_KNOWN"

counts = Counter()

def define_cea_date_ranges():
  """Starts with preseason, March 16 2019 12:00.

  Returns:
      Array: Array containing the dates of each CEA week
  """
  num_weeks = 14
  weeks = []

  weeks.append(datetime.strptime(STARTING_DATE+"12",'%Y%m%d%H'))
  d = timedelta(days=7)
  for i in range(1,num_weeks):
    weeks.append(weeks[0] + d * i)
  return weeks

def get_date_played(weeks, date_of_game):
  """Calculates the week the game was played, given the date of the replay
  
  Args:
      weeks (Array[datetime]): dates of CEA weeks
      date_of_game (datetime): date replay was played
  
  Returns:
      String: week game was played
  """
  weeks = [abs(week - date_of_game) for week in weeks]
  min_index = weeks.index(min(weeks))
  rounds = ['Round1', 'GapWeek', 'Round2', 'Round3', 'Round4', 'Round5']
  if min_index == 0:
    return 'Preseason'
  elif min_index < 9:
    return 'Week' + str(min_index)
  else:
    return rounds[min_index - 9]

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

def get_time(utc_timestamp):
  """Gets date given UTC timestamp of game
  
  Args:
      utc_timestamp (int): UTC timestamp of game
  Returns:
      datetime
  """
  real_timestamp = utc_timestamp / (10 * 1000 * 1000) - 11644473600
  real_timestamp -= 60 * 60 * 7;
  utc = datetime.utcfromtimestamp(real_timestamp)
  return utc

def find_team(teams, name):
  """tries to find the team for a player
  if it can't be determined, returns UNKNOWN_TEAM
  
  Args:
      teams (dict): dict with key = player, value = team
      name (string): name of player to find
  """
  if name.lower() in teams:
    return teams[name.lower()]
  else:
    return UNKNOWN_TEAM

def identify_unknown_players(matchup_dictionary, team_dictionary):
  """ Identifies unknown players in the teams file. If a player whose team is
  known matches up against a player whose team is unknown, then we can obtain
  the unknown player's team by checking the team matchups.
  Prints out potential errors (instances in which a team faced multiple
  opponents)
  and suggests the proper team for players whose team is unknown.
  
  Args:
      matchup_dictionary (dict): dict with key = Week played, value =
        dict<string,list> of key = team, and value = opponents played that week
      team_dictionary (dict): dict with key = player, value = team
  """
  for week in matchup_dictionary.keys():
    for team, opponents in matchup_dictionary[week].items():
      if team == UNKNOWN_TEAM:
        continue
      opponent_teams = [find_team(teams,opponent) for opponent in set(opponents)]
      team_counter = Counter(opponent_teams)

      # If the team faced more than 2 opponents, that's not supposed to happen.
      if len(team_counter) >= 2 + int(UNKNOWN_TEAM in team_counter):
        print("Potential error in teams file: In {0}, {1} faced multiple teams:".format(week,team))
        print('Players: ', *["{0} {1}".format(find_team(teams, i), i) for i in set(opponents)], sep='\n\t')
      # If the team faced 2 opponents, and one was UNKNOWN_TEAM, then we know what team they faced.
      elif UNKNOWN_TEAM in team_counter and len(team_counter) == 2:
        # Get the team that is not UNKNOWN_TEAM: everyone belongs to that team.
        opponent_team = next(team for team in opponent_teams if team != UNKNOWN_TEAM )
        for opponent in set(opponents):
          if find_team(teams, opponent) == UNKNOWN_TEAM:
            print("Suggested team for {0}: {1};\n \t {2} faced {3} in {4}".format(opponent, opponent_team, opponent_team, team, week))
      

def copy_into_path(original, copyname, path):
  """copies into a new location, making the folders if necessary and stops if the file's already there
  
  Args:
      original (string): the file to copy
      copyname (string): the filename to use for the new location
      path (list of string): parts of the path at which to put the copy
  """
  path = os.path.join(*path).replace(" ", "_")
  os.makedirs(path, exist_ok=True) # makes the directories if necessary
  path = os.path.join(path, copyname.replace(" ", "_") + ".SC2Replay")
  if not os.path.isfile(path):
    counts['replay copies organized'] += 1
    shutil.copyfile(original, path)
  else:
    counts['replay copies already existed'] += 1
    
def organize_replays(directory, output_directory, teams, aliases):
  """copies replays to another directory with standardized format
  
  Args:
      directory (string): replay directory
      output_directory (string): new replay directory
      teams (dict): dict with key = player, value = team
  """
  # Using mypq, load the replay file
  matcher = re.compile(r'\.SC2Replay$', re.IGNORECASE)
  replays = [file for file in os.listdir(directory) if matcher.search(file)]
  print("Found %d replays to scan" % len(replays))

  #The dates corresponding to each week
  week_time = define_cea_date_ranges()  
  race_dictionary = {
    "Protoss" : "P" , "Zerg" : "Z", "Terran" : "T",
    "异虫" : "Z", "星灵" : "P", "人类" : "T"}
  map_dictionary = {
    "Automaton LE" : "Automaton LE",
    "机械城  天梯版" : "Automaton LE",
    "Kings Cove LE" : "Kings Cove LE",
    "国王藏宝地天梯版" : "Kings Cove LE",
    "Year Zero LE" : "Year Zero LE",
    "New Repugnancy LE" : "New Repugnancy LE",
    "Cyber Forest LE" : "Cyber Forest LE",
    "赛博森林天梯版" : "Cyber Forest LE",
    "Port Aleksander LE" : "Port Aleksander LE",
    "Kairos Junction LE" : "Kairos Junction LE",
    "Acropolis LE" : "Acropolis LE",
    "Thunderbird LE" : "Thunderbird LE",
    "Turbo Cruise 84 LE" : "Turbo Cruise 84 LE",
    "Triton LE" : "Triton LE",
    "Disco Bloodbath LE" : "Disco Bloodbath LE",
    "Winters Gate LE" :  "Winters Gate LE",
    "Ephemeron LE" : "Ephemeron LE",
    "World of Sleepers LE" : "World of Sleepers LE",
  }

  # Windows has to close the file before moving them, so
  # files must be stored in a dictionary.
  renamed_files = {}

  # 2 dimensional dictionary that stores matchups per week.
  # KEY 1: Week, VALUE 1: Dictionary<string,list>
  # ex: matchup_dictionary['Week1']['Microsoft Macrohard']
  matchup_dictionary = {}

  for replay in replays:
    try:
      # necessary stuff from s2protocol
      archive = mpyq.MPQArchive(os.path.join(directory,replay))
      contents = archive.header['user_data_header']['content']
      header = versions.latest().decode_replay_header(contents)
      base_build = header['m_version']['m_baseBuild']
      # Build 76114 was never added to s2protocol.
      if base_build == 76811:
        protocol = versions.build(76114)
      else:
        protocol = versions.build(base_build)
      
      # get the general info about the replay
      contents = archive.read_file('replay.details')
      result = protocol.decode_replay_details(contents)
      player_list = result['m_playerList']
      
      # string array with 2 player names, i.e [Feniks, DarthNoob]
      player_names = [erase_punctuation(player_list[0]['m_name']),
                      erase_punctuation(player_list[1]['m_name'])]
      
      # resolve aliases for players who play under several accounts
      for i in range(len(player_names)):
        if player_names[i].lower() in aliases:
            player_names[i] = aliases[player_names[i].lower()]
      
      # ex: [P, Z]
      player_races = [player_list[0]['m_race'].decode('UTF-8'),
                      player_list[1]['m_race'].decode('UTF-8')]
      player_races = [race_dictionary[race] for race in player_races]
      
      # ex: [Alexa 12 Pool, Google Noobernetes]
      player_teams = [find_team(teams, player_names[0]), find_team(teams, player_names[1])]
      
      # Keep naming consistent by always putting players alphabetized by team
      if player_teams[1] < player_teams[0]:
        player_races = [player_races[1], player_races[0]]
        player_names = [player_names[1], player_names[0]]
        player_teams = [player_teams[1], player_teams[0]]

      # ex: Week4
      replay_time = result['m_timeUTC']
      week_played = get_date_played(week_time, get_time(replay_time))

      # Updates the Matchup Dictionary
      if week_played not in matchup_dictionary:
        matchup_dictionary[week_played] = {}
      matchup_dictionary[week_played].setdefault(player_teams[0], []).append(player_names[1])
      matchup_dictionary[week_played].setdefault(player_teams[1], []).append(player_names[0])

      # ex: Kings Cove LE
      map_name = result['m_title'].decode('UTF-8').translate(
                 str.maketrans('', '', string.punctuation))

      # In case map name is not in English.
      if not map_name.replace(" ","").isalnum() and map_name not in map_dictionary:
        print("Map name %s not recognized" % map_name)
        print("\t%s, %s" % (week_played, map_name))
        print("\t%s: %s (%s)" % (player_teams[0], player_names[0], player_races[0]))
        print("\t%s: %s (%s)" % (player_teams[1], player_names[1], player_races[1]))
        continue
      elif map_name in map_dictionary:
        map_name = map_dictionary[map_name]
      
      src = os.path.join(directory, replay)
      
      # don't continue for unknown players so they can be fixed
      if UNKNOWN_TEAM in player_teams:
        print("Couldn't find the team for one of the players. Here's what we know:")
        print("\t%s, %s" % (week_played, map_name))
        print("\t%s: %s (%s)" % (player_teams[0], player_names[0], player_races[0]))
        print("\t%s: %s (%s)" % (player_teams[1], player_names[1], player_races[1]))
        continue
      
      # copy into team/player/matchup folders
      copy_into_path(src, 
          "-".join([player_teams[1], player_names[1], map_name, week_played]),
          [player_teams[0], "%s (%s)" % (player_names[0], player_races[0]), "vs " + player_races[1]])
      copy_into_path(src,
          "-".join([player_teams[0], player_names[0], map_name, week_played]),
          [player_teams[1], "%s (%s)" % (player_names[1], player_races[1]), "vs " + player_races[0]])
          
      # rename the original to avoid name conflicts and make it clear what's been processed
      to_rename = "-".join([
        week_played,
        player_teams[0], player_teams[1],
        player_names[0], player_names[1],
        player_races[0], player_races[1],
        map_name]).replace(" ","_") + ".SC2Replay"
      dst = os.path.join(output_directory, to_rename)
      if src.lower() != dst.lower():
        counts['replays processed'] += 1
        os.makedirs(output_directory, exist_ok=True)
        renamed_files[src] = dst
      else:
        counts['replays were already processed'] += 1
    except:
      print("Error processing replay: %s" % replay)
      traceback.print_exc()
  for key, value in renamed_files.items():
      shutil.move(key, value)

  for count_name, count in sorted(counts.items()):
    print(count, count_name)

  # Identify players who are not recognized
  identify_unknown_players(matchup_dictionary, teams)

if __name__ == "__main__":
  teams, aliases = cea_team_name_parser.init_dictionary(TEAMS_FILE)
  organize_replays(REPLAY_DIRECTORY, REPLAY_DIRECTORY, teams, aliases)


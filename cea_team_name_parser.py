import csv

def init_dictionary(filename):
  """Initializes dictionary with key player name, value team name,
     given a CSV of teams and players.
  Args:
      filename (string): CSV with team name in 1st column, players in rest of the columns
  Returns a tuple of:
      team (dict): player name => team name
      players (dict): player alias => main player name
  """
  teams = {}
  players = {}
  with open(filename, mode='r', encoding="utf-8-sig") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=",")
    for row in csv_reader:
      team_name = row[0]
      for member in row[1:]:
        aliases = member.split('=')
        for alias in aliases:
            # we convert to lowercase to make string comparison easier.
            teams[alias.lower()] = team_name
            players[alias.lower()] = aliases[0]
  return (teams, players)
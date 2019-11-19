#!/bin/bash

if [[ -z $1 ]]
then
	echo "Provide a team name. For example,"
	echo "    $0 \"Google BetaStars\""
	exit 0
fi

MATCHES=$(ls)
for FILTER in "$@"
do
	MATCHES=$(echo "$MATCHES" | grep "$FILTER" -i)
done

NUM_MATCHES=$(echo "$MATCHES" | wc -l)
if [[ $NUM_MATCHES -eq 0 ]]
then
	echo "No teams were matches by those filters."
	exit 0
fi
if [[ $NUM_MATCHES -gt 1 ]]
then
	echo "Multiple teams matched:"
	echo "$MATCHES"
	exit 0
fi

TEAM="$MATCHES"
REPLAYS=$(find $TEAM | grep '\.sc2replay' -i)

echo ">>Players fielded each week:"
for WEEK in Preseason Week1 Week2 Week3 Week4 Week5 Week6 Week7 Week8 Round1 Round2 Round3 Round4
do
	echo ""
	echo "$WEEK"
	for PLAYER in $(echo "$REPLAYS" | grep "$WEEK" | cut -d/ -f2)
	do
		echo "    $PLAYER"
	done
done

echo ""
echo ">>Players fielded on each map:"
for MAP in "Kairos_Junction" "New_Repugnancy" "Port_Aleksander" "Automaton" "Year_Zero" "Cyber_Forest" "Kings_Cove" "Ephemeron" "Triton" "World of Sleepers" "Thunderbird" "Disco Bloodbath" "Acropolis" "Winters Gate"
do
	echo ""
	echo "$MAP" | sed 's/_/ /'
	echo "$REPLAYS" | grep "$MAP" | cut -d/ -f4,2 | sed -E 's/^(.*)\/[^\.]*-([^\-]*)\..*/\t\2\t\1/' | sort
done

#!/bin/sh

wget --quiet https://oldschool.runescape.wiki/w/Trailblazer_Reloaded_League/Tasks
mv Tasks tasks.unformatted
grep "data-taskid" tasks.unformatted -A 4 | grep -v href | grep -v "/" > tasks.formatted

wget --quiet https://sync.runescape.wiki/runelite/player/OlliWolli/TRAILBLAZER_RELOADED_LEAGUE
mv TRAILBLAZER_RELOADED_LEAGUE olliwolli.json

wget --quiet https://sync.runescape.wiki/runelite/player/LinkWitz/TRAILBLAZER_RELOADED_LEAGUE
mv TRAILBLAZER_RELOADED_LEAGUE linkwitz.json

python3 trailblazer_compare.py


#!/bin/sh

set -e

wget --quiet https://oldschool.runescape.wiki/w/Raging_Echoes_League/Tasks
mv Tasks tasks.unformatted
grep "data-taskid" tasks.unformatted -A 4 | grep -v href | grep -v "/" > tasks.formatted

wget --quiet https://sync.runescape.wiki/runelite/player/OlliWolli/RAGING_ECHOES_LEAGUE || echo "Failed to download OlliWolli JSON" >&2
mv RAGING_ECHOES_LEAGUE olliwolli.json

wget --quiet https://sync.runescape.wiki/runelite/player/LinkWitz/RAGING_ECHOES_LEAGUE || echo "Failed to download LinkWitz JSON" >&2
mv RAGING_ECHOES_LEAGUE linkwitz.json

python3 trailblazer_compare.py

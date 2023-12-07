import json
from pathlib import Path

linkwitz = json.loads(Path("linkwitz.json").read_text())
olliwolli = json.loads(Path("olliwolli.json").read_text())

tasks = Path("tasks.formatted").read_text().splitlines()

taskmap = {
    int(tasks[i].split('"')[1]): tasks[i+1][4:]
    for i in range(len(tasks))
    if 'data-taskid="' in tasks[i]
}

olliwolli_tasks = {
    taskmap[tid] for tid in olliwolli["league_tasks"]
}

linkwitz_tasks = {
    taskmap[tid] for tid in linkwitz["league_tasks"]
}

print()
print("Tasks LinkWitz has that OlliWolli doesn't:")
print("==========================================")
for task in sorted(linkwitz_tasks - olliwolli_tasks):
    print(task)

print()
print("Tasks OlliWolli has that LinkWitz doesn't:")
print("==========================================")
for task in sorted(olliwolli_tasks - linkwitz_tasks):
    print(task)

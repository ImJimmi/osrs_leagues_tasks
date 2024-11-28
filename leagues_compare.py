import cfgclasses
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Iterator, Iterable

TASKS_URL = "https://oldschool.runescape.wiki/w/Raging_Echoes_League/Tasks"


def get_user_info_url(username: str) -> str:
    return (
        f"http://sync.runescape.wiki/runelite/player/{username}/RAGING_ECHOES_LEAGUE"
    )

def wget_content(url: str) -> str:
    with tempfile.NamedTemporaryFile("w") as tmpfile:
        subprocess.run(["wget", "--quiet", url, "-O", tmpfile.name], check=True)
        with open(tmpfile.name) as f:
            return f.read()


@dataclass
class Task:
    tid: int
    region: str
    name: str
    desc: str
    points: int

    @staticmethod
    def load_from_txt(txt: str) -> Iterator["Task"]:
        html_lines = txt.splitlines()
        while html_lines:
            line = html_lines.pop(0)
            if "data-taskid" in line:
                # Start of a task, read the required information
                parts = line.strip("<>").split()
                tid_part = [p for p in parts if p.startswith("data-taskid=")][0]
                reg_part = [p for p in parts if p.startswith("data-tbz-area-for-filtering=")][0]
                tid = int(tid_part.removeprefix("data-taskid=").strip('"'))
                region = (
                    reg_part.removeprefix("data-tbz-area-for-filtering=").strip('"')
                )

                # Drop the next two lines
                html_lines = html_lines[2:]

                # Read the name
                name = html_lines.pop(0).removeprefix("<td>")

                # Drop a line
                html_lines = html_lines[1:]

                # Read the description
                desc = html_lines.pop(0).removeprefix("<td>")

                # Drop a few lines (ignoring the requirements section for now)
                html_lines = html_lines[3:]

                # Read the points the task is worth
                points = int(html_lines.pop(0).split()[-1])

                yield Task(tid, region, name, desc, points)

    @staticmethod
    def to_dict(lst: Iterable["Task"]) -> dict[int, "Task"]:
        return {task.tid: task for task in lst}


@dataclass
class UserData:
    username: str
    levels: dict[str, int]
    combat_achieves: set[int]
    league_tasks: set[int]

    @staticmethod
    def get(username: str) -> "UserData":
        url = get_user_info_url(username)
        content = wget_content(url)
        data = json.loads(content)
        return UserData(
            data["username"],
            data["levels"],
            set(data["combat_achievements"]),
            set(data["league_tasks"]),
        )


@dataclass
class Config:
    regions: list[str] = cfgclasses.arg(
        "Regions to consider tasks for. "
        "Defaults to the starting regions and global.",
        default_factory=lambda: ["misthalin", "general", "karamja"],
    )
    user1: str = cfgclasses.arg(
        "First user to compare. Defaults to OlliWolli.",
        default="OlliWolli",
    )
    user2: str = cfgclasses.arg(
        "Second user to compare. Defaults to LinkWitz.",
        default="LinkWitz",
    )

    def run(self) -> None:
        content = wget_content(TASKS_URL)
        tasks = Task.to_dict(Task.load_from_txt(content))
        userdat1 = UserData.get(self.user1)
        userdat2 = UserData.get(self.user2)

        user1_score = sum(tasks[tid].points for tid in userdat1.league_tasks)
        user2_score = sum(tasks[tid].points for tid in userdat2.league_tasks)

        print(f"{userdat1.username} has {user1_score} points vs {userdat2.username} who has {user2_score}")
        print()

        user1_uniques = userdat1.league_tasks - userdat2.league_tasks
        user1_uniq_points = sum(tasks[tid].points for tid in user1_uniques)
        user2_uniques = userdat2.league_tasks - userdat1.league_tasks
        user2_uniq_points = sum(tasks[tid].points for tid in user2_uniques)


        header1=f"Tasks {userdat1.username} has that {userdat2.username} doesn't for a sum of {user1_uniq_points} points:"
        print(header1)
        print("=" * len(header1))
        lines = [
            f"({tasks[tid].points:3d}) {tasks[tid].name}"
            for tid in user1_uniques
            if tasks[tid].region in self.regions or self.regions == ["all"]
        ]
        for line in sorted(lines):
            print(line)
        print()

        header2=f"Tasks {userdat2.username} has that {userdat1.username} doesn't for a sum of {user2_uniq_points} points:"
        print(header2)
        print("=" * len(header2))
        lines = [
            f"({tasks[tid].points:3d}) {tasks[tid].name}"
            for tid in user2_uniques
            if tasks[tid].region in self.regions or self.regions == ["all"]
        ]
        for line in sorted(lines):
            print(line)
        print()

if __name__ == "__main__":
    cfg = cfgclasses.parse_args(Config, sys.argv[1:], "get_task_list")
    cfg.run()

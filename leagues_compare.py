import cfgclasses
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Iterable

TASKS_URL = "https://oldschool.runescape.wiki/w/Raging_Echoes_League/Tasks"


def get_user_info_url(username: str) -> str:
    return f"http://sync.runescape.wiki/runelite/player/{username}/RAGING_ECHOES_LEAGUE"


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
                reg_part = [
                    p for p in parts if p.startswith("data-tbz-area-for-filtering=")
                ][0]
                tid = int(tid_part.removeprefix("data-taskid=").strip('"'))
                region = reg_part.removeprefix("data-tbz-area-for-filtering=").strip(
                    '"'
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


class CompareMode(Enum):
    TASKS = "tasks"
    SKILLS = "skills"


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

    def task_score(self, tasks: dict[int, Task]) -> int:
        return sum(tasks[tid].points for tid in self.league_tasks)


@dataclass
class Config:
    mode: CompareMode = cfgclasses.arg(
        "Compare mode to use.",
        choices=[m.value for m in CompareMode],
        default=CompareMode.TASKS.value,
        transform=CompareMode,
        transform_type=str,
    )
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

    def user_task_compare(
        self, tasks: dict[int, Task], userdataA: UserData, userdataB: UserData
    ) -> None:
        uniques = userdataA.league_tasks - userdataB.league_tasks
        uniq_points = sum(tasks[tid].points for tid in uniques)

        header = f"Tasks {userdataA.username} has that {userdataB.username} doesn't for a sum of {uniq_points} points:"
        print(header)
        print("=" * len(header))
        lines = [
            f"({tasks[tid].points:3d}) {tasks[tid].name}"
            for tid in uniques
            if tasks[tid].region in self.regions or self.regions == ["all"]
        ]
        for line in sorted(lines):
            print(line)
        print()

    def run_task_compare(self, userdat1: UserData, userdat2: UserData) -> None:
        content = wget_content(TASKS_URL)
        tasks = Task.to_dict(Task.load_from_txt(content))

        print(
            f"{userdat1.username} has {userdat1.task_score(tasks)} points vs {userdat2.username} who has {userdat2.task_score(tasks)}"
        )
        print()

        self.user_task_compare(tasks, userdat1, userdat2)
        self.user_task_compare(tasks, userdat2, userdat1)

    def run_skills_compare(self, userdat1: UserData, userdat2: UserData) -> None:
        header = ("", userdat1.username, userdat2.username)
        footer = (
            "TOTAL",
            str(sum(userdat1.levels.values())),
            str(sum(userdat2.levels.values())),
        )
        rows = (
            [header]
            + [
                (x, str(userdat1.levels[x]), str(userdat2.levels[x]))
                for x in sorted(userdat1.levels)
            ]
            + [footer]
        )
        col1_size = max(len(x) for x, _, __ in rows)
        col2_size = max(len(x) for _, x, __ in rows)
        col3_size = max(len(x) for _, __, x in rows)
        for row in rows:
            line = " ".join(
                [
                    row[0] + " " * (col1_size - len(row[0])),
                    "|",
                    " " * (col2_size - len(row[1])) + row[1],
                    "|",
                    " " * (col3_size - len(row[2])) + row[2],
                ]
            )
            print(line)

    def run(self) -> None:
        userdat1 = UserData.get(self.user1)
        userdat2 = UserData.get(self.user2)
        if self.mode == CompareMode.TASKS:
            self.run_task_compare(userdat1, userdat2)
        elif self.mode == CompareMode.SKILLS:
            self.run_skills_compare(userdat1, userdat2)
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")


if __name__ == "__main__":
    cfg = cfgclasses.parse_args(Config, sys.argv[1:], "get_task_list")
    cfg.run()

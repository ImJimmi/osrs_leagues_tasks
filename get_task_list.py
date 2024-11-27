import cfgclasses
import requests
import sys
from dataclasses import dataclass
from typing import Iterator

TASKS_URL = "https://oldschool.runescape.wiki/w/Raging_Echoes_League/Tasks"


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
                tid = int(parts[1].removeprefix("data-taskid=").strip('"'))
                region = (
                    parts[2].removeprefix("data-tbz-area-for-filtering=").strip('"')
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


@dataclass
class Config:
    regions: list[str] = cfgclasses.arg(
        "Regions to support. Defaults to the starting regions and global.",
        default_factory=lambda: ["misthalin", "general", "karamja"],
    )

    def run(self) -> None:
        resp = requests.get(TASKS_URL)
        tasks = Task.load_from_txt(resp.text)
        for task in tasks:
            if task.region not in self.regions:
                continue
            print(task.name, task.points)

if __name__ == '__main__':
    cfg = cfgclasses.parse_args(Config, sys.argv[1:], "get_task_list")
    cfg.run()

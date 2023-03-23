#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
import json
import logging
import pathlib
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from dataclasses import dataclass

import gitlab
import numpy as np
import requests
import requests.adapters
from rich.box import ROUNDED
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress
from rich.table import Table

today = datetime.date.today()

# 计算上一周的日期范围
last_week_start = today - datetime.timedelta(days=today.weekday() + 7)  # 上一周的周一
last_week_end = last_week_start + datetime.timedelta(days=6)  # 上一周的周日

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(show_path=False)],
)

log = logging.getLogger("git")


def int_list(src):
    return list(map(int, src))


def str_list(src):
    return list(map(str, src))


@dataclass
class GitProject:
    client: gitlab.Gitlab
    # table: Table
    progress: Progress
    project_id: int = None
    users: list = None
    filetype: list = None
    branches: list = None

    def __post_init__(self):
        self.project = self.client.projects.get(self.project_id)

    def get_commits(self, branch):
        author_commits = []
        # commits = self.project.commits.list(all=True, ref_name=branch)
        # log.debug(f'since: {last_week_start}, until: {last_week_end}')

        commits = self.project.commits.list(since=last_week_start, until=last_week_end, all=True, ref_name=branch)
        for commit in commits:
            committer_email = commit.committer_email
            title = commit.title
            message = commit.message

            if ('Merge' in message) or ('Merge' in title):
                log.debug('Merge跳过')
                continue
            else:
                for user in self.users:
                    if committer_email.find(user) >= 0:
                        author_commits.append(commit)
        return author_commits

    def get_code(self, commit, ptask):
        log.debug(f'获取提交[{commit.id}]的代码量')
        commit_info = self.project.commits.get(commit.id)
        code = commit_info.stats
        self.progress.update(ptask, advance=1)
        return code

    @staticmethod
    def extract_task_result(task):
        result = task.result()
        return [
            int(result["additions"]),
            int(result["deletions"]),
            int(result["total"])
        ]

    def get_stats_by_branch(self, branch_name):
        log.debug(f'获取工程{self.project.name}分支[{branch_name}]的提交记录')
        author_commits = self.get_commits(branch_name)
        ptask = self.progress.add_task(f"[green]{branch_name}...", total=len(author_commits))
        all_task = []
        with ThreadPoolExecutor(max_workers=32) as pool:
            for commit in author_commits:
                all_task.append(pool.submit(self.get_code, commit, ptask))

            # 主线程等待所有子线程完成
            wait(all_task, return_when=ALL_COMPLETED)
            codes = np.array([self.extract_task_result(task) for task in all_task])
            codes = np.sum(codes, axis=0)

        data = {
            "project_name": self.project.name,
            "branch_name": branch_name,
            "stats": [
                str(len(author_commits)),
                str(codes[0]),
                str(codes[1]),
                str(codes[2]),
                str(codes[0] - codes[1])
            ]
        }
        return data

    def get_stats_data(self):
        data = []
        for branch in self.branches:
            log.debug(f'获取工程{self.project.name}分支[{branch}]的提交记录')
            author_commits = self.get_commits(branch)
            all_task = []
            with ThreadPoolExecutor(max_workers=32) as pool:
                for commit in author_commits:
                    all_task.append(pool.submit(self.get_code, commit))

                # 主线程等待所有子线程完成
                wait(all_task, return_when=ALL_COMPLETED)
                codes = np.array([self.extract_task_result(task) for task in all_task])
                codes = np.sum(codes, axis=0)

            data.append([
                self.project.name,
                branch,
                str(len(author_commits)),
                str(codes[0]),
                str(codes[1]),
                str(codes[2]),
                str(codes[0] - codes[1])
            ])
        return data


class GitStats:
    DEFAULT_CONFIG_FILE = "gitstats.json"
    DEFAULT_POOL_SIZE = 50
    COLUMNS = ['Project Name', 'Branch Name', 'Commit', 'Additions', 'Deletions', 'Total Change', 'Total Additions']

    def __init__(self, config_file=None):
        self.config = self.load_config(config_file)
        self.client = self.get_client()
        self.console = Console()
        self.table = self.get_table()
        self.progress = Progress()

    def load_config(self, config_file):
        filename = config_file if config_file else self.DEFAULT_CONFIG_FILE
        file = pathlib.Path(__file__).resolve().parent / filename
        with file.open("r") as fp:
            conf = json.load(fp)

        return conf

    def get_client(self):
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.DEFAULT_POOL_SIZE,
            pool_maxsize=self.DEFAULT_POOL_SIZE
        )
        session.mount('http://', adapter)
        url = self.config.get("url")
        token = self.config.get("token")
        return gitlab.Gitlab(url, private_token=token, session=session)

    def get_table(self):
        table = Table(title="Gitlab Code Stats", header_style="bold magenta", box=ROUNDED)
        for i, col in enumerate(self.COLUMNS):
            if i >= 2:
                table.add_column(col, justify="right")
            else:
                table.add_column(col)
        return table

    def print(self, data):
        stats = []
        for d in data:
            self.table.add_row(d["project_name"], d["branch_name"], *d["stats"])
            stats.append(int_list(d["stats"]))

        stats_arr = np.array(stats)
        total = list(np.sum(stats_arr, axis=0))
        offset = self.config.get("offset", 0)
        total[-1] += offset
        total = str_list(total)

        self.table.add_section()
        self.table.add_row("", "", *total, style="red bold")

        self.console.print(self.table)

    def run(self):
        self.progress.start()
        data = []
        projects_conf = self.config.get("projects", [])
        for conf in projects_conf:
            project = GitProject(self.client, self.progress, **conf)
            for b in conf["branches"]:
                data.append(project.get_stats_by_branch(b))
        self.progress.stop()
        self.print(data)


def run():
    gs = GitStats()
    gs.run()


if __name__ == "__main__":
    run()

import base64
from github import Github
from dateutil import tz


class git_handler:
    def __init__(self, token):
        self.github = Github(token)

    def get_file_commit_time(self, repo, filename):
        repo = self.github.get_repo(repo)
        commits = repo.get_commits(path=filename)
        modification_time_raw = commits[0].commit.author.date
        modification_time = modification_time_raw.replace(
            tzinfo=tz.tzutc()).astimezone(tz.tzlocal()).strftime("%s")
        return modification_time

    def get_file_content(self, repo, tag, filename):
        repo = self.github.get_repo(repo)
        raw_content = repo.get_file_contents(filename, ref=tag)
        file_content = base64.b64decode(raw_content.content)
        return file_content

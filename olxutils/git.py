from __future__ import unicode_literals

from subprocess import check_call, check_output, CalledProcessError


class GitHelperException(Exception):
    pass


class GitHelper(object):

    BRANCH_FORMAT = "run/%s"

    def __init__(self, run, delete_existing=False):
        self.run = run
        self.branch = self.BRANCH_FORMAT % run
        self.delete_existing = delete_existing
        self.message = ""

    def _git_call(self, args):
        check_call("git %s" % args, shell=True)

    def _git_output(self, args):
        return check_output("git %s" % args, shell=True)

    def create_branch(self):
        if self.is_dirty():
            message = (
                "The working directory contains untracked files "
                "or uncommitted changes.\n"
                "Please commit, stash, or delete them "
                "and try again.\n"
            )
            raise GitHelperException(message.format(self.branch))

        if self.branch_exists():
            if self.delete_existing:
                self.delete_branch()
            else:
                message = (
                    "The target git branch already exists."
                )
                raise GitHelperException(message.format(self.branch))

        try:
            self._git_call("checkout -b {}".format(self.branch))
        except CalledProcessError:
            raise GitHelperException('Error creating '
                                     'branch {}'.format(self.branch))

    def is_dirty(self):
        # If 'git status --porcelain' produces any output, we've
        # got a dirty working directory. If its output is empty,
        # the working directory is clean.
        try:
            if self._git_output("status --porcelain"):
                return True
        except CalledProcessError:
            message = "Unable to run git status"
            raise GitHelperException(message)

        return False

    def branch_exists(self):
        try:
            self._git_call("rev-parse --verify {}".format(self.branch))
        except CalledProcessError:
            return False

        return True

    def delete_branch(self):
        try:
            self._git_call("branch -D {}".format(self.branch))
        except CalledProcessError:
            raise GitHelperException('Error deleting '
                                     'branch {}'.format(self.branch))

    def add_to_branch(self):
        # Git add the changed files and commit them.
        try:
            self._git_call("add .")
            self._git_call("commit -m 'New run: {}'".format(self.run))
        except CalledProcessError:
            raise GitHelperException('Error committing new run.')
        self.message = (
            "\n"
            "To push this new branch upstream, run:\n"
            "\n"
            "$ git push -u origin {}\n"
            "\n"
            "To switch back to master, run:\n"
            "\n"
            "$ git checkout master\n"
        ).format(self.branch)

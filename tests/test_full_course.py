from __future__ import unicode_literals

import os
import tempfile

import shutil
import shlex

from subprocess import check_call, CalledProcessError

from olxutils.cli import CLI, CLIException

import git

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from unittest import TestCase


class FullCourseTestCase(TestCase):
    """
    Render a full course and compare its results to expectations
    """

    SOURCE_DIR = os.path.join(os.path.dirname(__file__),
                              'course',
                              'source')
    RESULT_DIR = os.path.join(os.path.dirname(__file__),
                              'course',
                              'result')

    def setUp(self):
        """
        Copy the source and result files to temporary directories
        """
        self.tmpdir = tempfile.mkdtemp()
        self.sourcedir = os.path.join(self.tmpdir,
                                      'source')
        self.resultdir = os.path.join(self.tmpdir,
                                      'result')
        shutil.copytree(self.SOURCE_DIR,
                        self.sourcedir,
                        symlinks=True)
        shutil.copytree(self.RESULT_DIR,
                        self.resultdir,
                        symlinks=True)

    def diff(self):
        # There's no Pythonic way that's any more efficient than
        # calling out to "diff -r" here
        check_call('diff -q -r source result',
                   cwd=self.tmpdir,
                   shell=True)

    def render_course(self, cmdline):
        os.chdir(self.sourcedir)
        args = shlex.split(cmdline)
        CLI().main(args)

    def test_render_course_matching(self):
        self.render_course("olx-new-run foo 2019-01-01 2019-12-31")
        self.diff()

    def test_render_course_nonmatching(self):
        self.render_course("olx-new-run bar 2019-01-01 2019-12-31")
        with self.assertRaises(CalledProcessError):
            self.diff()

    def test_render_course_error(self):
        """Force an exception in rendering by removing a required file."""
        os.remove(os.path.join(self.sourcedir,
                               'include',
                               'course.xml'))
        with self.assertRaises(CLIException):
            self.render_course("olx-new-run foo 2019-01-01 2019-12-31")

    def test_render_course_force_git_error(self):
        # Simulate an empty PATH, so a git command fails
        with patch.dict(os.environ,
                        {'PATH': ''}):
            with self.assertRaises(CLIException):
                self.render_course("olx new-run -b foo 2019-01-01 2019-12-31")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)


class GitFullCourseTestCase(FullCourseTestCase):

    def setUp(self):
        super(GitFullCourseTestCase, self).setUp()

        os.chdir(self.sourcedir)
        repo = git.Repo.init()
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "John D. Oe")
            cw.set_value("user", "email", "johndoe@example.com")
            cw.release()
        repo.git.add('.')
        repo.git.commit('-m', 'Initial commit')

        self.repo = repo

    def diff(self):
        check_call('diff -q -r -x .git source result',
                   cwd=self.tmpdir,
                   shell=True)

    def checkout_master(self):
        self.repo.git.checkout('master')

    def test_render_course_matching_git(self):
        self.render_course("olx-new-run -b foo 2019-01-01 2019-12-31")
        self.diff()
        self.assertIn('run/foo', self.repo.branches)

    def test_render_course_duplicate_run_name(self):
        """Does a duplicate run name raise a CLI error?"""
        # First render, should succeed
        self.render_course("olx-new-run -b foo 2019-01-01 2019-12-31")
        with self.assertRaises(CLIException):
            # Second render, should fail because we're not using --force
            self.render_course("olx-new-run -b foo 2019-01-01 2019-12-31")

    def test_render_course_duplicate_run_name_force(self):
        """Does a duplicate run name succeed if using -f/--force?"""
        # First render, should succeed without -f
        self.render_course("olx-new-run -b foo 2019-01-01 2020-01-30")
        # This is necessary because otherwise -f would try to delete
        # the checked-out branch, which can't work
        self.checkout_master()
        # Second render, should succeed now because we're using -f
        self.render_course("olx-new-run -f -b foo 2019-01-01 2019-12-31")
        # The course with the correct dates should have replaced the
        # one with the wrong dates, so the diff should now succees
        self.diff()
        self.assertIn('run/foo', self.repo.branches)

    def test_dirty_working_tree_dir(self):
        """Does a dirty working tree raise a CLI error?"""
        wd = self.repo.working_tree_dir
        with tempfile.NamedTemporaryFile(mode='w',
                                         dir=wd) as f:
            f.write('foo')
            f.flush()
            with self.assertRaises(CLIException):
                self.render_course("olx-new-run -b foo 2019-01-01 2019-12-31")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

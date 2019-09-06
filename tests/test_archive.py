from __future__ import print_function, unicode_literals

from olxutils.archive import ArchiveHelper

from tempfile import gettempdir

import os
import tarfile
import logging

from subprocess import check_output

from unittest import TestCase


class ArchiveHelperTestCase(TestCase):

    DEMO_COURSE_URL = 'https://github.com/edx/edx-demo-course'
    DEMO_COURSE_TAG = 'open-release/ironwood.2'

    def _git_command(self, args):
        command = "git %s" % args
        logging.debug("+ %s" % command)
        return check_output(command, shell=True).strip()

    def setUp(self):
        # Create a local checkout of the edX demo course.
        #
        # Just so we don't download the course archive on every test
        # run, do a HEAD request first, and only follow up with a GET
        # if the local copy doesn't already exist.

        tmpdir = os.path.join(gettempdir(),
                              'olx-utils-test-4w9786')

        self.checkout_dir = os.path.join(tmpdir, 'edx-demo-course')

        if not os.path.exists(self.checkout_dir):
            os.makedirs(tmpdir, 0o755)
            self._git_command('-C %s clone -b %s %s' %
                              (tmpdir,
                               self.DEMO_COURSE_TAG,
                               self.DEMO_COURSE_URL))

    def test_content(self):
        # create an archive with ArchiveHelper
        helper = ArchiveHelper(root_directory=self.checkout_dir,
                               base_name='archive')
        archive = helper.make_archive()

        # Read back the contents
        with tarfile.open(name=archive,
                          mode='r|gz') as copy:
            names = copy.getnames()

        expected_names = [
            'course/about',
            'course/chapter',
            'course/combinedopenended',
            'course/course',
            'course/course.xml',
            'course/discussion',
            'course/drafts',
            'course/html',
            'course/info',
            'course/peergrading',
            'course/policies',
            'course/sequential',
            'course/static',
            'course/tabs',
            'course/vertical',
            'course/video',
            'course/videoalpha',
        ]

        for name in expected_names:
            self.assertIn(name, names)

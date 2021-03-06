# Copyright 2014 Cloudbase Solutions Srl
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import unittest

import mock

from cloudbaseinit.plugins.common import execcmd
from cloudbaseinit.tests import testutils


def _remove_file(filepath):
    try:
        os.remove(filepath)
    except OSError:
        pass


@mock.patch('cloudbaseinit.osutils.factory.get_os_utils')
class execcmdTest(unittest.TestCase):

    def test_from_data(self, _):
        command = execcmd.BaseCommand.from_data(b"test")

        self.assertIsInstance(command, execcmd.BaseCommand)

        # Not public API, though.
        self.assertTrue(os.path.exists(command._target_path),
                        command._target_path)
        self.addCleanup(_remove_file, command._target_path)

        with open(command._target_path) as stream:
            data = stream.read()

        self.assertEqual("test", data)
        command._cleanup()
        self.assertFalse(os.path.exists(command._target_path),
                         command._target_path)

    def test_args(self, _):
        class FakeCommand(execcmd.BaseCommand):
            command = mock.sentinel.command

        with testutils.create_tempfile() as tmp:
            fake_command = FakeCommand(tmp)
            self.assertEqual([mock.sentinel.command, tmp],
                             fake_command.args)

            fake_command = execcmd.BaseCommand(tmp)
            self.assertEqual([tmp], fake_command.args)

    def test_from_data_extension(self, _):
        class FakeCommand(execcmd.BaseCommand):
            command = mock.sentinel.command
            extension = ".test"

        command = FakeCommand.from_data(b"test")
        self.assertIsInstance(command, FakeCommand)

        self.addCleanup(os.remove, command._target_path)
        self.assertTrue(command._target_path.endswith(".test"))

    def test_execute_normal_command(self, mock_get_os_utils):
        mock_osutils = mock_get_os_utils()

        with testutils.create_tempfile() as tmp:
            command = execcmd.BaseCommand(tmp)
            command.execute()

            mock_osutils.execute_process.assert_called_once_with(
                [command._target_path],
                shell=command.shell)

            # test __call__ API.
            mock_osutils.execute_process.reset_mock()
            command()

            mock_osutils.execute_process.assert_called_once_with(
                [command._target_path],
                shell=command.shell)

    def test_execute_powershell_command(self, mock_get_os_utils):
        mock_osutils = mock_get_os_utils()

        with testutils.create_tempfile() as tmp:
            command = execcmd.Powershell(tmp)
            command.execute()

            mock_osutils.execute_powershell_script.assert_called_once_with(
                command._target_path, command.sysnative)

    def test_execute_cleanup(self, _):
        with testutils.create_tempfile() as tmp:
            cleanup = mock.Mock()
            command = execcmd.BaseCommand(tmp, cleanup=cleanup)
            command.execute()

            cleanup.assert_called_once_with()

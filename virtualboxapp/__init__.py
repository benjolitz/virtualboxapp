'''
A way to run a specially configured VirtualBox machine with a specific command
'''
import json
from collections import namedtuple
import os.path
import vbox
import time
import shlex
import logging

logger = logging.getLogger('virtualboxapp')
logger.addHandler(logging.NullHandler())

__author__ = "Ben Jolitz"
__copyright__ = "Copyright 2015, Ben Jolitz"
__credits__ = []
__license__ = "BSD"
__version__ = "0.0.1"
__maintainer__ = "Ben Jolitz"
__email__ = "ben.jolitz+virtualboxapp@gmail.com"
__status__ = "Alpha"

SharedFolder = namedtuple(
    'SharedFolder', ('share_name', 'path', 'mount_point',))
SharedFolders = namedtuple('SharedFolders', ['folders', 'mount_command'])
SHARED_FOLDER_REQUIRED_KEYS = frozenset(['share_name', 'path', 'mount_point'])
unicode_type = type(u'')


def byteify(item):
    if isinstance(item, dict):
        return {
            byteify(key): byteify(value) for key, value
            in item.iteritems()}
    elif isinstance(item, list):
        return [byteify(element) for element in item]
    elif isinstance(item, unicode_type):
        return item.encode('utf-8')
    return item


def parse_shared_folders(config, folder_key):
    folders = config[folder_key]
    return tuple(verify_shared_folders(folders))


def verify_shared_folders(folders):
    for folder in folders:
        if not all(folder.get(key, False) for key in
                   SHARED_FOLDER_REQUIRED_KEYS):
            raise KeyError(
                "Shared folder declaration incomplete. Missing {0!r}".format(
                    [x for x in SHARED_FOLDER_REQUIRED_KEYS
                     if not folder.get(x)]))
        folder['path'] = os.path.abspath(os.path.expanduser(folder['path']))
        yield SharedFolder(
            folder['share_name'],
            folder['path'],
            folder['mount_point'])


def acquire_vm(config, vm_name_key):
    host = config['vbox'].api.vms.get(config[vm_name_key])
    if host is None:
        raise KeyError('VM {0} not found in VirtualBox!'.format(
            config[vm_name_key]))
    return host


APP_KEY = namedtuple('APP_KEY', ['key', 'empty_allowed', 'parse_function'])
APP_REQUIRED_KEYS = frozenset([
    APP_KEY('GUEST_USERNAME', False, None),
    APP_KEY('GUEST_PASSWORD', False, None),
    APP_KEY('FOLDERS', True, parse_shared_folders),
    APP_KEY('MACHINE_NAME', False, acquire_vm),
    APP_KEY('COMMAND', False, None),
    APP_KEY('MOUNT_SHARE_COMMAND', True, None),
])


def wait_for_guest_additions(host):
    t_s = time.time()
    state = int(host.source.info['GuestAdditionsRunLevel'])
    while state < 3 or time.time() - t_s > 60:
        state = int(host.source.info['GuestAdditionsRunLevel'])
        time.sleep(0.01)
    return state == 3


def setup_virtual_folders(host, folders):
    current_folders = dict(
        (x.name.lower(), x) for x in host.shared.listRegistered())
    for folder in folders:
        if folder.share_name.lower() in current_folders:
            if folder.path == current_folders[folder.share_name.lower()].path:
                continue
            current_folders[folder.share_name.lower()].remove()
        host.shared.set(folder.share_name, folder.path)


def run(*apps):
    for app in apps:
        machine = app['vbox']
        host = app['MACHINE_NAME']
        if host.state.isRunning():
            continue
        try:
            if not host.state.isSaved():
                machine.cli.manage.setExtraData(
                    host.name, 'GUI/Seamless', 'off')
                if app['FOLDERS']:
                    setup_virtual_folders(host, app['FOLDERS'])
                host.state.start()
                if not wait_for_guest_additions(host):
                    host.state.powerOff()
                    continue
                host.source.savestate()
            machine.cli.manage.setExtraData(
                host.name, 'GUI/Seamless', 'on')
            host.state.start()
            wait_for_guest_additions(host)
            if 'controller' not in app:
                app['controller'] = \
                    host.guest.control(
                        app['GUEST_USERNAME'], app['GUEST_PASSWORD'])
            control = app['controller']
            for folder in app['FOLDERS']:
                test_command = shlex.split(
                    app['TEST_IF_MOUNTED']['COMMAND'].format(
                        mount_point=folder.mount_point,
                        share_name=folder.share_name))
                mount_command = app['MOUNT_SHARE_COMMAND'].format(
                    mount_point=folder.mount_point,
                    share_name=folder.share_name).split()
                unmount_command = shlex.split(
                    app['UNMOUNT_SHARE_COMMAND'].format(
                        mount_point=folder.mount_point,
                        share_name=folder.share_name))
                try:
                    control.execute(
                        test_command, program=test_command[0])
                    if app['TEST_IF_MOUNTED']['FALSE_RESULT_TYPE'].lower() \
                            != 'exception':
                        pass
                except vbox.api.exceptions.ExecuteError:
                    pass
                else:
                    control.execute(
                        unmount_command, program=unmount_command[0])
                time.sleep(2)
                control.execute(mount_command, program=mount_command[0])
            control.execute([], program=app['COMMAND'])
            host.source.savestate()
        except (KeyboardInterrupt, SystemExit):
            machine.cli.manage.setExtraData(
                host.name, 'GUI/Seamless', 'off')
            host.state.powerOff()
            raise SystemExit
        except Exception as e:
            logger.exception("Uncaught Exception ({0})!".format(e))
            machine.cli.manage.setExtraData(
                host.name, 'GUI/Seamless', 'off')
            if host.state.val == 'running':
                try: host.state.powerOff()
                except Exception as e:
                    logger.exception('Unable to halt')
            raise


def verify_apps(manager, *iterable):
    for app_path in iterable:
        with open(app_path, 'rb') as fh:
            try:
                app_config = byteify(json.loads(fh.read()))
            except ValueError:
                raise ValueError(
                    '{0!r} is invalid! Consider JSON Linting it!'.format(
                        app_path))

            app_config['vbox'] = manager
            for app_key in APP_REQUIRED_KEYS:
                try:
                    value = app_config[app_key.key]
                except KeyError:
                    raise KeyError(
                        '{0!r} is missing required key {1!r}'.format(
                            app_path, app_key.key))
                else:
                    if not value and not app_key.empty_allowed:
                        raise KeyError(
                            '{0}[{1!r}] can not be empty!'.format(
                                app_path, app_key.key))
                    if app_key.parse_function:
                        app_config[app_key.key] = app_key.parse_function(
                            app_config, app_key.key)
            yield app_config


def main():
    import optparse
    parser = optparse.OptionParser()
    _, json_applications = parser.parse_args()
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    vbox_logger = logging.getLogger('vbox')
    vbox_logger.setLevel(logging.DEBUG)
    vbox_logger.addHandler(handler)
    run(*[app for app in verify_apps(vbox.VBox(), *json_applications)])

if __name__ == "__main__":
    main()

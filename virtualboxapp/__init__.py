import json
from collections import namedtuple
import os.path
import vbox

SharedFolder = namedtuple(
    'SharedFolder', ('share_name', 'path', 'mount_point',))
SharedFolders = namedtuple('SharedFolders', ['folders', 'mount_command'])
SHARED_FOLDER_REQUIRED_KEYS = frozenset(['share_name', 'path', 'mount_point'])


def parse_shared_folders(config, folder_key):
    folders = config[folder_key]
    mount_command = config['MOUNT_SHARE_COMMAND']
    return SharedFolders(tuple(verify_shared_folders(folders)), mount_command)


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
            folder['share_name'], folder['path'], folder['mount_point'])


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


def run(*apps):
    for app in apps:
        print(app)


def verify_apps(manager, *iterable):
    for app_path in iterable:
        with open(app_path, 'rb') as fh:
            try:
                app_config = json.loads(fh.read())
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
    run(*[app for app in verify_apps(vbox.VBox(), json_applications)])

if __name__ == "__main__":
    main()

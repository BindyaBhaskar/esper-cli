from cement import ex, Controller
from cement.utils.version import get_version_banner
from crayons import white
from esperclient import CommandRequest
from esperclient.rest import ApiException

from esper.controllers.enums import OutputFormat, DeviceCommandEnum
from esper.core.version import get_version
from esper.ext.api_client import APIClient
from esper.ext.db_wrapper import DBWrapper
from esper.ext.utils import validate_creds_exists

VERSION_BANNER = """
Command Line Tool for Esper SDK %s
%s
""" % (get_version(), get_version_banner())


class DeviceCommand(Controller):
    class Meta:
        label = 'device-command'

        # text displayed at the top of --help output
        description = 'Fire commands for device'

        # text displayed at the bottom of --help output
        epilog = 'Usage: espercli device-command'

        stacked_type = 'nested'
        stacked_on = 'base'

    def _command_basic_response(self, command, format=OutputFormat.TABULATED):
        valid_keys = ['id', 'command', 'state']

        if format == OutputFormat.TABULATED:
            title = white("TITLE", bold=True)
            details = white("DETAILS", bold=True)
            renderable = [{title: k, details: v} for k, v in command.to_dict().items() if k in valid_keys]
        else:
            renderable = {k: v for k, v in command.to_dict().items() if k in valid_keys}

        return renderable

    @ex(
        help='Show command details',
        arguments=[
            (['command_id'],
             {'help': 'Device command id',
              'action': 'store'}),
            (['-d', '--device'],
             {'help': 'Device id',
              'action': 'store',
              'dest': 'device'}),
            (['-j', '--json'],
             {'help': 'Render result in Json format',
              'action': 'store_true',
              'dest': 'json'}),
        ]
    )
    def show(self):
        command_id = self.app.pargs.command_id
        validate_creds_exists(self.app)
        db = DBWrapper(self.app.creds)
        command_client = APIClient(db.get_configure()).get_command_api_client()
        enterprise_id = db.get_enterprise_id()

        if self.app.pargs.device:
            device_id = self.app.pargs.device
        else:
            device = db.get_device()
            if not device or not device.get('id'):
                self.app.log.info('Not set the current device.')
                return

            device_id = device.get('id')

        try:
            response = command_client.get_command(command_id, device_id, enterprise_id)
        except ApiException as e:
            self.app.log.debug(f"Failed to show details of command: {e}")
            self.app.log.error(f"Failed to show details of command, reason: {e.reason}")
            return

        if not self.app.pargs.json:
            renderable = self._command_basic_response(response)
            print(white(f"\tCOMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.TABULATED.value, headers="keys", tablefmt="fancy_grid")
        else:
            renderable = self._command_basic_response(response, OutputFormat.JSON)
            print(white(f"COMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.JSON.value)

    @ex(
        help='Install application version',
        arguments=[
            (['-d', '--device'],
             {'help': 'Device id',
              'action': 'store',
              'dest': 'device'}),
            (['-v', '--version'],
             {'help': 'Application version id',
              'action': 'store',
              'dest': 'version'}),
            (['-j', '--json'],
             {'help': 'Render result in Json format',
              'action': 'store_true',
              'dest': 'json'}),
        ]
    )
    def install(self):
        validate_creds_exists(self.app)
        db = DBWrapper(self.app.creds)
        command_client = APIClient(db.get_configure()).get_command_api_client()
        enterprise_id = db.get_enterprise_id()

        if self.app.pargs.device:
            device_id = self.app.pargs.device
        else:
            device = db.get_device()
            if not device or not device.get('id'):
                self.app.log.info('Not set the current device.')
                return

            device_id = device.get('id')

        version_id = self.app.pargs.version

        command_request = CommandRequest(command_args={"app_version": version_id},
                                         command=DeviceCommandEnum.INSTALL.name)
        try:
            response = command_client.run_command(enterprise_id, device_id, command_request)
        except ApiException as e:
            self.app.log.debug(f"Failed to fire the install command: {e}")
            self.app.log.error(f"Failed to install application, reason: {e.reason}")
            return

        if not self.app.pargs.json:
            renderable = self._command_basic_response(response)
            print(white(f"\tCOMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.TABULATED.value, headers="keys", tablefmt="fancy_grid")
        else:
            renderable = self._command_basic_response(response, OutputFormat.JSON)
            print(white(f"COMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.JSON.value)

    @ex(
        help='Ping a device',
        arguments=[
            (['-d', '--device'],
             {'help': 'Device id',
              'action': 'store',
              'dest': 'device'}),
            (['-j', '--json'],
             {'help': 'Render result in Json format',
              'action': 'store_true',
              'dest': 'json'}),
        ]
    )
    def ping(self):
        validate_creds_exists(self.app)
        db = DBWrapper(self.app.creds)
        command_client = APIClient(db.get_configure()).get_command_api_client()
        enterprise_id = db.get_enterprise_id()

        if self.app.pargs.device:
            device_id = self.app.pargs.device
        else:
            device = db.get_device()
            if not device or not device.get('id'):
                self.app.log.info('Not set the current device.')
                return

            device_id = device.get('id')

        command_request = CommandRequest(command=DeviceCommandEnum.UPDATE_HEARTBEAT.name)
        try:
            response = command_client.run_command(enterprise_id, device_id, command_request)
        except ApiException as e:
            self.app.log.debug(f"Failed to fire the ping command: {e}")
            self.app.log.error(f"Failed to ping the device, reason: {e.reason}")
            return

        if not self.app.pargs.json:
            renderable = self._command_basic_response(response)
            print(white(f"\tCOMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.TABULATED.value, headers="keys", tablefmt="fancy_grid")
        else:
            renderable = self._command_basic_response(response, OutputFormat.JSON)
            print(white(f"COMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.JSON.value)

    @ex(
        help='Lock a device',
        arguments=[
            (['-d', '--device'],
             {'help': 'Device id',
              'action': 'store',
              'dest': 'device'}),
            (['-j', '--json'],
             {'help': 'Render result in Json format',
              'action': 'store_true',
              'dest': 'json'}),
        ]
    )
    def lock(self):
        validate_creds_exists(self.app)
        db = DBWrapper(self.app.creds)
        command_client = APIClient(db.get_configure()).get_command_api_client()
        enterprise_id = db.get_enterprise_id()

        if self.app.pargs.device:
            device_id = self.app.pargs.device
        else:
            device = db.get_device()
            if not device or not device.get('id'):
                self.app.log.info('Not set the current device.')
                return

            device_id = device.get('id')

        command_request = CommandRequest(command=DeviceCommandEnum.LOCK.name)
        try:
            response = command_client.run_command(enterprise_id, device_id, command_request)
        except ApiException as e:
            self.app.log.debug(f"Failed to fire the lock command: {e}")
            self.app.log.error(f"Failed to lock the device, reason: {e.reason}")
            return

        if not self.app.pargs.json:
            renderable = self._command_basic_response(response)
            print(white(f"\tCOMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.TABULATED.value, headers="keys", tablefmt="fancy_grid")
        else:
            renderable = self._command_basic_response(response, OutputFormat.JSON)
            print(white(f"COMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.JSON.value)

    @ex(
        help='Reboot a device',
        arguments=[
            (['-d', '--device'],
             {'help': 'Device id',
              'action': 'store',
              'dest': 'device'}),
            (['-j', '--json'],
             {'help': 'Render result in Json format',
              'action': 'store_true',
              'dest': 'json'}),
        ]
    )
    def reboot(self):
        validate_creds_exists(self.app)
        db = DBWrapper(self.app.creds)
        command_client = APIClient(db.get_configure()).get_command_api_client()
        enterprise_id = db.get_enterprise_id()

        if self.app.pargs.device:
            device_id = self.app.pargs.device
        else:
            device = db.get_device()
            if not device or not device.get('id'):
                self.app.log.info('Not set the current device.')
                return

            device_id = device.get('id')

        command_request = CommandRequest(command=DeviceCommandEnum.REBOOT.name)
        try:
            response = command_client.run_command(enterprise_id, device_id, command_request)
        except ApiException as e:
            self.app.log.debug(f"Failed to fire the reboot command: {e}")
            self.app.log.error(f"Failed to reboot the device, reason: {e.reason}")
            return

        if not self.app.pargs.json:
            renderable = self._command_basic_response(response)
            print(white(f"\tCOMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.TABULATED.value, headers="keys", tablefmt="fancy_grid")
        else:
            renderable = self._command_basic_response(response, OutputFormat.JSON)
            print(white(f"COMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.JSON.value)

    @ex(
        help='Wipe a device',
        arguments=[
            (['-d', '--device'],
             {'help': 'Device id',
              'action': 'store',
              'dest': 'device'}),
            (['-e', '--exstorage'],
             {'help': 'External storage',
              'action': 'store_true',
              'dest': 'external_storage'}),
            (['-f', '--frp'],
             {'help': 'Factory reset production',
              'action': 'store_true',
              'dest': 'frp'}),
            (['-j', '--json'],
             {'help': 'Render result in Json format',
              'action': 'store_true',
              'dest': 'json'}),
        ]
    )
    def wipe(self):
        validate_creds_exists(self.app)
        db = DBWrapper(self.app.creds)
        command_client = APIClient(db.get_configure()).get_command_api_client()
        enterprise_id = db.get_enterprise_id()

        if self.app.pargs.device:
            device_id = self.app.pargs.device
        else:
            device = db.get_device()
            if not device or not device.get('id'):
                self.app.log.info('Not set the current device.')
                return

            device_id = device.get('id')

        external_storage = self.app.pargs.external_storage
        frp = self.app.pargs.frp

        if external_storage is None:
            self.app.log.error('External storage value is empty')

        if frp is None:
            self.app.log.error('Factory reset production value is empty')

        command_request = CommandRequest(command_args={"wipe_external_storage": external_storage, 'wipe_FRP': frp},
                                         command=DeviceCommandEnum.WIPE.name)
        try:
            response = command_client.run_command(enterprise_id, device_id, command_request)
        except ApiException as e:
            self.app.log.debug(f"Failed to fire the wipe command: {e}")
            self.app.log.error(f"Failed to wipe the device, reason: {e.reason}")
            return

        if not self.app.pargs.json:
            renderable = self._command_basic_response(response)
            print(white(f"\tCOMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.TABULATED.value, headers="keys", tablefmt="fancy_grid")
        else:
            renderable = self._command_basic_response(response, OutputFormat.JSON)
            print(white(f"COMMAND DETAILS of {response.command}", bold=True))
            self.app.render(renderable, format=OutputFormat.JSON.value)

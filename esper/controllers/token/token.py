from cement import Controller, ex
from esperclient.rest import ApiException

from esper.controllers.enums import OutputFormat
from esper.ext.api_client import APIClient
from esper.ext.db_wrapper import DBWrapper
from esper.ext.utils import validate_creds_exists, parse_error_message


class Token(Controller):
    class Meta:
        label = 'token'

        # text displayed at the top of --help output
        description = 'token command for displaying all the information associated with the token'

        # text displayed at the bottom of --help output
        epilog = 'Usage: espercli token'

        stacked_type = 'nested'
        stacked_on = 'base'


    def _token_basic_response(self, token, format=OutputFormat.TABULATED):
        if format == OutputFormat.TABULATED:
            title = "TITLE"
            details = "DETAILS"
            renderable = [
                {title: 'Enterprise Id', details: token.enterprise},
                {title: 'Token', details: token.token},
                {title: 'Expires On', details: token.expires_on},
                {title: 'Scope', details: token.scope},
                {title: 'Created On', details: token.created_on},
                {title: 'Updated On', details: token.updated_on}
            ]
        else:
            renderable = {
                'Enterprise': token.enterprise,
                'Developer App': token.developer_app,
                'Token': token.token,
                'Expires On': token.scope,
                'Created On': str(token.created_on),
                'Updated On': str(token.updated_on)
            }

        return renderable
        
        

    @ex(
        help='Show token details',
        arguments=[
            (['-j', '--json'],
             {'help': 'Render result in Json format',
              'action': 'store_true',
              'dest': 'json'})
        ]
    )
    def show(self):
        validate_creds_exists(self.app)
        db = DBWrapper(self.app.creds)
        token_client = APIClient(db.get_configure()).get_token_api_client()
        response = None
        try:
            response = token_client.get_token_info()
        except ApiException as e:
            self.app.log.error(f"[token-show] Failed to show details of an token: {e}")
            self.app.render(f"ERROR: {parse_error_message(self.app, e)}\n")
            return

        if not self.app.pargs.json:
            renderable = self._token_basic_response(response)
            self.app.render(renderable, format=OutputFormat.TABULATED.value, headers="keys", tablefmt="plain")
        else:
            renderable = self._token_basic_response(response, OutputFormat.JSON)
            self.app.render(renderable, format=OutputFormat.JSON.value)



    def renew_token_basic_response(self, token, format=OutputFormat.TABULATED):
        if format == OutputFormat.TABULATED:
            title = "TITLE"
            details = "DETAILS"
            renderable = [
                {title: 'Id', details: token.id},
                {title: 'User', details: token.user},
                {title: 'Enterprise Id', details: token.enterprise},
                {title: 'Developer App', details: token.developerapp},
                {title: 'Token', details: token.token},
                {title: 'Scope', details: token.scope},
                {title: 'Created On', details: token.created_on},
                {title: 'Updated On', details: token.updated_on},
                {title: 'Expires On', details: token.expires_at},
            ]
        else:
            renderable = {
                'Id': token.id,
                'User': token.user,
                'Enterprise Id': token.enterprise,
                'Developer App': token.developerapp,
                'Token': token.token,
                'Scope': token.scope,
                'Created On': token.created_on,
                'Updated On': token.updated_on,
                'Expires On': token.expires_at,
            }

        return renderable



    @ex(
        help='Renew Token',
        arguments=[
            (['-d','--developerappid'],
             {'help': 'DeveloperApp id',
              'action': 'store',
              'dest': 'dev_app_id'}),
            (['-t','--token'],
             {'help': 'Token to renew',
              'action': 'store',
              'dest': 'token'}),
            (['-j', '--json'],
             {'help': 'Render result in Json format',
              'action': 'store_true',
              'dest': 'json'})
        ]
    )
    def renew(self):
        validate_creds_exists(self.app)
        db = DBWrapper(self.app.creds)
        token_client = APIClient(db.get_configure()).get_token_api_client()
        enterprise_id = db.get_enterprise_id()

        if self.app.pargs.token:
            token_to_renew = self.app.pargs.token
        else:
            self.app.log.debug('There is no token given to renew.')
            self.app.render('There is no token given to renew.\n')
            return 

        if self.app.pargs.token:
            developer_app_id = self.app.pargs.dev_app_id
        else:
            self.app.log.debug('DeveloperApp id is not given')
            self.app.render('DeveloperApp id is not given\n')
            return 

        try:
            response = token_client.renew_token(enterprise_id, developer_app_id, token_to_renew)
        except ApiException as e:
            self.app.log.error(f"[token-show] Failed to renew token: {e}")
            self.app.render(f"ERROR: {parse_error_message(self.app, e)}\n")
            return
 
        if not self.app.pargs.json:
            renderable = self.renew_token_basic_response(response)
            self.app.render(renderable, format=OutputFormat.TABULATED.value, headers="keys", tablefmt="plain")
        else:
            renderable = self.renew_token_basic_response(response, OutputFormat.JSON)
            self.app.render(renderable, format=OutputFormat.JSON.value)
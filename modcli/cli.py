import click
import crayons
import requests
import re

from modcli import settings, config, __version__


def get_url(api_url: str, path: str):
    if not re.match('https?://.*', api_url):
        raise Exception('Invalid api_url: {0}'.format(api_url))
    return '{0}/{1}'.format(api_url.rstrip('/'), path.lstrip('/'))


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(prog_name='modcli', version=__version__)
def main():
    pass


@click.group()
def auth():
    pass


@click.command(help='Authenticate user with SSO (MOD Forum)')
@click.option('-s', '--show-token', type=bool, help='Print the JWT token obtained', is_flag=True)
@click.option('-o', '--one-time', type=bool, help='Only print token once (do not store it)', is_flag=True)
@click.option('-e', '--environment', type=click.Choice(['prod', 'labs', 'dev']), default='prod', help='MOD API Environment')
def login_sso(show_token: bool, one_time: bool, environment: str):
    api_url = settings.API_URLS[environment]
    result = requests.post(get_url(api_url, '/users/tokens_sso'), json={
        'agent': 'modcli:{0}'.format(__version__),
    })
    if result.status_code != 200:
        click.echo(crayons.red('Error: {0}'.format(result.json()['error-message'])), err=True)
        exit(1)
    token = result.json()['message'].strip()
    _, payload, _ = token.split('.')
    username = payload['user_id']

    if not one_time:
        config.save_token(token, username, api_url, environment)

    if show_token or one_time:
        print(token.strip())
    else:
        click.echo(crayons.green('You\'re now logged in as [{0}].'.format(username)))


@click.command(help='Authenticate user')
@click.option('-u', '--username', type=str, prompt=True, help='User ID')
@click.option('-p', '--password', type=str, prompt=True, hide_input=True, help='User password')
@click.option('-s', '--show-token', type=bool, help='Print the JWT token obtained', is_flag=True)
@click.option('-o', '--one-time', type=bool, help='Only print token once (do not store it)', is_flag=True)
@click.option('-e', '--environment', type=click.Choice(['prod', 'labs', 'dev']), default='prod', help='MOD API Environment')
def login(username: str, password: str, show_token: bool, one_time: bool, environment: str):
    api_url = settings.API_URLS[environment]
    result = requests.post(get_url(api_url, '/users/tokens'), json={
        'user_id': username,
        'password': password,
        'agent': 'modcli:{0}'.format(__version__),
    })
    if result.status_code != 200:
        click.echo(crayons.red('Error: {0}'.format(result.json()['error-message'])), err=True)
        exit(1)
    token = result.json()['message'].strip()

    if not one_time:
        config.save_token(token, username, api_url, environment)

    if show_token or one_time:
        print(token.strip())
    else:
        click.echo(crayons.green('You\'re now logged in as [{0}].'.format(username)))


@click.command(help='Show current active access JWT token')
@click.option('-e', '--environment', type=click.Choice(['prod', 'labs', 'dev']), default=None, help='MOD API Environment')
def active_token(environment: str):
    token = config.read_token(environment)
    if not token:
        click.echo(crayons.red('You must authenticate first.'), err=True)
        click.echo('Try:\n $ modcli auth login')
        exit(1)
    click.echo(token)


auth.add_command(login)
auth.add_command(active_token)
main.add_command(auth)


if __name__ == '__main__':
    main()

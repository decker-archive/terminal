# SPDX Identifier: MIT
# Copyright (c) 2022 mastadon Inc.
import asyncio
import sys
import getpass

import pick
import aiohttp
import keyboard

MAIN_MENU = [
    'Change My Profile',
    'Display Guild',
    'Create Guild',
    'Join Guild',
    'Show Joined Guilds',
    'Change Settings',
]

GUILD_MENU = [
    'Settings',
    'Leave',
]

async def init_session():
    global _session
    global BASE_URL
    BASE_URL = 'https://concord.chat/api/v5'
    _session = aiohttp.ClientSession(
        headers={'User-Agent': 'Mastadon TUI'}
    )


async def request(method: str, prefix: str, data: dict = None):
    if data:
        r = await _session.request(method, BASE_URL + prefix, json=data, headers={'Authorization': _token})
    else:
        r = await _session.request(method, BASE_URL + prefix, json=data, headers={'Authorization': _token})

    if not r.ok:
        raise Exception(r.status, await r.json(), prefix)
    else:
        return r

async def create_token(email: str, password: str) -> str:
    data = {
        'email': email,
        'password': password
    }

    r = await _session.get(
        BASE_URL + '/users/@me/tokens', json=data
    )

    if r.status != 201:
        raise Exception('Invalid Email and/or Password')

    ret = await r.json()

    return ret[0]

async def get_me():
    r = await request('GET', '/users/@me')
    return await r.json()

async def get_guilds():
    r = await request('GET', '/users/@me/guilds')
    return await r.json()

def msg(*values: object):
    print(*values, file=sys.stderr)

def main_menu() -> str:
    return pick.pick(MAIN_MENU, 'Pick your next Menu: ', indicator='>')

async def get_channels(guild_id: int):
    r = await request('GET', f'/guilds/{str(guild_id)}/channels')
    return await r.json()

async def edit_user(**data):
    r = await request('PATCH', '/users/@me', data=data)
    return await r.json()

async def parse_main_menu(selection: str):
    pause_up()
    if selection[0] == MAIN_MENU[0]:
        settings = [
            'username',
            'discriminator',
            'email',
            'password',
            'cancel'
        ]
        setting = pick.pick(settings, 'Pick the Setting to edit: ', indicator='>')[0]
        if setting == 'cancel':
            s = main_menu()
            return await parse_main_menu(s)



    if selection[0] == MAIN_MENU[1]:
        guild_names = []
        for guild in guilds:
            guild_names.append({'label': guild['name'], 'id': guild['id']})

        guild_names.append('cancel')
        def get_label(o):
            if isinstance(o,str):return o
            else:return o.get('label')

        guild = pick.pick(guild_names, 'Select a Guild: ', indicator='>', options_map_func=get_label)

        if guild[0] == 'cancel':
            s = main_menu()
            return await parse_main_menu(s)

        channels = await get_channels(guild_id=guild[0]['id'])

        for g in guilds:
            if g['id'] == guild[0]['id']:
                guild = g

        channel_names = [channel['name'] for channel in channels if channel['type'] == 1]
        category_names = [channel['name'] for channel in channels if channel['type'] == 0]

        p = '''
        id: {id}
        name: {name}
        description: {description}
        channels: {channels}
        categorys: {categorys}
        nsfw: {nsfw}
        verified: {verified}
        '''.format(
            id=str(guild['id']),
            name=guild['name'],
            description=guild['description'],
            channels=', '.join(channel_names),
            categorys=', '.join(category_names),
            nsfw='yes' if guild['nsfw'] is True else 'no',
            verified='yes' if guild['verified'] is True else 'no'
        )

        msg(p)

        # TODO: Channel Menu

async def handler(type):
    global _token
    global me
    global guilds
    global message_cache

    if type[0] == 'Login':
        email = input('email: ')
        password = getpass.getpass('password: ')
        pause_up()

        await init_session()

        _token = await create_token(email, password)

        me = await get_me()

        msg(f'Welcome back to Mastadon, {me["username"]}#{str(me["discriminator"])}. We hope you enjoy your stay here.')
        del email, password

        guilds = await get_guilds()

        selection = main_menu()
        await parse_main_menu(selection=selection)


    elif type[0] == 'SignUp':
        ...
    else:
        return msg('ERROR: Invalid Input')

def pause_up():
    n = '\n'
    for _ in range(100):
        msg(n)

async def main():
    type = pick.pick(['Login', 'SignUp'], 'Please choose an option: ', indicator='>')
    pause_up()
    await handler(type)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(_session.close())
    loop.stop()
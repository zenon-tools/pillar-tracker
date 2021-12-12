import json
import datetime
import sys
import os

from utils.node_rpc_wrapper import NodeRpcWrapper
from utils.telegram_wrapper import TelegramWrapper


def check_and_send_pillar_events(telegram, cfg, cached_pillars, new_pillars):
    channel_id = cfg['telegram_channel_id']
    dev_chat_id = cfg['telegram_dev_chat_id']

    # Check for dismantled Pillars. Assume Pillar is dismantled if the owner address is not present anymore in the new data.
    for owner_address in cached_pillars:
        if owner_address not in new_pillars and len(new_pillars) < len(cached_pillars):
            m = create_dismantled_pillar_message(
                cached_pillars[owner_address])
            if 'error' in m:
                handle_error(telegram, dev_chat_id, m['error'])
            else:
                r = telegram.bot_send_message_to_chat(channel_id, m['message'])
                name = cached_pillars[owner_address]['name']
                print(
                    f'Pillar dismantled message sent ({name}): {r.status_code}')

    # Check for new Pillars. Assume Pillar is new if the owner address was not present in the cached data.
    for owner_address in new_pillars:
        if owner_address not in cached_pillars and len(new_pillars) > len(cached_pillars):
            m = create_new_pillar_message(
                new_pillars[owner_address])
            if 'error' in m:
                handle_error(telegram, dev_chat_id, m['error'])
            else:
                r = telegram.bot_send_message_to_chat(channel_id, m['message'])
                name = new_pillars[owner_address]['name']
                print(f'Pillar created message sent ({name}): {r.status_code}')

    # Check for Pillar name changes
    for owner_address in new_pillars:
        if owner_address in cached_pillars:

            # Get current and cached name
            current_name = new_pillars[owner_address]['name']
            cached_name = cached_pillars[owner_address]['name']

            if current_name != cached_name:
                m = create_pillar_name_changed_message(
                    cached_name, current_name)
                if 'error' in m:
                    handle_error(telegram, dev_chat_id, m['error'])
                else:
                    r = telegram.bot_send_message_to_chat(channel_id, m['message'])
                    print(
                        f'Pillar name changed message sent ({cached_name} -> {current_name}): {r.status_code}')

    # Check for changes in reward sharing
    for owner_address in new_pillars:
        if owner_address in cached_pillars:
            old_momentum_percentage = cached_pillars[
                owner_address]['giveMomentumRewardPercentage']
            new_momentum_percentage = new_pillars[owner_address]['giveMomentumRewardPercentage']
            old_delegate_percentage = cached_pillars[
                owner_address]['giveDelegateRewardPercentage']
            new_delegate_percentage = new_pillars[owner_address]['giveDelegateRewardPercentage']
            name = new_pillars[owner_address]['name']
            owner_address = new_pillars[owner_address]['ownerAddress']
            changed_shares_data = {}

            if old_momentum_percentage != new_momentum_percentage:
                changed_shares_data['name'] = name
                changed_shares_data['ownerAddress'] = owner_address
                changed_shares_data['momentumRewards'] = {
                    'oldMomentumPercentage': old_momentum_percentage, 'newMomentumPercentage': new_momentum_percentage}

            if old_delegate_percentage != new_delegate_percentage:
                changed_shares_data['name'] = name
                changed_shares_data['ownerAddress'] = owner_address
                changed_shares_data['delegateRewards'] = {
                    'oldDelegatePercentage': old_delegate_percentage, 'newDelegatePercentage': new_delegate_percentage}

            if changed_shares_data != {}:
                if 'momentumRewards' not in changed_shares_data:
                    changed_shares_data['momentumRewards'] = {
                        'oldMomentumPercentage': old_momentum_percentage}
                if 'delegateRewards' not in changed_shares_data:
                    changed_shares_data['delegateRewards'] = {
                        'oldDelegatePercentage': old_delegate_percentage}

                m = create_reward_share_changed_message(changed_shares_data)
                if 'error' in m:
                    handle_error(telegram, dev_chat_id, m['error'])
                else:
                    r = telegram.bot_send_message_to_chat(channel_id, m['message'])
                    name = new_pillars[owner_address]['name']
                    print(
                        f'Reward share changed message sent ({name}): {r.status_code}')


def create_dismantled_pillar_message(pillar_data):
    try:
        m = 'Pillar dismantled!\n'
        m = m + 'Pillar: ' + pillar_data['name']
        return {'message': m}
    except KeyError:
        return {'error': 'KeyError: create_dismantled_pillar_message'}


def create_new_pillar_message(pillar_data):
    try:
        m = 'New Pillar spawned!\n'
        m = m + 'Say hello to ' + pillar_data['name'] + '\n'
        m = m + 'Momentum rewards sharing: ' + \
            str(pillar_data['giveMomentumRewardPercentage']) + '%\n'
        m = m + 'Delegate rewards sharing: ' + \
            str(pillar_data['giveDelegateRewardPercentage']) + '%\n'
        return {'message': m}
    except KeyError:
        return {'error': 'KeyError: create_new_pillar_message'}


def create_pillar_name_changed_message(cached_name, current_name):
    try:
        m = 'Pillar name changed!\n'
        m = m + cached_name + ' \U000027A1 ' + current_name
        return {'message': m}
    except KeyError:
        return {'error': 'KeyError: create_pillar_name_changed_message'}


def create_reward_share_changed_message(changed_shares_data):
    try:
        m = 'Pillar: ' + changed_shares_data['name'] + '\n'

        old_momentum_percentage = changed_shares_data['momentumRewards']['oldMomentumPercentage']
        if ('newMomentumPercentage' in changed_shares_data['momentumRewards']):
            new_momentum_percentage = changed_shares_data['momentumRewards']['newMomentumPercentage']
            m = m + 'Momentum rewards sharing: ' + str(old_momentum_percentage) + \
                '% \U000027A1 ' + str(new_momentum_percentage) + '%\n'
        else:
            m = m + 'Momentum rewards sharing: ' + \
                str(old_momentum_percentage) + '%\n'

        old_delegate_percentage = changed_shares_data['delegateRewards']['oldDelegatePercentage']
        if ('newDelegatePercentage' in changed_shares_data['delegateRewards']):
            new_delegate_percentage = changed_shares_data['delegateRewards']['newDelegatePercentage']
            m = m + 'Delegate rewards sharing: ' + \
                str(old_delegate_percentage) + '% \U000027A1 ' + \
                str(new_delegate_percentage) + '%'
        else:
            m = m + 'Delegate rewards sharing: ' + str(old_delegate_percentage) + '%'

        return {'message': m}

    except KeyError:
        return {'error': 'KeyError: create_reward_share_changed_message'}


def create_pinned_stats_message(pillars, momentum_height):
    try:
        # Only show top 70 Pillars because of Telegram's message character limit (4096 characters)
        if len(pillars) > 70:
            m = 'Pillar reward sharing rates (top 70)\n' 
        else:
            m = 'Pillar reward sharing rates\n'
        m = m + 'Last updated: ' + \
            str(datetime.datetime.now(datetime.timezone.utc).strftime(
                '%Y-%m-%d %H:%M:%S')) + ' (UTC)\n'
        m = m + 'Momentum height: ' + str(momentum_height) + '\n'
        m = m + 'M = momentum reward sharing %\n'
        m = m + 'D = delegate reward sharing %\n'
        m = m + 'W = Pillar weight (ZNN) \n'
        m = m + 'P/E = produced/expected momentums\n\n'

        for owner_address in pillars:
            if pillars[owner_address]['rank'] < 70:
                weight = int(
                    round(pillars[owner_address]['weight'] / 100000000))
                m = m + str(pillars[owner_address]['rank'] + 1) + ' - ' + str(pillars[owner_address]['name']) + ' -> M: ' + str(pillars[owner_address]['giveMomentumRewardPercentage']) + '% D: ' + str(pillars[owner_address]['giveDelegateRewardPercentage']
                                                                                                                                                                                                        ) + '% W: ' + str(weight) + ' P/E: ' + str(pillars[owner_address]['currentStats']['producedMomentums']) + '/' + str(pillars[owner_address]['currentStats']['expectedMomentums']) + '\n'
        return {'message': m}

    except KeyError:
        return {'error': 'KeyError: create_pinned_stats_message'}


def read_file(file_path):
    f = open(file_path)
    content = json.load(f)
    f.close()
    return content


def write_to_file_as_json(data, file_name):
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile, indent=4)


def handle_error(telegram, dev_chat_id, message):
    print(message)

    # Send the developer a message if a developer chat ID is configured
    if len(dev_chat_id) != 0:
        telegram.bot_send_message_to_chat(chat_id=dev_chat_id, message=message)

    # Exit script on error
    sys.exit()


def main():

    # Get current file path
    path = os.path.dirname(os.path.abspath(__file__))

    # Read config
    cfg = read_file(f'{path}/config/config.json')

    # Data store directory
    DATA_STORE_DIR = f'{path}/data_store'

    # Pillar cache file
    PILLAR_CACHE_FILE = f'{DATA_STORE_DIR}/pillar_data.json'

    # Check and create data store directory
    if not os.path.exists(DATA_STORE_DIR):
        os.makedirs(DATA_STORE_DIR, exist_ok=True)

    # Check and create pillar cache file
    if not os.path.exists(f'{PILLAR_CACHE_FILE}'):
        open(f'{PILLAR_CACHE_FILE}', 'w+').close()

    # Create wrappers
    node = NodeRpcWrapper(node_url=cfg['node_url_http'])
    telegram = TelegramWrapper(
        bot_api_key=cfg['telegram_bot_api_key'])

    # Get latest momentum
    latest_momentum = node.get_latest_momentum()
    if 'error' in latest_momentum:
        handle_error(
            telegram, cfg['telegram_dev_chat_id'], latest_momentum['error'])

    # Get latest Pillar data
    new_pillar_data = node.get_all_pillars()
    if 'error' in new_pillar_data:
        handle_error(
            telegram, cfg['telegram_dev_chat_id'], new_pillar_data['error'])

    # Get cached Pillar data from file
    if os.stat(f'{DATA_STORE_DIR}/pillar_data.json').st_size != 0:
        cached_pillar_data = read_file(f'{DATA_STORE_DIR}/pillar_data.json')
    else:
        cached_pillar_data = None

    # Create and update the pinned stats message
    pinned_stats_message = create_pinned_stats_message(
        new_pillar_data['pillars'], latest_momentum['height'])
    if 'error' in pinned_stats_message:
        handle_error(telegram, cfg['telegram_dev_chat_id'],
                     pinned_stats_message['error'])
    else:
        r = telegram.bot_edit_message(
            chat_id=cfg['telegram_channel_id'], message_id=cfg['telegram_pinned_message_id'], message=pinned_stats_message['message'])
        print(f'Pinned message updated: {r.status_code}')

    # Check for new Pillar events if cached data exists
    if cached_pillar_data is not None:
        check_and_send_pillar_events(
            telegram, cfg, cached_pillar_data['pillars'], new_pillar_data['pillars'])

    # Cache current Pillar data to file
    write_to_file_as_json(
        new_pillar_data, f'{PILLAR_CACHE_FILE}')


if __name__ == '__main__':
    print(f'{str(datetime.datetime.now())}: Starting')
    main()
    print(f'{str(datetime.datetime.now())}: Completed')

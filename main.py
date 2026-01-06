import time
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChannel, MessageEntityTextUrl
import requests
from bs4 import BeautifulSoup
import re
from reg import reg  # make sure this import is at the top

#===============================================

api_id = 34291316
api_hash = 'b5dda7d9b8fc162bd3792e7a2b6e2926'
client = TelegramClient("my_session", api_id, api_hash)

source_channel_id = 3306540431 # main source channel
destination_channel = "@xuxhxudhx" # post channel
last_message_id = 96350 # message id
#https://t.me/c/2682944548/601074
#===============================================

def count_digits(text):
    return len(re.findall(r'\d', text))

def extract_telegraph_link(entities, message):
    if entities:
        for entity in entities:
            if isinstance(entity, MessageEntityTextUrl):
                return entity.url
    match = re.search(r'https://telegra.ph/\S+', message)
    return match.group(0) if match else None


def fetch_telegraph_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text(separator='\n')
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        date_pattern = re.compile(r'^[A-Za-z]+\s+\d{1,2},\s+\d{4}$')
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if start_index is None and date_pattern.match(line):
                start_index = i
            if "https://t.me/xForceOmegaBot" in line:
                end_index = i
                break  # stop at the first occurrence
        if start_index is not None and end_index is not None and end_index >= start_index:
            return '\n'.join(lines[start_index:end_index + 1])
        return None
    except Exception as e:
        print(f"Error reading Telegraph content: {e}")
        return None

#===============================================

with client:
    source = PeerChannel(source_channel_id)
    print("Listening for new messages...")
    while True:
        try:
            new_messages = client.iter_messages(source, min_id=last_message_id, reverse=True)
            for message in new_messages:
                if message.text:
                    # Skip messages containing "CC K1LLER"
                    if "CC K1LLER" in message.text:
                        print(f"Skipping message {message.id} because it contains CC K1LLER")
                        continue
                    
                    print(f"Checking message ID {message.id}...")
                    telegraph_url = extract_telegraph_link(message.entities, message.text)
                    if telegraph_url:
                        print(f"Telegraph link found: {telegraph_url}")
                        content = fetch_telegraph_content(telegraph_url)
                        if content:
                            lines = content.splitlines()
                            card_data_lines = lines[3:]  # skip the first 3 lines
                            card_message = '\n'.join(card_data_lines)
                            card_result = reg(card_message)
                            if card_result:
                                client.send_message(destination_channel, card_result)
                            else:
                                client.send_message(destination_channel, content)
                        else:
                            print("Telegraph parse failed, using original message...")
                            card_result = reg(message.text.strip())
                            if card_result and count_digits(card_result) > 20:
                                client.send_message(destination_channel, card_result)
                            else:
                                print("Not enough digits - not sending.")
                    else:
                        print("No telegraph link found - using original message")
                        card_result = reg(message.text.strip())
                        if card_result and count_digits(card_result) > 20:
                            client.send_message(destination_channel, card_result)
                        else:
                            print("Not enough digits - not sending.")
                if message.id > last_message_id:
                    last_message_id = message.id
            time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)



#LastVersion
# message skipတဲ့ ကုတ်ထည့်ချင်တယ် CC K1LLER ဒီစာပါရင် skip ပါ

import asyncio
import json
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import init, Fore
import pyfiglet

# Initialize colorama for colored output
init(autoreset=True)

CREDENTIALS_FILE = '/data/data/com.termux/files/home/credentials.json'  # Ensure the path is correct

# Function to save credentials to a local file
def save_credentials(credentials):
    try:
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f)
    except Exception as e:
        print(Fore.RED + f"Error saving credentials: {str(e)}")

# Function to load credentials from the local file
def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(Fore.RED + f"Error loading credentials: {str(e)}")
            return {}
    return {}

async def auto_sender(client, session_name):
    repeat_count = int(input(f"How many times do you want to send the message to all groups for {session_name}? "))
    delay_between_rounds = int(input(f"Enter the delay (in seconds) between each round for {session_name}: "))

    for round_num in range(1, repeat_count + 1):
        print(f"\nStarting round {round_num} of forwarding messages to all groups for {session_name}.")

        saved_messages_peer = await client.get_input_entity('me')
        history = await client(GetHistoryRequest(
            peer=saved_messages_peer,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            limit=1,
            max_id=0,
            min_id=0,
            hash=0
        ))

        if not history.messages:
            print("No messages found in 'Saved Messages'")
            return

        last_message = history.messages[0]

        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group = dialog.entity
                try:
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                except Exception as e:
                    print(Fore.RED + f"Failed to forward message to {group.title} using {session_name}: {str(e)}")
                await asyncio.sleep(3)

        print(f"Completed round {round_num}. Waiting for the next round (if applicable).")
        if round_num < repeat_count:
            print(f"Delaying for {delay_between_rounds} seconds before the next round.")
            await asyncio.sleep(delay_between_rounds)

    print(f"Completed all {repeat_count} rounds of forwarding.")
    await client.disconnect()

async def main():
    print(Fore.RED + pyfiglet.figlet_format("LEGITDEALS9"))
    print(Fore.GREEN + "Made by @Legitdeals9\n")

    credentials = load_credentials()
    
    if not credentials:
        print(Fore.RED + "No saved credentials found. Please enter the details for new sessions.")
    
    num_sessions = int(input("Enter how many sessions you want to log in: "))
    
    tasks = []
    clients = []

    for i in range(1, num_sessions + 1):
        session_key = f'session{i}'
        if session_key in credentials:
            api_id = credentials[session_key]['api_id']
            api_hash = credentials[session_key]['api_hash']
            phone_number = credentials[session_key]['phone_number']
            print(f"\nUsing saved credentials for session {i}.")
        else:
            print(f"\nEnter details for account {i}:")
            api_id = int(input(f"Enter API ID for session {i}: "))
            api_hash = input(f"Enter API hash for session {i}: ")
            phone_number = input(f"Enter phone number for session {i} (with country code): ")

            credentials[session_key] = {
                'api_id': api_id,
                'api_hash': api_hash,
                'phone_number': phone_number
            }
            save_credentials(credentials)

        session_name = f'session{i}'
        client = TelegramClient(session_name, api_id, api_hash)

        # Start the client and add it to the clients list
        await client.start(phone=phone_number)
        clients.append((client, session_name))

    # Start auto-sender for all logged-in clients
    for client, session_name in clients:
        tasks.append(auto_sender(client, session_name))

    await asyncio.gather(*tasks)

# Run the main function using asyncio
asyncio.run(main())
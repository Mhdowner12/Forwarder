import asyncio
import time
import json
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import init, Fore
import pyfiglet

# Initialize colorama for colored output
init(autoreset=True)

CREDENTIALS_FILE = 'credentials.json'

# Function to save credentials to a local file
def save_credentials(credentials):
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(credentials, f)

# Function to load credentials from the local file
def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    return {}

async def login_and_forward(api_id, api_hash, phone_number, session_name):
    # Initialize the Telegram client for each session
    client = TelegramClient(session_name, api_id, api_hash)

    # Connect and start the client
    await client.start(phone=phone_number)

    # Handle two-factor authentication
    try:
        if await client.is_user_authorized() is False:
            await client.send_code_request(phone_number)
            await client.sign_in(phone_number)

    except SessionPasswordNeededError:
        # Prompt for the two-factor authentication password
        password = input("Two-factor authentication enabled. Enter your password: ")
        await client.sign_in(password=password)

    # Get the last message from 'Saved Messages'
    saved_messages_peer = await client.get_input_entity('me')
    history = await client(GetHistoryRequest(
        peer=saved_messages_peer,
        offset_id=0,
        offset_date=None,
        add_offset=0,
        limit=1,  # Get only the last message
        max_id=0,
        min_id=0,
        hash=0
    ))

    if not history.messages:
        print("No messages found in 'Saved Messages'")
        return

    last_message = history.messages[0]

    # Ask how many times to send the message and delay between rounds after login
    repeat_count = int(input(f"How many times do you want to send the message to all groups for {session_name}? "))
    delay_between_rounds = int(input(f"Enter the delay (in seconds) between each round for {session_name}: "))

    # Loop for repeating the forwarding process based on the repeat_count
    for round_num in range(1, repeat_count + 1):
        print(f"\nStarting round {round_num} of forwarding messages to all groups for {session_name}.")

        # Get all dialogs (i.e., chats, groups, etc.)
        async for dialog in client.iter_dialogs():
            # Only check for group chats
            if dialog.is_group:
                group = dialog.entity
                try:
                    # Forward the last message to the group
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                except Exception as e:
                    print(Fore.RED + f"Failed to forward message to {group.title} using {session_name}: {str(e)}")

                # Add a 3-second delay between each group forwarding
                await asyncio.sleep(3)

        print(f"Completed round {round_num}. Waiting for the next round (if applicable).")

        # Delay after completing all groups before starting the next round (if not the last round)
        if round_num < repeat_count:
            print(f"Delaying for {delay_between_rounds} seconds before the next round.")
            await asyncio.sleep(delay_between_rounds)

    print(f"Completed all {repeat_count} rounds of forwarding.")

    # Disconnect the client after the task is done
    await client.disconnect()

async def main():
    # Display the banner with pyfiglet
    print(Fore.RED + pyfiglet.figlet_format("LEGITDEALS9"))
    print(Fore.GREEN + "Made by @Legitdeals9\n")

    # Load saved credentials or start with an empty dictionary
    credentials = load_credentials()

    num_sessions = int(input("Enter how many sessions you want to log in: "))

    tasks = []

    for i in range(1, num_sessions + 1):
        if f'session{i}' in credentials:
            # Use saved credentials if available
            api_id = credentials[f'session{i}']['api_id']
            api_hash = credentials[f'session{i}']['api_hash']
            phone_number = credentials[f'session{i}']['phone_number']
            print(f"\nUsing saved credentials for session {i}.")
        else:
            # Prompt for API credentials for each account
            print(f"\nEnter details for account {i}:")
            api_id = int(input(f"Enter API ID for session {i}: "))
            api_hash = input(f"Enter API hash for session {i}: ")
            phone_number = input(f"Enter phone number for session {i} (with country code): ")

            # Save the new credentials
            credentials[f'session{i}'] = {
                'api_id': api_id,
                'api_hash': api_hash,
                'phone_number': phone_number
            }
            save_credentials(credentials)

        # Define a unique session name for each account
        session_name = f'session{i}'

        # Add the login and forwarding task to the list
        tasks.append(login_and_forward(api_id, api_hash, phone_number, session_name))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

# Run the main function using asyncio
asyncio.run(main())
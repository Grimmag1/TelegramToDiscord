# Telegram to Discord Bridge Bot

A Python bot that forwards messages and media from Telegram channels/chats to Discord with an approval workflow.

## Features

- **Automatic Message Forwarding**: Monitors specified Telegram channels and forwards new messages to a Discord approval channel
- **Media Support**: Handles single files, images, and grouped media (albums)
- **Approval Workflow**: Messages require admin approval (✅ reaction) before being posted to the main Discord channel
- **Rich Embeds**: Displays message metadata including sender, chat name, and timestamp (GMT+1)
- **Grouped Media Handling**: Automatically batches grouped Telegram messages into a single Discord post

## How It Works

1. Bot monitors configured Telegram channels/chats
2. When a new message arrives, it's forwarded to a Discord **approval channel**
3. An admin reacts with ✅ to approve the message
4. The approved message is then posted to the **main Discord channel** for all users to see

## Prerequisites

- Python 3.8+
- Discord Bot Token
- Telegram API credentials (API_ID and API_HASH)
- Discord server with two channels (approval and main) and their ID

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

2. Install required packages:
```bash
pip install telethon discord.py python-dotenv
```

3. Create a `.env` file in the project root:
```env
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
TOKEN=your_discord_bot_token
PERSONAL_ID=your_telegram_user_id
```

## Configuration

### Getting Telegram Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Copy `api_id` and `api_hash` to your `.env` file

### Getting Discord Bot Token

1. Go to https://discord.com/developers/applications
2. Create a new application
3. Go to the "Bot" section
4. Click "Reset Token" and copy it to your `.env` file
5. Enable "Message Content Intent" under Privileged Gateway Intents

### Discord Channel Setup

In `main.py`, update these IDs with your Discord channel IDs:

```python
APPROVAL_CHANNEL_ID = 1234567890  # Channel where messages await approval
MAIN_CHANNEL_ID = 9876543210      # Channel where approved messages are posted
```

To get channel IDs:
1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click a channel → Copy ID

### Telegram Chat/Channel Setup

Update the chat IDs you want to monitor in `main.py`:

```python
@T_client.on(events.NewMessage(chats=[PERSONAL_ID, CHAT_ID_1, CHAT_ID_2]))
```

Currently configured chats are defined at the top of the file.

## Usage

Run the bot:

```bash
python main.py
```

On first run, Telegram will ask you to authenticate:
1. Enter your phone number
2. Enter the verification code sent to your Telegram app
3. If you have 2FA enabled, enter your password

### Approving Messages

1. Check the approval channel in Discord
2. Review the message content and sender information
3. React with ✅ to approve and post to the main channel
4. The message will automatically appear in the main channel

## File Structure

```
.
├── main.py           # Main bot script
├── .env              # Environment variables (not committed)
├── .gitignore        # Git ignore file
├── anon.session      # Telegram session file (auto-generated)
└── downloads/        # Temporary storage for media files
```

## Security Notes

- **Never commit** `.env` file or `anon.session` to version control
- The `.gitignore` file is configured to exclude sensitive files
- Regenerate your Discord bot token if it's ever exposed
- Keep your Telegram API credentials private

## Troubleshooting

### Bot doesn't respond
- Check that both clients are logged in successfully
- Verify channel IDs are correct
- Ensure the bot has appropriate permissions in Discord

### Media not downloading
- Check that the `downloads/` directory exists and is writable
- Verify you have enough disk space

### Telegram authentication fails
- Delete `anon.session` and run the bot again
- Verify API_ID and API_HASH are correct

## Dependencies

- `telethon` - Telegram client library
- `discord.py` - Discord API wrapper
- `python-dotenv` - Environment variable management

## License

This project is open source and available under the MIT License.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

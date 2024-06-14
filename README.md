# Discord Hunt Bot

This is a Python-based Discord bot that helps manage and coordinate hunting sessions within a Discord server. The bot provides several commands for users to claim a channel, accept claims, resume hunts, join the queue, and view the queue list.

# Use Case: Hunting Spot Claim Bot

## Overview

The Hunting Spot Claim Bot is designed to manage and automate the queuing system for various locations in a game or any other application where multiple users may need to claim specific spots or rooms. The bot helps streamline the process by allowing users to claim a spot through a simple command and displaying a timer for the duration of the claim.

## Features

- **Multiple Channels Setup**: Configure multiple channels with different location names corresponding to the spots or rooms in the game/application.
- **Claim Command**: Users can claim a location by using the `/claim` command in the respective channel.
- **Timer Display**: A timer shows the remaining time for the claim, updating every 30 seconds.
- **Notification**: Users receive notifications when they successfully claim a spot and when their time is running out.

## How It Works

1. **Setup Channels**: Admins create channels for each location that can be claimed in the game/application.
2. **Claiming a Spot**: A user enters the channel of the desired location and types the `/claim` command to claim that spot.
3. **Verification**: The bot verifies the claim and posts a confirmation message along with an image (optional) and the remaining time.
4. **Timer Updates**: The timer counts down from the specified duration, updating every 30 seconds.
5. **Claim Expiry**: Once the timer runs out, the spot becomes available for other users to claim.

## Example

Below is an example of how the bot functions in a Discord server:

### Screenshot
![image](https://github.com/Morrisk4y/medivia-claimbot/assets/72673660/d83e5ed0-c906-48ce-bb6f-ded58b1e79cd)


### Steps

1. **User Claims Spot**:
    - Command: `/claim`
    - Channel: `#hunting-spot-1`

2. **Bot Response**:
    ```plaintext
    medivia-verification-bot [BOT]
    You claimed the hunting spot with your image!

    Hunting Spot Timer
    Time Remaining: 02:59:30
    Claimed by: groggysh
    ```


By using the Hunting Spot Claim Bot, game administrators can ensure an organized and fair system for managing access to popular locations within the game, reducing conflicts and improving user experience.

## Commands

- `/claim` - Claims a Discord channel.
- `/acceptclaim` - Accepts the claim if the previous owner left.
- `/resume` - Resumes your hunt and refreshes the timer.
- `/next` - Puts yourself in the queue.
- `/listqueue` - Sends the list of players in the queue to the Discord channel you sent this command from.

## Files and Directory Structure

- `Dockerfile` - Contains the instructions to build the Docker image for the application.
- `LICENSE` - The license file for the application.
- `README.md` - This readme file.
- `app.py` - The main application code.
- `example.env` - Example environment configuration file.
- `requirements.txt` - List of Python dependencies required for the application.

## Building and Running the Application

### Prerequisites

- Docker
- Docker Compose (optional but recommended)
- Python 3.8+
- A Discord bot token

### Setting Up

1. **Clone the Repository**

   ```sh
   git clone https://github.com/yourusername/discord-hunt-bot.git
   cd discord-hunt-bot

### make sure to update the .env file you copied with your info

### Running the Application
- Using Docker
- cp example.env .env
- docker build -t discord-claim-bot .
- docker run --env-file .env -d discord-hunt-bot

### Without Docker
pip install -r requirements.txt
python app.py


### License

This project is licensed under the terms of the MIT license. See the LICENSE file for details.

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue.

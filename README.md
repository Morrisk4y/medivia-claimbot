# Discord Hunt Bot

This is a Python-based Discord bot that helps manage and coordinate hunting sessions within a Discord server. The bot provides several commands for users to claim a channel, accept claims, resume hunts, join the queue, and view the queue list.

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

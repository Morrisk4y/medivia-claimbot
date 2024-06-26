import discord
from discord.ext import commands
from discord.commands import Option
import asyncio
import os

# Load environment variables and setup bot
from dotenv import load_dotenv
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CLAIM_DURATION_SECONDS = int(os.getenv("CLAIM_DURATION_SECONDS", 3600))
RESUME_DURATION_SECONDS = int(os.getenv("RESUME_DURATION_SECONDS", 900))
ACCEPT_CLAIM_SECONDS = int(os.getenv("ACCEPT_CLAIM_SECONDS", 900))
GUILD_ID = int(os.getenv("GUILD_ID"))
PREFIX = os.getenv('PREFIX')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, description="Hunting Spot Bot")

# Global dictionaries to manage timers, queues, and the current owner
timers = {}
resume_timers = {}
acceptclaim_timers = {}
queues = {}
current_owner = {}

@bot.slash_command(name="claim", description="Claim a hunting spot")
async def claim(ctx, image: Option(discord.Attachment, description="Upload an image of the hunting spot", required=True)):
    channel_id = ctx.channel.id
    user_id = ctx.author.id

    # Check if the uploaded file is an image
    if not image.content_type.startswith('image/'):
        await ctx.respond("Please upload a valid image file.", ephemeral=True)
        return

    # Existing code for handling claims
    if channel_id in current_owner and current_owner[channel_id] == user_id:
        await ctx.respond("You are already the owner of this hunting spot.", ephemeral=True)
    elif channel_id in timers and not timers[channel_id]['task'].done():
        if user_id in queues.get(channel_id, []):
            await ctx.respond("You are already in the queue.", ephemeral=True)
        else:
            queues.setdefault(channel_id, []).append(user_id)
            await ctx.respond("This hunting spot is already claimed. You have been added to the queue.", ephemeral=True)
    else:
        message = await ctx.respond("You claimed the hunting spot with your image!", files=[await image.to_file()])
        initiate_claim_sequence(ctx, channel_id, user_id, message)

@bot.slash_command(name="next", description="Join the queue for the next hunting spot")
async def next(ctx):
    channel_id = ctx.channel.id
    user_id = ctx.author.id

    # Check if the user is already the owner
    if channel_id in current_owner and current_owner[channel_id] == user_id:
        await ctx.respond("You cannot join the queue because you are currently the owner of the hunting spot.", ephemeral=True)
    elif channel_id in queues and user_id in queues[channel_id]:
        await ctx.respond("You are already in the queue.", ephemeral=True)
    elif channel_id in current_owner:
        queues.setdefault(channel_id, []).append(user_id)
        await ctx.respond(f"{ctx.author.display_name} has been added to the queue.")
    else:
        await ctx.respond("No one has claimed the spot. Type /claim to claim the spot.", ephemeral=True)

@bot.slash_command(name="timer", description="Get the current timer for the hunting spot")
async def timer(ctx):
    channel_id = ctx.channel.id
    if channel_id in timers and not timers[channel_id]['task'].done():
        duration = timers[channel_id]['task']._coro.cr_frame.f_locals['duration']
        
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_display = f"{hours:02}:{minutes:02}:{seconds:02}"
        
        await ctx.respond(f"Time remaining for the current claim: {time_display}", ephemeral=True)
    else:
        await ctx.respond("There is no active timer for this channel.", ephemeral=True)


@bot.slash_command(name="listqueue", description="List all users currently in the queue for the hunting spot")
async def listqueue(ctx):
    channel_id = ctx.channel.id
    if channel_id in queues and queues[channel_id]:
        # Initialize the embed for the queue
        embed = discord.Embed(title="Queue for the Hunting Spot", description="Here are the users currently waiting:", color=discord.Color.blue())
        
        # Populate the embed with the queue
        for index, user_id in enumerate(queues[channel_id], start=1):
            user = await ctx.guild.fetch_member(user_id)  # Fetch the member from their ID
            embed.add_field(name=f"Position {index}", value=user.display_name, inline=False)  # Append each user with their position

        # Try sending the embed in a DM
        try:
            await ctx.author.send(embed=embed)
            await ctx.respond("I've sent you the queue list in a DM!", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("I couldn't send you a DM. Please check your privacy settings!", ephemeral=True)
    else:
        await ctx.respond("There are currently no users in the queue. Claim the spot with /claim!", ephemeral=True)



@bot.slash_command(name="acceptclaim", description="Accept the claim for the hunting spot")
async def acceptclaim(ctx, image: Option(discord.Attachment, description="Upload an image of the hunting spot", required=True)):
    channel_id = ctx.channel.id
    user_id = ctx.author.id

    # Check if accept claim timer is active for this user
    if channel_id in acceptclaim_timers and not acceptclaim_timers[channel_id]['task'].done():
        if current_owner.get(channel_id) == user_id:
            acceptclaim_timers[channel_id]['task'].cancel()  # Cancel existing timer
            await ctx.respond("You have successfully claimed the spot!")
            initiate_claim_sequence(ctx, channel_id, user_id, acceptclaim_timers[channel_id]['message'])
            del acceptclaim_timers[channel_id]
        else:
            await ctx.respond("It is not your turn to claim or you did not claim in time.", ephemeral=True)
    else:
        await ctx.respond("There is no active timer to accept, or it has already expired.", ephemeral=True)

@bot.slash_command(name="resume", description="Resume or extend your claim on the hunting spot")
async def resume(ctx, image: Option(discord.Attachment, description="Upload an image of the hunting spot", required=True)):
    channel_id = ctx.channel.id
    user_id = ctx.author.id

    # Check if resume timer is active for this user
    if channel_id in resume_timers and not resume_timers[channel_id]['task'].done():
        if current_owner.get(channel_id) == user_id:
            resume_timers[channel_id]['task'].cancel()  # Cancel existing timer
            await ctx.respond("Your claim timer has been resumed", ephemeral=True)
            initiate_claim_sequence(ctx, channel_id, user_id, resume_timers[channel_id]['message'])
            del resume_timers[channel_id]
        else:
            await ctx.respond("You are not the current owner of any claim.", ephemeral=True)
    else:
        await ctx.respond("There is no active timer to resume or it has already expired.", ephemeral=True)


@bot.slash_command(name="leave", description="Leave the queue or cancel your current claim")
async def leave(ctx):
    channel_id = ctx.channel.id
    user_id = ctx.author.id
    
    if channel_id in current_owner and current_owner[channel_id] == user_id:
        if channel_id in timers and timers[channel_id]['task']:
            timers[channel_id]['task'].cancel()  # Cancel the active timer
            old_message = timers[channel_id]['message']
            new_message = await create_new_embed(ctx, "Hunting Spot Available", "Player left the spawn. The spot is now available for claiming. If no one is in the queue", discord.Color.green())
            if isinstance(old_message, discord.Message):
                await old_message.delete()  # Delete the old embed
            timers[channel_id]['message'] = new_message  # Update the message reference
            del current_owner[channel_id]

        if queues[channel_id]:
            next_user_id = queues[channel_id].pop(0)
            next_user = await ctx.guild.fetch_member(next_user_id)
            current_owner[channel_id] = next_user_id
            await ctx.respond(f"{ctx.author.display_name} has left. {next_user.mention}, it's your turn to accept the claim.")
            timers[channel_id] = {
                'task': asyncio.create_task(accept_claim_timer(ctx, new_message, next_user_id)),
                'message': new_message
            }
        else:
            await ctx.respond("You have left the queue and no one else is in line.", ephemeral=True)
            if channel_id in timers:
                del timers[channel_id]
    else:
        if queues[channel_id] and user_id in queues[channel_id]:
            queues[channel_id].remove(user_id)
            await ctx.respond(f"{ctx.author.display_name}, you have been removed from the queue.", ephemeral=True)
        else:
            await ctx.respond("You are not currently owning or in the queue.", ephemeral=True)


async def create_new_embed(ctx, title, description, color, owner=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"Claimed by: {ctx.author.display_name}")
    return await ctx.send(embed=embed)
  
def initiate_claim_sequence(ctx, channel_id, user_id, message):
    print(f"Initiating claim sequence: channel_id={channel_id}, user_id={user_id}")
    current_owner[channel_id] = user_id

    if 'task' in timers.get(channel_id, {}):
        print(f"Cancelling existing timer for channel_id={channel_id}")
        timers[channel_id]['task'].cancel()

    timers[channel_id] = {
        'task': asyncio.create_task(handle_timer(ctx, message, CLAIM_DURATION_SECONDS, user_id)),
        'message': message
    }

    if channel_id not in queues:
        queues[channel_id] = []

    print(f"Claim sequence initiated: current_owner={current_owner[channel_id]}, timers={timers[channel_id]}")

async def handle_timer(ctx, message, duration, owner):
    channel_id = ctx.channel.id
    print(f"Starting timer for channel_id={channel_id}, owner={owner}, duration={duration} seconds")
    try:
        previous_message = message
        while duration > 0:
            await asyncio.sleep(30)
            duration -= 30
            remaining_time = max(duration, 0)  # Ensure the remaining time doesn't go negative

            # Calculate hours, minutes, and seconds
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_display = f"{hours:02}:{minutes:02}:{seconds:02}"

            print(f"Timer update for channel_id={channel_id}: {time_display} remaining")

            try:
                # Create a new embed message
                new_message = await create_new_embed(ctx, "Hunting Spot Timer", f"Time Remaining: {time_display}", discord.Color.blue(), owner)
                if isinstance(previous_message, discord.Message):
                    await previous_message.delete()
                previous_message = new_message
            except Exception as e:
                print(f"Exception occurred while creating new embed for channel_id={channel_id}: {e}")
        
        print(f"Timer ended for channel_id={channel_id}, starting resume timer")
        await start_resume_timer(ctx, previous_message, owner)
    except asyncio.CancelledError:
        print(f"Timer task for channel_id={channel_id} was cancelled.")
    except Exception as e:
        print(f"Unexpected exception in timer for channel_id={channel_id}: {e}")

async def start_resume_timer(ctx, message, owner):
    channel_id = ctx.channel.id
    duration = RESUME_DURATION_SECONDS
    owner_user = await message.guild.fetch_member(owner)
    await ctx.send(f"{owner_user.mention}, your resume timer is starting! type /resume to continue claiming the spawn")  # Correctly mention the owner
    await update_embed(message, "Resume Timer", f"Time to resume: {duration} seconds", discord.Color.red(), owner)
    resume_timers[channel_id] = {
        'task': asyncio.create_task(resume_timer(ctx, message, duration, owner)),
        'message': message
    }

async def resume_timer(ctx, message, duration, owner):
    channel_id = ctx.channel.id
    while duration > 0:
        await asyncio.sleep(10)
        duration -= 10
        await update_embed(message, "Resume Timer", f"Time to resume: {duration} seconds", discord.Color.red(), owner)

    if duration == 0 and channel_id in current_owner:
        del current_owner[channel_id]  # Remove the owner if they don't resume
        await update_embed(message, "Hunting Spot Available", "The resume period has ended. The spot is now available for claiming.", discord.Color.green(), None)
        if queues[channel_id]:
            await process_queue(ctx, message, channel_id)
        del resume_timers[channel_id]  # Clear the timer


async def accept_claim_timer(ctx, message, next_user_id):
    channel_id = ctx.channel.id
    duration = ACCEPT_CLAIM_SECONDS
    try:
        next_user_id = int(next_user_id)
        next_user = await ctx.guild.fetch_member(next_user_id)
        next_user_display_name = next_user.display_name if next_user else "Unknown User"

        await ctx.send(f"{next_user.mention}, you have {duration} seconds to /acceptclaim.")
        await update_embed(message, "Claim Timer", f"{next_user_display_name}, you have {duration} seconds to /acceptclaim.", discord.Color.orange(), next_user_id)

        acceptclaim_timers[channel_id] = {
            'task': asyncio.create_task(accept_claim_countdown(ctx, message, duration, next_user_id, next_user_display_name)),
            'message': message
        }

    except ValueError:
        await ctx.send("Invalid user ID. User IDs must be numeric.")
    except discord.NotFound:
        await ctx.send("User not found. Please ensure the user ID is correct.")


async def accept_claim_countdown(ctx, message, duration, next_user_id, next_user_display_name):
    channel_id = ctx.channel.id
    try:
        while duration > 0:
            await asyncio.sleep(10)
            duration -= 10

            new_message = await create_new_embed(ctx, "Claim Timer", f"{next_user_display_name}, you have {duration} seconds to /acceptclaim.", discord.Color.orange(), next_user_id)
            if isinstance(message, discord.Message):
                await message.delete()
            message = new_message
            acceptclaim_timers[channel_id]['message'] = message

        # Handle the scenario when the timer expires
        # You may need to add additional logic here
    except asyncio.CancelledError:
        print(f"Accept claim timer for channel_id={channel_id} was cancelled.")
    except Exception as e:
        print(f"Unexpected exception in accept claim timer for channel_id={channel_id}: {e}")


        
async def process_queue(ctx, message, channel_id):
    if queues[channel_id]:
        next_user_id = queues[channel_id].pop(0)
        next_user = await ctx.guild.fetch_member(next_user_id)  # Fetching the member # Prompting user
        # Start an accept claim timer for the next user
        timers[channel_id] = {
            'task': asyncio.create_task(accept_claim_timer(ctx, message, next_user_id)),
            'message': message
        }
        current_owner[channel_id] = next_user_id  # Update owner ID
    else:
        # If no one is in the queue to take the claim
        await update_embed(message, "Hunting Spot Available", "The resume period has ended. The spot is now available for claiming.", discord.Color.green(), None)
        del current_owner[channel_id]  # Remove the current owner as there is no queue


async def accept_claim_timer(ctx, message, next_user_id):
    channel_id = ctx.channel.id
    duration = ACCEPT_CLAIM_SECONDS
    try:
        next_user_id = int(next_user_id)
        next_user = await ctx.guild.fetch_member(next_user_id)
        next_user_display_name = next_user.display_name if next_user else "Unknown User"

        await ctx.send(f"{next_user.mention}, you have {duration} seconds to /acceptclaim.")

        # Create new embed and delete the old one
        new_message = await create_new_embed(ctx, "Claim Timer", f"{next_user_display_name}, you have {duration} seconds to /acceptclaim.", discord.Color.orange(), next_user_id)
        if isinstance(message, discord.Message):
            await message.delete()
        message = new_message

        acceptclaim_timers[channel_id] = {
            'task': asyncio.create_task(accept_claim_countdown(ctx, message, duration, next_user_id, next_user_display_name)),
            'message': message
        }
    except Exception as e:
        print(f"Exception occurred while starting accept claim timer for channel_id={channel_id}: {e}")




async def update_embed(message, title, description, color, owner_id=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if owner_id:
        owner = await message.guild.fetch_member(owner_id)
        owner_display_name = owner.display_name if owner else "Unknown Owner"
        embed.set_footer(text=f"Claim owned by: {owner_display_name}")
    await message.edit(embed=embed)
    

@bot.event
async def on_ready():
    print('Bot is ready.')

bot.run(DISCORD_TOKEN)
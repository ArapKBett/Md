import discord
from discord.ext import commands
import json
import logging
import asyncio
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    logger.error("config.json not found. Please create it with your token and settings.")
    exit(1)

# Bot setup
intents = discord.Intents.default()
intents.members = True  # Required to access server members
bot = commands.Bot(command_prefix=config['prefix'], self_bot=True, intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
    logger.info("Self-bot is ready. Use !massdm <message> to send DMs.")

@bot.command()
async def massdm(ctx, *, message):
    """
    Command to send a custom DM to all members in the server where the command is invoked.
    Usage: !massdm Hello, this is a test message!
    """
    if not ctx.guild:
        await ctx.send("This command must be used in a server.")
        return

    logger.info(f"Starting mass DM in server: {ctx.guild.name} ({ctx.guild.id})")
    success_count = 0
    fail_count = 0

    # Iterate through all members in the server
    for member in ctx.guild.members:
        # Skip the bot itself and other bots
        if member == bot.user or member.bot:
            continue

        try:
            # Send the DM
            await member.send(message)
            logger.info(f"Sent DM to {member.name} ({member.id})")
            success_count += 1

            # Delay to avoid rate limits (adjust as needed)
            await asyncio.sleep(2)  # 2 seconds between DMs

        except discord.Forbidden:
            logger.warning(f"Failed to DM {member.name} ({member.id}): DMs closed or blocked")
            fail_count += 1
        except discord.HTTPException as e:
            logger.error(f"Failed to DM {member.name} ({member.id}): {e}")
            fail_count += 1
            # Handle rate limit specifically
            if e.status == 429:
                retry_after = e.retry_after if hasattr(e, 'retry_after') else 5
                logger.warning(f"Rate limited. Waiting {retry_after} seconds.")
                await asyncio.sleep(retry_after)
        except Exception as e:
            logger.error(f"Unexpected error for {member.name} ({member.id}): {e}")
            fail_count += 1

        # Optional: Update status periodically
        if (success_count + fail_count) % 10 == 0:
            logger.info(f"Progress: {success_count} successful, {fail_count} failed")

    # Send summary to the user
    summary = f"Mass DM completed:\n- Successful: {success_count}\n- Failed: {fail_count}"
    await ctx.send(summary)
    logger.info(summary)

# Error handling for commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide a message to send. Usage: !massdm <message>")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"An error occurred: {error}")

# Run the bot
try:
    bot.run(config['token'], bot=False)  # bot=False indicates a self-bot
except discord.LoginFailure:
    logger.error("Invalid token. Please check your token in config.json.")
except Exception as e:
    logger.error(f"Failed to start bot: {e}")

import os
import discord
from discord import app_commands, Member
from discord.ext import commands
import datetime
import requests
import random as r

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create the bot instance
bot = commands.Bot(command_prefix='!', intents=intents)


def load_env_file(filepath='.env'):
    """Load variables from .env file into os.environ"""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found")
        return

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                # Split on first = sign
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    # Set in os.environ so it's accessible everywhere
                    os.environ[key.strip()] = value


# Load the variables
load_env_file()

# Now it will work with os.getenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT = os.getenv('DISCORD_CLIENT_ID')
URL = os.getenv('DISCORD_BOT_URL')

# Debug
if TOKEN:
    print("Token Found")
else:
    print("Token not found")
if CLIENT:
    print("Client found")
else:
    print("Client not found")
if URL:
    print("URL found")
    print(URL)
else:
    print("URL not found")


# ==================== EVENT HANDLERS ====================

@bot.event
async def on_ready():
    """Bot startup event"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(
    member="The member to kick",
    reason="Reason for kicking"
)
@app_commands.checks.has_permissions(kick_members=True)
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    """Kick a member using slash command"""

    # Check if BOT has permission to kick
    if not interaction.guild.me.guild_permissions.kick_members:
        await interaction.response.send_message("❌ I don't have permission to kick members!", ephemeral=True)
        return

    # Check if target is kickable (bot's role must be higher)
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I cannot kick this member (their role is equal or higher than mine)!",
            ephemeral=True
        )
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(
        f"✅ {member.mention} has been kicked. Reason: {reason or 'No reason provided'}"
    )


@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(
    member="The member to ban",
    reason="Reason for banning"
)
@app_commands.checks.has_permissions(ban_members=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    """Ban a member using slash command"""

    # Check if BOT has permission to ban
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("❌ I don't have permission to ban members!", ephemeral=True)
        return

    # Check if target is bannable
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I cannot ban this member (their role is equal or higher than mine)!",
            ephemeral=True
        )
        return

    await member.ban(reason=reason)
    await interaction.response.send_message(
        f"✅ {member.mention} has been banned. Reason: {reason or 'No reason provided'}"
    )


@bot.tree.command(name="unban", description="Unban a user from the server")
@app_commands.describe(
    user_id="The user ID to unban"
)
@app_commands.checks.has_permissions(ban_members=True)
async def slash_unban(interaction: discord.Interaction, user_id: str):
    """Unban a user using slash command"""

    # Check if BOT has permission to unban
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("❌ I don't have permission to unban members!", ephemeral=True)
        return

    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ {user.mention} has been unbanned.")
    except discord.NotFound:
        await interaction.response.send_message("❌ User not found or not banned.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to unban this user!", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid user ID!", ephemeral=True)


@bot.tree.command(name="mute", description="Timeout a member")
@app_commands.describe(
    member="The member to mute",
    duration="Duration in seconds (default 60)",
    reason="Reason for muting"
)
@app_commands.checks.has_permissions(moderate_members=True)
async def slash_mute(interaction: discord.Interaction, member: discord.Member, duration: int = 60, reason: str = None):
    """Mute (timeout) a member using slash command"""

    # Check if BOT has permission to timeout members
    if not interaction.guild.me.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ I don't have permission to timeout members!", ephemeral=True)
        return

    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I cannot mute this member (their role is equal or higher than mine)!",
            ephemeral=True
        )
        return

    duration_td = datetime.timedelta(seconds=duration)
    await member.timeout(duration_td, reason=reason)
    await interaction.response.send_message(
        f"✅ {member.mention} has been muted for {duration} seconds. Reason: {reason or 'No reason provided'}"
    )


@bot.tree.command(name="botperms", description="Check the bot's permissions in this server")
async def slash_botperms(interaction: discord.Interaction):
    """Check bot permissions using slash command"""
    bot_perms = interaction.guild.me.guild_permissions

    embed = discord.Embed(
        title="🤖 Bot Permissions",
        description="Here are my current permissions in this server:",
        color=discord.Color.blue()
    )

    important_perms = {
        "Administrator": bot_perms.administrator,
        "Kick Members": bot_perms.kick_members,
        "Ban Members": bot_perms.ban_members,
        "Manage Messages": bot_perms.manage_messages,
        "Manage Roles": bot_perms.manage_roles,
        "Manage Channels": bot_perms.manage_channels,
        "Moderate Members": bot_perms.moderate_members,
        "View Audit Log": bot_perms.view_audit_log,
    }

    for perm_name, has_perm in important_perms.items():
        status = "✅" if has_perm else "❌"
        embed.add_field(name=perm_name, value=status, inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Get information about this server")
async def slash_serverinfo(interaction: discord.Interaction):
    """Get server info using slash command"""
    guild = interaction.guild

    embed = discord.Embed(
        title=f"{guild.name} Server Info",
        color=discord.Color.blue()
    )
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Get information about a user")
@app_commands.describe(member="The member to get info about (leave empty for yourself)")
async def slash_userinfo(interaction: discord.Interaction, member: discord.Member = None):
    """Get user info using slash command"""
    member = member or interaction.user

    embed = discord.Embed(
        title=f"User Info - {member}",
        color=member.color
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)

    roles = [role.mention for role in member.roles[1:]]  # Skip @everyone
    if roles:
        embed.add_field(name="Roles", value=", ".join(roles), inline=False)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="speak", description="Make the bot send a message")
@app_commands.describe(text="The message you want the bot to send")
@app_commands.checks.has_permissions(send_messages=True)
async def slash_speak(interaction: discord.Interaction, text: str):
        """Make the bot speak in the channel"""

        # Send the message to the channel
        await interaction.channel.send(text)

        # Confirm to the user (only they can see this)
        await interaction.response.send_message(f"✅ Message sent!", ephemeral=True)


@bot.tree.command(name="gif", description="Search for a GIF")
@app_commands.describe(query="What GIF to search for")
async def slash_gif(interaction: discord.Interaction, query: str):
    """Search for a GIF using Tenor API"""

    # Defer the response since API calls take time
    await interaction.response.defer()

    # Tenor API (you'll need a free API key from https://tenor.com/gifapi)
    TENOR_API_KEY = os.getenv('TENOR_API_KEY')  # Add this to your .env file

    if not TENOR_API_KEY:
        await interaction.followup.send("❌ Tenor API key not configured!")
        return

    # Search GIFs
    url = f"https://tenor.googleapis.com/v2/search?q={query}&key={TENOR_API_KEY}&limit=1"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        if data['results']:
            gif_url = data['results'][0]['media_formats']['gif']['url']
            await interaction.followup.send(gif_url)
        else:
            await interaction.followup.send(f"❌ No GIFs found for '{query}'")
    else:
        await interaction.followup.send("❌ Failed to fetch GIF")


@bot.tree.command(name="dice", description="Roll a D6")
@app_commands.describe(text="Dice roll")
@app_commands.checks.has_permissions(send_messages=True)
async def slash_Dice(interaction: discord.Interaction, member: discord.Member, text: str):
    diceroll=r.randint(1,6)
    message=diceroll.__str__()
    await interaction.response.send_message(f"The dice number you rolled is {message} {member.mention}")





# ==================== ERROR HANDLERS ====================

@slash_kick.error
@slash_ban.error
@slash_unban.error
@slash_mute.error
async def permission_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle permission errors for moderation commands"""
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command!",
            ephemeral=True
        )


# ==================== PREFIX COMMANDS (LEGACY SUPPORT) ====================
# Keep these if you want both slash commands AND prefix commands

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def prefix_kick(ctx, member: discord.Member, *, reason=None):
    """Prefix command version of kick"""
    if not ctx.guild.me.guild_permissions.kick_members:
        await ctx.send("❌ I don't have permission to kick members!")
        return
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("❌ I cannot kick this member (their role is equal or higher than mine)!")
        return
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.mention} has been kicked. Reason: {reason or 'No reason provided'}")


@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def prefix_ban(ctx, member: discord.Member, *, reason=None):
    """Prefix command version of ban"""
    if not ctx.guild.me.guild_permissions.ban_members:
        await ctx.send("❌ I don't have permission to ban members!")
        return
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("❌ I cannot ban this member (their role is equal or higher than mine)!")
        return
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member.mention} has been banned. Reason: {reason or 'No reason provided'}")



# ==================== RUN BOT ====================

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Make sure your .env file contains DISCORD_TOKEN=your_token_here")
    else:
        print("Starting bot...")
        bot.run(TOKEN)
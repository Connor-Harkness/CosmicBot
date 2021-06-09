from discord.ext import commands
from discord import Embed
from datetime import datetime


class GuildModeration(commands.Cog):
    """Moderation commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group("guild")
    #@commands.has_any_role()
    async def GuildModerate(self, ctx):
        """Guild Moderation commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid Sub-command passed")
    
    @GuildModerate.command()
    async def info(self, ctx):
        """Shows available Guild Information"""
        now = datetime.now()
        footer_time = now.strftime("%H:%M:%S%p")
        text_channels = ctx.guild.text_channels
        voice_channels = ctx.guild.voice_channels
        members = ctx.guild.members
        owner = ctx.guild.owner
        server_icon = ctx.guild.icon_url_as(format = 'jpg')

        embed=Embed(title="Guild Information", description=f"Guild Users: {len(members)} | Guild Channels: {len(text_channels)+len(voice_channels)}")
        embed.set_author(name=f"{ctx.guild.name}")
        embed.set_thumbnail(url=server_icon)
        embed.add_field(name="Text Channels", value=len(text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(voice_channels), inline=True)
        embed.add_field(name="User Count", value=len(members), inline=True)
        embed.set_footer(text=f"Requested By: {ctx.author.name} @ {footer_time}")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(GuildModeration(bot))
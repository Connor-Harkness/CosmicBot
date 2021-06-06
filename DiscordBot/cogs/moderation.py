from discord.ext import commands




class Moderation:
    """Moderation commands"""

    def __init__(self, bot):
        self.bot = bot
        self.CONSTANTS = bot.CONSTANTS

    @commands.command
    @commands.has_any_role(self.CONSTANTS["Staff Role"])



    def setup(bot):
        bot.add_cog(Moderation(bot))
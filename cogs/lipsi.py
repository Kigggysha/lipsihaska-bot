import disnake
from disnake.ext import commands


class LipsiCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command()
    async def lipsi(inter):
        """Проверить работоспособность бота."""
        await inter.response.send_message("ha")


def setup(bot: commands.Bot):
    bot.add_cog(LipsiCommand(bot))
import disnake
from disnake.ext import commands


class JoinVoice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command()
    async def join(self, inter: disnake.ApplicationCommandInteraction):
        try:
            if inter.author.voice:
                channel = inter.author.voice.channel
                vc = await channel.connect()
                await inter.response.send_message(f"Присоединяюсь!")
            else :
                await inter.response.send_message(f"Вы должны находится в канале для того чтобы я смог присоединится к вам.")
        except:
            await inter.response.send_message(f"Бот уже находится в канале на этом сервере")

def setup(bot: commands.Bot):
    bot.add_cog(JoinVoice(bot))
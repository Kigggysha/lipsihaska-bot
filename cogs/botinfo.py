import disnake
from disnake.ext import commands


class BotInfoCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command()
    async def botinfo(inter):
        """Информация о боте."""
        await inter.response.send_message("БОТ РАБОТАЕТ В ТЕСТОВОМ РЕЖИМЕ ВСЕ БАГИ - @Kigggysha \nБот умеет: \nДавать ракушки - /daily \nНаписать информацию о вас - /info\n Вспроизводить треки из ютуба (ВАЖНО для всех манипуляций бот должен находится в голосовом канале) \n\n\nЧто готово/будет сделано: https://trello.com/b/Ng8ZYLTl/lipsihaskabot ")



def setup(bot: commands.Bot):
    bot.add_cog(BotInfoCommand(bot))
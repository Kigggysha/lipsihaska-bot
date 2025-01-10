# Imports of disnake
import disnake
from disnake.ext import commands
from disnake.ext.commands import UserInputError
from disnake.ui import View, Button

import os

import sqlite3

import datetime
from datetime import datetime, date, time

import random

from PIL import Image, ImageFilter, ImageDraw, ImageFont

import asyncio

from pytube import YouTube


TOKEN = 'MTEzMzUyNTUyNDUzMTEzMDQyOQ.GrIb3m.ch6aA9UAHcnr86N4QxVhshj-iFGygJ779btzzY'

# Создание экземпляра класса commands.Bot() и присваивание его в "bot".
intents = disnake.Intents.default()
intents.message_content = True
intents.messages = True

client = disnake.Client(intents=intents)
bot = commands.Bot()

#Подключение к базе данных 
con = sqlite3.connect("base.db")

# Словарь для отслеживания текущего трека для каждого сервера
current_song = {}
audio_connections = {}

# Когда бот будет готов, эта функция будет запущена.
@bot.event
async def on_ready():
    print("Бот готов!")

bot.load_extension("cogs.ping")
bot.load_extension("cogs.lipsi")
bot.load_extension("cogs.botinfo")
#bot.load_extension("cogs.join")

@bot.slash_command(guild_ids=[940204213030510613], description="Комманда чисто для ПП, не завидуем") #команда которая показывается только на пп
async def hipp(inter):
    await inter.response.send_message(f"Привет всем {inter.guild.member_count} участникам ПП")

@bot.slash_command(description="Добавить бота в аудиоканал")
async def join(inter):
    try:
        if inter.author.voice:
            channel = inter.author.voice.channel
            voice_connection = await channel.connect()

            audio_connections.setdefault(inter.guild_id, voice_connection)

            await inter.response.send_message(f"Присоединяюсь!")
        else:
            await inter.response.send_message(f"Вы должны находится в канале для того чтобы я смог присоединится к вам.")
    except:
        await inter.response.send_message(f"Бот уже находится в канале на этом сервере")

@bot.slash_command(description="Включить аудио")
async def play(ctx):
    if await is_bot_in_same_channel(ctx):
        try: 
            song_name = get_songs(ctx.guild.id)

            sound_path = f'sounds/{ctx.guild.id}/{song_name[0]}'

            #np = os.path.join(f'sounds/{ctx.guild.id}', 'now_playing')
            #os.mkdir(np)
            #shutil.copy2(sound_path, f'sounds/{ctx.guild.id}/now_playing/')

            #now_playing = f'sounds/{ctx.guild.id}/now_playing/{song_name[0]}'
            channel = ctx.author.voice.channel

            await play_sound(ctx, sound_path)
        except Exception as e:
            print(f"Произошла ошибка: {type(e).__name__}")
            print(f"Детали ошибки: {e}")
            await ctx.send('Нет файлов для воспроизведения.')
    else:
        await ctx.send('Бот должен находиться в одном с вами голосовом канале, чтобы воспроизвести звук.')

@bot.slash_command(description="Остановить аудио")
async def pause(ctx):
    # Проверяем, что бот находится в голосовом канале
    if await is_bot_in_same_channel_and_playing(ctx):
        await pause_sound(ctx)
        await ctx.send(f'Останавливаю аудио')
    else:
        await ctx.send('Бот должен находиться в одном с вами голосовом канале и воспроизводить аудио, чтобы остановить его.')

@bot.slash_command(description="Продолжить воспроизводить аудио")
async def resume(ctx):
    # Проверяем, что бот находится в голосовом канале
    if await is_bot_in_same_channel_and_paused(ctx):
        await resume_sound(ctx)
        await ctx.send(f'Продолжаю воспроизводить аудио')
    else:
        await ctx.send('Бот должен находиться в одном с вами голосовом канале и иметь остановленное аудио, чтобы продолжить воспроизводить его.')

@bot.slash_command(description="Добавить трек по ссылке в очередь")
async def add(ctx, link):
    await ctx.response.defer()
    # Проверяем, что бот находится в голосовом канале
    if await is_bot_in_same_channel(ctx):
        try: 
            index = len(get_songs(ctx.guild.id))
        except:
            index = 0

        try:
            song_name = download_audio(link, ctx.guild.id, index)
            await ctx.send(f'Добавляю {song_name} в список')
        except:
            await ctx.send(f'Трек превышает лимит в 15 минут либо не является ссылкой на видео с ютуба')
    else:
        await ctx.send('Бот должен находиться в одном с вами голосовом канале.')

@bot.slash_command(description="Следующий трек")
async def next(ctx):
    guild_id = ctx.guild.id
    # Проверяем, что бот находится в голосовом канале
    if await is_bot_in_same_channel_and_playing(ctx):
        next_song_number = current_song[guild_id] + 1
        current_song.pop(guild_id)
        current_song.setdefault(guild_id, next_song_number)
        try: 
            song_name = get_songs(guild_id)
            sound_path = f'sounds/{guild_id}/{song_name[current_song[guild_id]]}'
            channel = ctx.author.voice.channel

            #old_source = disnake.FFmpegPCMAudio(f'sounds/{guild_id}/{song_name[current_song[guild_id] - 1]}')
            #old_source.cleanup()

            # Воспроизводим звук
            audio_source = disnake.FFmpegPCMAudio(sound_path)
            current_song.setdefault(guild_id, 0)

            voice_connection = audio_connections[guild_id]
            voice_connection.pause()
            voice_connection.play(audio_source, after=lambda e: next_audio(ctx))

            await ctx.send(f'Включаю следующий трек')

            #os.remove(f'sounds/{guild_id}/{song_name[current_song[guild_id] - 1]}')
            #print(f'deleting: sounds/{guild_id}/{song_name[current_song[guild_id] - 1]}')
        except IndexError:
            current_song.pop(guild_id)
            current_song.setdefault(guild_id, 0)
            sound_path = f'sounds/{guild_id}/{song_name[current_song[guild_id]]}'

            audio_source = disnake.FFmpegPCMAudio(sound_path)
            current_song.setdefault(guild_id, 0)

            voice_connection = audio_connections[guild_id]
            voice_connection.pause()
            voice_connection.play(audio_source, after=lambda e: next_audio(ctx))

            await ctx.send(f'Очередь закончилась, начинаю заного.')
        except Exception as e:
            print(f"Произошла ошибка: {type(e).__name__}")
            print(f"Детали ошибки: {e}")
            await ctx.send('Нет файлов для воспроизведения.')
    else:
        await ctx.send('Бот должен находиться в одном с вами голосовом канале и воспроизводить аудио, чтобы переключить трек.')
    
@bot.slash_command(name="change_name", description="Смена имени")       #обновлено
async def changename(inter, new_name: str):
    if IsUserInDatabase(inter.author.id):
        cursor = con.cursor()
        sql_update = """Update usertable set BotUserName = ? where DiscordUserID = ?"""
        data = (new_name, inter.author.id)
        cursor.execute(sql_update, data)
        con.commit()
        cursor.close()
        await inter.response.send_message("Имя изменено!")
    else:
        AddUserToDB(user_id = inter.author.id, user_name = inter.author.name, chosed_name = new_name)
        await inter.response.send_message(f"Добро пожаловать {new_name} ваше имя изменено!")

@bot.slash_command(name = "visualinfo", description="Визуальное отображение вашей статистики")
async def info2(inter):
    await inter.response.defer()

    userInfoList = GetUserInfo(inter)

    inBotUserName = userInfoList[0]
    userShellsAmount = userInfoList[1]
    userLevel = userInfoList[2]
    xpToNextLevel = userInfoList[3]
    userXP = userInfoList[4]
    isUserXPMaxed = userInfoList[5]

    if await visualUserInfo(inter.author.id, inter.author.name, userXP, userLevel, userShellsAmount, xpToNextLevel, isUserXPMaxed) == 1:
        await inter.followup.send(file=disnake.File("images/temp/1.jpg"))

    else:
        await inter.followup.send("Произошла непредвиденная ошибка, если вы видите данное сообщение обратитесь к kigggysha в Discord", ephemeral=True) 

@bot.slash_command(name = "ava", description = "Обновить вашу аватарку")
async def updateAvatar(ctx):
    await ctx.send("Пожалуйста, отправьте изображение в следующем сообщении (При использовании команды на сервере ответьте на это сообщение).")
    def check(message):
        return message.author == ctx.author and message.attachments
    try:
        response = await bot.wait_for('message', check=check, timeout=60)  #бот ожидает сообщения с изображением
        attachment = response.attachments[0]

        if attachment.content_type.startswith('image'):
            await attachment.save(f"images/avatar/{ctx.author.id}.png") #сохранение изображение я виде пнг с названием из айди пользователя
            avatarImage = process_image(f"images/avatar/{ctx.author.id}.png")
            avatarImage.save(f"images/avatar/{ctx.author.id}.png")
            await ctx.send("Аватарка сохранена!")
    except asyncio.TimeoutError:
        await ctx.send("Истекло время ожидания для отправки изображения.")

@bot.slash_command(description="Получить ежедневную награду")                                                   #обновлено, но я очень хочу переписать содержимое
async def daily(inter):
    if IsUserInDatabase(inter.author.id):
        cursor = con.cursor()
        sql = "SELECT LastTimeCollected FROM usertable WHERE DiscordUserID = ?"                                 #извлекаем из базы время последнего сбора 
        val = (inter.author.id,)
        cursor.execute(sql, val)
        LastTime = cursor.fetchone()[0]
        cursor.close()

        if str(date.today()) !=  str(LastTime):                                                                 #если последняя дата получения не сегодня то
            cursor = con.cursor()
            sql = "SELECT MoneyAmount FROM usertable WHERE DiscordUserID = ?"                                   #извлекаем из базы количество монет пользователя
            cursor.execute(sql, val)

            money = cursor.fetchone()[0]                                                                        #записываем предыдущий баланс
            moneybefore = money
            money += random.randint(40, 150)                                                                    #добавляем к нему случайное число
            cursor.close()

            cursor = con.cursor()
            sql = "SELECT Experience FROM usertable WHERE DiscordUserID = ?"                                    #извлекаем из базы количество опыта пользователя
            cursor.execute(sql, val)
            xpBefore = cursor.fetchone()[0]  
            xp = xpBefore + random.randint(50, 200)
            cursor.close()

            cursor = con.cursor()
            sql_update = """Update usertable set MoneyAmount = ? where DiscordUserID = ?"""                     #обновляем базу с новым количеством денег
            data = (money, inter.author.id)
            cursor.execute(sql_update, data)

            sql_update = """Update usertable set Experience = ? where DiscordUserID = ?"""                      #обновляем базу с новым количеством опыта
            data = (xp, inter.author.id)
            cursor.execute(sql_update, data)

            sql_update = """Update usertable set LastTimeCollected = ? where DiscordUserID = ?"""               #обновляем базу с новой датой сбора
            data = (date.today(), inter.author.id)
            cursor.execute(sql_update, data)
            con.commit()
            cursor.close()

            await inter.response.send_message(f"Вы получили {money - moneybefore}🐚 ракушек и {xp - xpBefore} опыта")                   #пишем количество полученых денег

        else:                                                                                                   #если последняя дата получения сегодня то
            await inter.response.send_message(f"Вы уже получали ежедневную награду сегодня! Следующая награда через {getStrTimeToTomorrow()}")

    else:
        AddUserToDB(user_id = inter.author.id, user_name = inter.author.name, chosed_name = inter.author.name)  #добавляем пользователя в базу

        cursor = con.cursor()
        sql = "SELECT MoneyAmount FROM usertable WHERE DiscordUserID = ?"                                     #извлекаем из базы количество монет пользователя
        val = (inter.author.id,)
        cursor.execute(sql, val)
        money = cursor.fetchone()[0]                                                                          #записываем предыдущий баланс
        moneybefore = money
        money += random.randint(40, 150)                                                                      #добавляем к нему случайное число
        cursor.close()

        cursor = con.cursor()
        sql = "SELECT Experience FROM usertable WHERE DiscordUserID = ?"                                      #извлекаем из базы количество опыта пользователя
        cursor.execute(sql, val)
        xpBefore = cursor.fetchone()[0]  
        xp = xpBefore + random.randint(50, 200)
        cursor.close()

        cursor = con.cursor()
        sql_update = """Update usertable set MoneyAmount = ? where DiscordUserID = ?"""                       #обновляем базу с новым количеством денег
        data = (money, inter.author.id)
        cursor.execute(sql_update, data)

        sql_update = """Update usertable set Experience = ? where DiscordUserID = ?"""                        #обновляем базу с новым количеством опыта
        data = (xp, inter.author.id)
        cursor.execute(sql_update, data)

        sql_update = """Update usertable set LastTimeCollected = ? where DiscordUserID = ?"""                 #обновляем базу с новой датой сбора
        data = (date.today(), inter.author.id)
        cursor.execute(sql_update, data)
        con.commit()
        cursor.close()          

        await inter.response.send_message(f"Добро пожаловать {inter.author.name} ваша награда: {money - moneybefore}🐚 ракушек и {xp - xpBefore} опыта")

@bot.slash_command(description="Ваша информация")                       
async def info(inter):
    userInfoList = GetUserInfo(inter)

    inBotUserName = userInfoList[0]
    userShellsAmount = userInfoList[1]
    userLevel = userInfoList[2]
    xpToNextLevel = userInfoList[3]
    isUserXPMaxed = userInfoList[5]

    if not isUserXPMaxed:
        await inter.response.send_message(f"{inBotUserName} имеет {userShellsAmount}🐚 ракушек и {userLevel} уровень, до следующего уровня осталось {xpToNextLevel} опыта")
    else:
        await inter.response.send_message(f"{inBotUserName} имеет {userShellsAmount}🐚 ракушек и {userLevel} уровень, что на {xpToNextLevel} опыта больше чем максимальный уровень")
    
@bot.slash_command(description="Рулетка на ракушки")                    
async def rullete(inter, place_bet: int):
    if IsUserInDatabase(inter.author.id):
        cursor = con.cursor()
        val = (inter.author.id,)
        sql = "SELECT * FROM usertable WHERE DiscordUserID = ?"
        cursor.execute(sql, val)
        UserInfo = cursor.fetchone()
        UserMoneyRullete = UserInfo[4]
        if place_bet > UserInfo[4]:
            await inter.response.send_message("Недостаточно ракушек :(")
        elif place_bet == 0:
            await inter.response.send_message("Нельзя поставить 0 ракушек", ephemeral=True)
        else:
            view = RulleteButtons()
            view.UserIDForButtons = inter.author.id
            message = await inter.response.send_message("На что ставим?", view=view)
            # Wait for the View to stop listening for input...
            await view.wait()
            # Check the value to determine which button was pressed, if any.
            if view.value is None:
                await inter.followup.send("Превышено время ожидания", ephemeral=True)
            elif view.value == 1:
                #ставка на красное
                placed_bet_tuple = RulleteBet(place_bet, 1)
                if placed_bet_tuple[3] == 1:
                    colorEmoji = colorToEmoji({placed_bet_tuple[1]})
                    await inter.followup.send(f"Поздравляю! Ваш выигрыш - {placed_bet_tuple[0]}🐚 ракушек, выпало: {colorEmoji} - {placed_bet_tuple[2]}")
                    UserMoneyRullete = UserMoneyRullete + (placed_bet_tuple[0] - place_bet)
                    UpdateMoney(inter.author.id, UserMoneyRullete)
                else:
                    colorEmoji = colorToEmoji({placed_bet_tuple[1]})
                    await inter.followup.send(f"К сожалению вы проиграли {place_bet}🐚, выпало: {colorEmoji} - {placed_bet_tuple[2]}")
                    UserMoneyRullete = UserMoneyRullete - place_bet
                    UpdateMoney(inter.author.id, UserMoneyRullete)
            elif view.value == 2:
                #ставка на чёрное
                placed_bet_tuple = RulleteBet(place_bet, 2)
                if placed_bet_tuple[3] == 1:
                    colorEmoji = colorToEmoji({placed_bet_tuple[1]})
                    await inter.followup.send(f"Поздравляю! Ваш выигрыш - {placed_bet_tuple[0]}🐚 ракушек, выпало: {colorEmoji} - {placed_bet_tuple[2]}")
                    UserMoneyRullete = UserMoneyRullete + (placed_bet_tuple[0] - place_bet)
                    UpdateMoney(inter.author.id, UserMoneyRullete)
                else:
                    colorEmoji = colorToEmoji({placed_bet_tuple[1]})
                    await inter.followup.send(f"К сожалению вы проиграли {place_bet}🐚, выпало: {colorEmoji} - {placed_bet_tuple[2]}")
                    UserMoneyRullete = UserMoneyRullete - place_bet
                    UpdateMoney(inter.author.id, UserMoneyRullete)
            elif view.value == 0:
                #ставка на зелёное
                placed_bet_tuple = RulleteBet(place_bet, 0)
                if placed_bet_tuple[3] == 1:
                    colorEmoji = colorToEmoji({placed_bet_tuple[1]})
                    await inter.followup.send(f"Поздравляю! Ваш выигрыш - {placed_bet_tuple[0]}🐚 ракушек, выпало: {colorEmoji} - {placed_bet_tuple[2]}")
                    UserMoneyRullete = UserMoneyRullete + (placed_bet_tuple[0] - place_bet)
                    UpdateMoney(inter.author.id, UserMoneyRullete)
                else:
                    colorEmoji = colorToEmoji({placed_bet_tuple[1]})
                    await inter.followup.send(f"К сожалению вы проиграли {place_bet}🐚, выпало: {colorEmoji} - {placed_bet_tuple[2]}")
                    UserMoneyRullete = UserMoneyRullete - place_bet
                    UpdateMoney(inter.author.id, UserMoneyRullete)
            elif view.value == -1:
                await inter.followup.send(f"Отмена")
            # Once we're done, disable the buttons.
            for child in view.children:
                if isinstance(child, disnake.ui.Button):
                    child.disabled = True
            await inter.edit_original_message(view=view)
            placed_bet_tuple = None
            view.value = None
    else:
        AddUserToDB(user_id = inter.author.id, user_name = inter.author.name, chosed_name = inter.author.name)
        await inter.response.send_message(f"{inter.author.name} у вас нет ракушек.")

@bot.slash_command(description = "Колесо")                              
async def wheel(inter, place_bet: int):
    if IsUserInDatabase(inter.author.id):
        cursor = con.cursor()
        val = (inter.author.id,)
        sql = "SELECT * FROM usertable WHERE DiscordUserID = ?"
        cursor.execute(sql, val)
        UserInfo = cursor.fetchone()
        UserMoneyWheel = UserInfo[4]
        if place_bet > UserInfo[4]:
            await inter.response.send_message("Недостаточно ракушек :(")
        else:
            placed_bet_tuple = WheetBet(place_bet)
            ArrowDirectionStr = GetArrowDirection(placed_bet_tuple[1])
            UserMoneyWheel += (placed_bet_tuple[0] - place_bet)
            UpdateMoney(inter.author.id, UserMoneyWheel)
            await inter.response.send_message(f"Ваш выигрыш - {placed_bet_tuple[0]}  \n0.1 0.2 0.3 \n2.4 {ArrowDirectionStr} 0.5 \n1.7 1.5 1.2")
    else:
        AddUserToDB(user_id = inter.author.id, user_name = inter.author.name, chosed_name = inter.author.name)
        await inter.response.send_message(f"{inter.author.name} у вас нет ракушек.")
    placed_bet_tuple = 0

@bot.slash_command(name = "top", description="Топ по ракушкам")         
async def top_of_shells(inter):
    cursor = con.cursor()
    cursor.execute("SELECT BotUserName, MoneyAmount FROM usertable ORDER BY MoneyAmount DESC LIMIT 5")
    result = cursor.fetchall()
    topOfUsers = ""
    for row in result:
        name, value = row
        topOfUsers += (f"\nИмя: {name}, количество ракушек: {value}🐚")
    await inter.response.send_message(topOfUsers)

@bot.slash_command(description="Передать ракушки другому пользователю") 
async def send(inter, amount: int, receiver: disnake.User):
    if IsUserInDatabase(inter.author.id):
        cursor = con.cursor()
        val = (inter.author.id,)
        sql = "SELECT * FROM usertable WHERE DiscordUserID = ?"
        cursor.execute(sql, val)
        senderInfo = cursor.fetchone()
        senderMoneyAfterSend = senderInfo[4] - amount

        receiverID = receiver.id
        val = (receiverID,)
        sql = "SELECT * FROM usertable WHERE DiscordUserID = ?"
        cursor.execute(sql, val)
        receiverInfo = cursor.fetchone()
        receiverMoneyAfterSend = receiverInfo[4] + amount
        cursor.close()

        if amount > senderInfo[4]:
            await inter.response.send_message("У вас недостаточно ракушек :(")

        else:
            if IsUserInDatabase(receiverID):
                UpdateMoney(inter.author.id, senderMoneyAfterSend)
                UpdateMoney(receiverID, receiverMoneyAfterSend)
                await inter.response.send_message(f"Вы успешно передали {amount}🐚 ракушек пользователю <@{receiver.id}>")

            else:
                AddUserToDB(user_id = receiver.id, user_name = receiver.name, chosed_name = receiver.name)
                UpdateMoney(inter.author.id, senderMoneyAfterSend)
                UpdateMoney(receiverID, receiverMoneyAfterSend)
                await inter.response.send_message(f"Вы успешно передали {amount}🐚 ракушек пользователю <@{receiver.id}>")   
    else:
        AddUserToDB(user_id = inter.author.id, user_name = inter.author.name, chosed_name = inter.author.name)
        await inter.response.send_message(f"<@{inter.author.id}> у вас нет ракушек.")

class RulleteButtons(disnake.ui.View):

    def __init__(self):
        super().__init__(timeout=15.0)
        self.value: Optional[int] = None
        self.UserIDForButtons: Optional[int] = None

    @disnake.ui.button(label="Красное", style=disnake.ButtonStyle.red)
    async def red(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.UserIDForButtons == inter.author.id:
            await inter.response.send_message("Вы поставили на красное", ephemeral=True)
            self.value = 1
            self.stop()
        else:
            await inter.response.send_message("Не вы выбираете!", ephemeral=True)

    # This one is similar to the confirmation button except sets the inner value to `False`.
    @disnake.ui.button(label="Черное", style=disnake.ButtonStyle.grey)
    async def black(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.UserIDForButtons == inter.author.id:
            await inter.response.send_message("Вы поставили на чёрное", ephemeral=True)
            self.value = 2
            self.stop()
        else:
            await inter.response.send_message("Не вы выбираете!", ephemeral=True)

    @disnake.ui.button(label="Зелёное", style=disnake.ButtonStyle.green)
    async def green(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.UserIDForButtons == inter.author.id:
            await inter.response.send_message("Вы поставили на зелёное", ephemeral=True)
            self.value = 0
            self.stop()
        else:
            await inter.response.send_message("Не вы выбираете!", ephemeral=True)

    @disnake.ui.button(label="Отмена", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.UserIDForButtons == inter.author.id:
            await inter.response.send_message('Отменяем...', ephemeral=True)
            self.value = -1
            self.stop()
        else:
            await inter.response.send_message("Не вы выбираете!", ephemeral=True)

def process_image(image_path):
    try:
        # Открываем изображение
        image = Image.open(image_path)
        
        # Определяем минимальную сторону изображения
        min_side = min(image.width, image.height)
        
        # Вычисляем координаты для обрезки по центру
        left = (image.width - min_side) // 2
        upper = (image.height - min_side) // 2
        right = left + min_side
        lower = upper + min_side
        
        # Обрезаем изображение по центру
        cropped_image = image.crop((left, upper, right, lower))
        
        # Изменяем размер до 200x200 пикселей
        resized_image = cropped_image.resize((300, 300), Image.LANCZOS)
        
        return resized_image

    except Exception as e:
        print("Ошибка при обработке изображения:", e)
        return None

def squareToRoundImage(image):
    try:
        # Создаем новое изображение для обводки и обрезания
        output_image = Image.new('RGBA', (300, 300), (255, 255, 255, 0))
        mask = Image.new('L', (300, 300), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 300, 300), fill=255)
        # Обрезаем изображение по маске
        output_image.paste(image, (0, 0), mask=mask)
        return output_image
    except Exception as e:
        print("Ошибка при обработке изображения:", e)
        return None

def trapezoidCrop(image):
    blanc = Image.new('RGBA', (1200, 550), (255, 255, 255, 0))
    imageToCrop = image
    trap = Image.open("images/shapes/trapezoid.png")
    trap = trap.crop((0, 0, 1200, 550)) 
    imageToCrop = imageToCrop.crop((0, 0, 1200, 550))
    imageToCrop = imageToCrop.filter(ImageFilter.GaussianBlur(15))
    blanc.paste(imageToCrop, (0, 0), trap)
    return blanc

async def visualUserInfo(user_id: int, user_name: str, userXP: int, userLevel: int, userShellsAmount: int, xpToNextLevel: int, isUserXPMaxed):

    userInfoBanner = Image.open("images/background/juicy.png")
    blurredPart = trapezoidCrop(userInfoBanner)
    userInfoBanner.paste(blurredPart, (0, 0), blurredPart)

    try:
        #попытка загрузить аватарку, если не получается то загружаем дефолт
        try:
            userAvatarPicture = Image.open(f"images/avatar/{user_id}.png")
        except: 
            userAvatarPicture = Image.open("images/avatar/default.png")

        #обрабатываем аватарку, делая её круглой и добавляем обводку
        userAvatarPicture = squareToRoundImage(userAvatarPicture)
        outlineImage = Image.open("images/avatar/outline.png")
        outlineImage.paste(userAvatarPicture, (8, 8), userAvatarPicture)
        userInfoBanner.paste(outlineImage, (50, 28), outlineImage)

        #Добавляем никнейм пользователя
        font = ImageFont.truetype("font/Genshin_Impact.ttf", 96)
        drawer = ImageDraw.Draw(userInfoBanner)
        fill_color = (255, 255, 255)
        stroke_color = (0, 0, 0)
        drawer.text((414, 31), user_name, font = font, fill = fill_color, stroke_width = 2, stroke_fill = stroke_color)

        #Опыт + уровень
        if not isUserXPMaxed:
            font = ImageFont.truetype("font/Genshin_Impact.ttf", 48)
            drawer.text((526, 152), str(userXP) + " / " + str(xpToNextLevel + userXP), font = font, fill = fill_color, stroke_width = 2, stroke_fill = stroke_color)
            drawer.text((936, 151), str(userLevel) + " ур.", font = font, fill = fill_color, stroke_width = 2, stroke_fill = stroke_color)
        else:
            font = ImageFont.truetype("font/Genshin_Impact.ttf", 48)
            drawer.text((526, 152), str(userXP) + " /  MAX", font = font, fill = fill_color, stroke_width = 2, stroke_fill = stroke_color)
            drawer.text((936, 151), str(userLevel) + " ур.", font = font, fill = fill_color, stroke_width = 2, stroke_fill = stroke_color)

        #Количество ракушек
        font = ImageFont.truetype("font/Genshin_Impact.ttf", 60)
        drawer.text((500, 228), str(userShellsAmount) + " ", font = font, fill = fill_color, stroke_width = 2, stroke_fill = stroke_color)
        shell = Image.open("images/shell/sracushka.png")
        userInfoBanner.paste(shell, (415, 233), shell)

        #Время до след. дейлика
        drawer.text((48, 359), "До следующего дейлика ", font = font, fill = fill_color, stroke_width = 2, stroke_fill = stroke_color)
        font = ImageFont.truetype("font/Genshin_Impact.ttf", 48)

        delta = getTimeToTomorrow()
        hours = delta.days * 24 + delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60
        drawer.text((48, 439), f"{hours} часов {minutes} минут {seconds} секунд", font = font, fill = fill_color, stroke_width = 2, stroke_fill = stroke_color)

        rgb_userInfoBanner = userInfoBanner.convert('RGB')                                              #конвертируем в ргб без альфа канала для сохранения в jpg
        rgb_userInfoBanner.save("images/temp/1.jpg", quality=90)                                        #сохраняем как jpg т-к размер файла в несколько раз меньше
        return 1;
    except FileNotFoundError:
        return -1;

def AddUserToDB(user_id: int, user_name: str, chosed_name: str):
    cursor = con.cursor()
    cursor.execute("select * from usertable")
    iduser = len(cursor.fetchall())
    iduser += 1
    sql = "INSERT INTO usertable (ID, DiscordUserID, DiscordUserName, BotUserName, MoneyAmount, LastTimeCollected, Experience) VALUES (?, ?, ?, ?, ?, ?, ?)"
    val = (iduser, user_id, user_name, chosed_name, 0, date(1980, 1, 1), 0)
    cursor.execute(sql, val)
    con.commit()
    cursor.close()

def IsUserInDatabase(user_id: int):
    UserID = user_id
    cursor = con.cursor()
    cursor.execute("select * from usertable")
    UserAmount = len(cursor.fetchall())
    cursor.execute("select DiscordUserID from usertable")
    UserIDCheck = cursor.fetchall()
    counter = 0
    while counter != UserAmount +1: 
        if counter == UserAmount:
            return False
            break;
        elif UserIDCheck[counter][0] == user_id:
            return True
            break;
        counter += 1

def GetUserInfo(inter):
    if IsUserInDatabase(inter.author.id):
        cursor = con.cursor()
        val = (inter.author.id,)
        sql = "SELECT * FROM usertable WHERE DiscordUserID = ?"
        cursor.execute(sql, val)
        UserInfo = cursor.fetchone()
        con.commit()
        cursor.close()

        userXP = GetUserXP(UserInfo)

        currentLevelList = GetLevel(userXP)
        xpToNextLevel = currentLevelList[1]

        if userXP == 0 or userXP == (userXP + xpToNextLevel):
            currentLevelList = GetLevel(userXP + 1)
            xpToNextLevel = currentLevelList[1] + 1

        if currentLevelList[2] == 0:
            UserInfoList = (UserInfo[3], UserInfo[4], currentLevelList[0], xpToNextLevel, userXP, False)
            return UserInfoList

        elif currentLevelList[2] == 1:
            UserInfoList = (UserInfo[3], UserInfo[4], currentLevelList[0], currentLevelList[1], userXP, True)
            return UserInfoList
    else:
        AddUserToDB(user_id = inter.author.id, user_name = inter.author.name, chosed_name = inter.author.name)

        cursor = con.cursor()
        val = (inter.author.id,)
        sql = "SELECT * FROM usertable WHERE DiscordUserID = ?"
        cursor.execute(sql, val)
        UserInfo = cursor.fetchone()
        con.commit()
        cursor.close()

        userXP = GetUserXP(UserInfo)
        currentLevelList = GetLevel(userXP + 1)

        UserInfoList = (UserInfo[3], UserInfo[4], currentLevelList[0], currentLevelList[1] + 1, userXP, False)
        return UserInfoList

def RulleteBet(betAmount: int, betColor: int):
    RulleteBall = random.randint(0, 36)
    if (RulleteBall in (1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36) and betColor == 1):
        betAmount = int(betAmount * 1.8 + 1)
        RulleteTuple = (betAmount, colorCheck(RulleteBall), RulleteBall, 1)
        return RulleteTuple
    elif (RulleteBall in (2, 4, 6, 8, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35) and betColor == 2):
        betAmount = int(betAmount * 1.8 + 1)
        RulleteTuple = (betAmount, colorCheck(RulleteBall), RulleteBall, 1)
        return RulleteTuple
    elif RulleteBall == 0 and betColor == 0:
        betAmount = int(betAmount * 10 + 1)
        RulleteTuple = (betAmount, colorCheck(RulleteBall), RulleteBall, 1)
        return RulleteTuple
    else:
        betAmount = 0
        RulleteTuple = (betAmount, colorCheck(RulleteBall), RulleteBall, 0)
        return RulleteTuple

def colorCheck(num: int):
    if (num in (1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36)):
        return "красное"
    elif (num in (2, 4, 6, 8, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35)):
        return "чёрное"
    else:
        return "зелёное"

def colorToEmoji(color: str):
    if (list(color)[0] == "красное"):
        return "🟥"
    elif (list(color)[0] == "зелёное"):
        return "🟩"
    else:
        return "◼️"

def WheetBet(betAmount: int):
    WheelRoll = random.randint(1, 8)
    if WheelRoll == 1:
        betAmount = int(betAmount * 0.1)
        WheelTuple = (betAmount, WheelRoll)
        return WheelTuple
    elif WheelRoll == 2:
        betAmount = int(betAmount * 0.2)
        WheelTuple = (betAmount, WheelRoll)
        return WheelTuple
    elif WheelRoll == 3:
        betAmount = int(betAmount * 0.3)
        WheelTuple = (betAmount, WheelRoll)
        return WheelTuple
    elif WheelRoll == 4:
        betAmount = int(betAmount * 0.5)
        WheelTuple = (betAmount, WheelRoll)
        return WheelTuple
    elif WheelRoll == 5:
        betAmount = int(betAmount * 1.2)
        WheelTuple = (betAmount, WheelRoll)
        return WheelTuple
    elif WheelRoll == 6:
        betAmount = int(betAmount * 1.5)
        WheelTuple = (betAmount, WheelRoll)
        return WheelTuple
    elif WheelRoll == 7:
        betAmount = int(betAmount * 1.7)
        WheelTuple = (betAmount, WheelRoll)
        return WheelTuple
    elif WheelRoll == 8:
        betAmount = int(betAmount * 2.4)
        WheelTuple = (betAmount, WheelRoll)
        return WheelTuple

def GetArrowDirection(arrowDirection: int):
    if arrowDirection == 1:
        return "⇖"
    elif arrowDirection == 2:
        return "⇑"
    elif arrowDirection == 3:
        return "⇗"
    elif arrowDirection == 4:
        return "⇒"
    elif arrowDirection == 5:
        return "⇘"
    elif arrowDirection == 6:
        return "⇓"
    elif arrowDirection == 7:
        return "⇙"
    elif arrowDirection == 8:
        return "⇐"

def UpdateMoney(user_id: int, newMoneyAmount: int):
    cursor = con.cursor()
    sql_update = """Update usertable set MoneyAmount = ? where DiscordUserID = ?"""
    data = (newMoneyAmount, user_id)
    cursor.execute(sql_update, data)
    con.commit()
    cursor.close()

def GetLevel(user_xp_amount: int):
    cursor = con.cursor()
    cursor.execute("select * from LevelRequirements")
    levelsList = cursor.fetchall()
    con.commit()
    cursor.close()

    levelCounter = 0
    while user_xp_amount > levelsList[levelCounter][1]:
        levelCounter += 1
        if levelCounter == len(levelsList):
            break;

    if levelCounter == len(levelsList):
        xpOver = user_xp_amount - levelsList[levelCounter - 1][1]
        levelInfoList = (levelCounter, xpOver, 1)
        return levelInfoList
    else:
        xpToNext = levelsList[levelCounter][1] - user_xp_amount
        levelInfoList = (levelCounter, xpToNext, 0)
        return levelInfoList

def GetUserXP(UserInfo):
    return UserInfo[6]

def getTimeToTomorrow():
    tomorrow = datetime.combine(date.today(), time(23, 59, 59))
    a = tomorrow - datetime.today()                                                                     #считаем сколько осталось времни до завтра 0:00
    return a

def getStrTimeToTomorrow():
    tomorrow = datetime.combine(date.today(), time(23, 59, 59))
    a = str(tomorrow - datetime.today())                                                                #считаем сколько осталось времни до завтра 0:00
    index = a.find('.')
    return a[0 : (index)]

def download_audio(video_link, guild_id, queue_num):
    yt = YouTube(video_link)
    name = f'{queue_num}.mp3'
    if yt.length < 900:
        yt.streams.filter(only_audio = True).first().download(output_path = f'sounds/{guild_id}/',filename = name)
    else:
        raise NameError('TimeLimitExceeded')
    
    song_name = yt.streams[0].title
    return song_name

def get_songs(guild_id):
    songs_list = os.listdir(f'sounds/{guild_id}/')
    return songs_list

def is_user_channel_in_bot_voice_clients(ctx): #переписать для более эффективного поиска через словарь
    # if user channel is in bot connections return true
    try:
        author_vc = ctx.author.voice.channel
    except:
        return False

    for client_number in range(len(ctx.bot.voice_clients)):
        if ctx.bot.voice_clients[client_number].channel == ctx.author.voice.channel:
            return True
            break
    # if not return false
    return False

def is_bot_playing(ctx):
    voice_connection = audio_connections[ctx.guild.id]
    return voice_connection.is_playing()

def is_bot_paused(ctx):
    voice_connection = audio_connections[ctx.guild.id]
    return voice_connection.is_paused()

async def is_bot_in_same_channel(ctx):
    return len(ctx.bot.voice_clients) != 0 and is_user_channel_in_bot_voice_clients(ctx)

async def is_bot_in_same_channel_and_playing(ctx):
    return len(ctx.bot.voice_clients) != 0 and is_user_channel_in_bot_voice_clients(ctx) and is_bot_playing(ctx)

async def is_bot_in_same_channel_and_paused(ctx):
    return len(ctx.bot.voice_clients) != 0 and is_user_channel_in_bot_voice_clients(ctx) and is_bot_paused(ctx)

def next_audio(ctx):
    guild_id = ctx.guild.id

    next_song_number = current_song[guild_id] + 1

    current_song.pop(guild_id)
    current_song.setdefault(guild_id, next_song_number)

    try: 
        song_name = get_songs(guild_id)

        sound_path = f'sounds/{guild_id}/{song_name[current_song[guild_id]]}'

        # Воспроизводим звук
        audio_source = disnake.FFmpegPCMAudio(sound_path)
        current_song.setdefault(guild_id, 0)
        voice_connection = audio_connections[guild_id]
        voice_connection.play(audio_source, after=lambda e: next_audio(ctx))

        #os.remove(f'sounds/{guild_id}/{song_name[current_song[guild_id] - 1]}')
        #print(f'deleting: sounds/{guild_id}/{song_name[current_song[guild_id] - 1]}')
    except IndexError:
        current_song.pop(guild_id)
        current_song.setdefault(guild_id, 0)
        sound_path = f'sounds/{guild_id}/{song_name[current_song[guild_id]]}'

        audio_source = disnake.FFmpegPCMAudio(sound_path)
        current_song.setdefault(guild_id, 0)

        voice_connection = audio_connections[guild_id]
        voice_connection.pause()
        voice_connection.play(audio_source, after=lambda e: next_audio(ctx))
    except: # Оно удивительно ничего не делает при превышении лимита
        voice_connection = audio_connections[ctx.guild.id]
        voice_connection.pause()

async def play_sound(ctx, sound_path):
    audio_source = disnake.FFmpegPCMAudio(sound_path)
    current_song.setdefault(ctx.guild.id, 0)
    try:
        voice_connection = audio_connections[ctx.guild.id]
        voice_connection.play(audio_source, after=lambda e: next_audio(ctx))
        await ctx.send('Воспроизвожу аудио')
    except:
        await ctx.send('Бот уже воспроизводит аудио')

async def pause_sound(ctx):
    voice_connection = audio_connections[ctx.guild.id]
    voice_connection.pause()    

async def resume_sound(ctx):
    voice_connection = audio_connections[ctx.guild.id]
    voice_connection.resume()
    
# Войдите в Discord с помощью токена бота.
bot.run(TOKEN)
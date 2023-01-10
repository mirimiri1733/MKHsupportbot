import os
import re
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from dotenv import load_dotenv



application_id = "1062006450622300290"

load_dotenv()




intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, application_id=1062006450622300290)

    async def setup_hook(self):
        await self.add_cog(Cog(bot))

def check_mkh_guild(ctx: commands.Context):
    return ctx.guild.id == 1024581419097403412


class Cog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.config = {
            "default":{"ReactRoleEmoji":"📣", "HostRoleEmoji":"🏆"},
            827891370324656148:{"ReactRoleEmoji":"<:運営:983361088529764452>", "HostRoleEmoji":"<:shinkou:863668105100263435>"},
            }

        self.host_dic = {}
        self.data = []
        self.latest_msg = None

    def get_config(self, guild_id):
        try:
            return self.config[guild_id]
        except KeyError:
            return self.config["default"]

    def makemsg(self, data):
        msg = f"{data[0]}\n\n"
        for i in range(len(data)):
            if i == 0:
                continue
            if data[i] == False:
                show = "未申請"
            elif data[i] == True:
                show = "☑️申請済み"
            else:
                show = data[i]
            msg += f"{i}組 - {show}\n"
        dt_jst = datetime.utcnow() + timedelta(hours=9)
        msg += f"\nLast Update - {format(dt_jst, '%H:%M:%S')}"
        msg = f"```{msg}```"

        return msg

    # async def cog_command_error(self, ctx: commands.Context, error: Exception):
    #     if isinstance(error, commands.BotMissingPermissions):
    #         await ctx.send(f"`Error: Bot requires permission(s) to run this command.`\n{','.join(e for e in error.missing_permissions)}")
    #     elif isinstance(error, commands.MissingRole):
    #         await ctx.send(f"`Error: Following role is required to run this command.`\n{error.missing_role}")
    #     else:
    #         pass

    async def update_message(self):
        await self.latest_msg.edit(content=f"{self.makemsg(self.data)}")

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_role("運営")
    async def release(self, ctx: commands.Context):

        count = 0
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name="進行役")

        msg = await ctx.send("進行役のリセット中...")

        for member in guild.members:

            if role in member.roles:

                try:
                    await member.edit(nick="")
                    await member.remove_roles(role)
                    count += 1

                except discord.errors.Forbidden:
                    await ctx.send(f"上位の権限を持つユーザー(<@{member.id}>)を検出しました\n個別にニックネーム削除と進行役ロール解除を行ってください")     

        await msg.delete()
        await ctx.send(f"`{count}人の進行役のリセットが終了しました`")

    @commands.command()
    @commands.guild_only()
    @commands.has_role("運営")
    async def rm(self, ctx: commands.Context):
        embed = discord.Embed(title="参加者ロール / Participant Role")
        embed.description = "大会参加者は大会期間中このメッセージにリアクションを付け、ロールを取得してください。大会に関する通知を受け取ることが出来ます。リアクションを外すとロールも外されます。\n\nParticipants are encouraged to react to this message during the convention to obtain their rolls. You will receive notifications about the tournament. If you remove your reaction, your role will also be removed."
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction(self.get_config(ctx.guild.id)["ReactRoleEmoji"])

    @commands.command()
    @commands.guild_only()
    @commands.has_role("運営")
    async def y(self, ctx: commands.Context):
        target_word = "主催コピペ用"
        histories = [message async for message in ctx.channel.history(limit=None)]
        value_li = []
        for msg in histories:
            if target_word in msg.content:
                idx = msg.content.find(target_word)
                part = msg.content[idx+len(target_word):]
                value_li.insert(0, part)
        value = "".join(value_li).replace("\n", "", 1)
        with open("advancement.txt", "w", encoding="utf-8") as writer:
            writer.write(value)
        await ctx.send(file=discord.File(fp="advancement.txt"))
    
    @commands.command()
    @commands.guild_only()
    @commands.has_role("運営")
    async def mset(self, ctx: commands.Context):
        host_dic = {}
        target_word1 = "組"
        target_word2 = "★進"
        histories = [message async for message in ctx.channel.history(limit=None)]
        for msg in histories:
            if target_word1 in msg.content:
                rooms = msg.content.split("\n-\n")
                for room in rooms:
                    idx1 = room.find(target_word1)
                    idx2 = room.find(target_word2)
                    room_no = room[:idx1]
                    host_name = room[idx1+2:idx2]
                    host_dic[room_no] = host_name
        self.host_dic[ctx.guild.id] = host_dic
        await ctx.send("`メンション対象がセットされました`")

    @commands.command()
    @commands.guild_only()
    @commands.has_role("運営")
    async def mshow(self, ctx: commands.Context):
        msg = ""
        for i in range(len(self.host_dic[ctx.guild.id])):
            msg += f"{f'{int(i)+1}'} : {self.host_dic[ctx.guild.id][f'{int(i)+1}']}\n"
        await ctx.send(f"```{msg}```")

    @commands.command()
    @commands.guild_only()
    async def m(self, ctx: commands.Context, *room_no):
        msg = ""
        for i in room_no:
            host_name = self.host_dic[ctx.guild.id][i]
            mention = ctx.guild.get_member_named(host_name)
            msg += f"{mention.mention}\n"
        await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_role("運営")
    async def b(self, ctx: commands.Context, *category_names):
        
        guild = ctx.guild

        role_mkh = discord.utils.get(guild.roles, name="運営")
        role_shinkou = discord.utils.get(ctx.guild.roles, name="進行役")
        role_hosa = discord.utils.get(ctx.guild.roles, name="主催補佐")
        role_everyone = discord.utils.get(ctx.guild.roles, name="@everyone")

        round_list = [
        ["1回戦","2回戦","準決勝","決勝"],
        ["1回戦","2回戦","3回戦","準決勝","決勝"],
        ["1回戦","2回戦","3回戦","4回戦","準決勝","決勝"],
        ["1回戦","2回戦","3回戦","4回戦","準々決勝","準決勝","決勝"],
        ["1回戦","2回戦","3回戦","4回戦","5回戦","準々決勝","準決勝","決勝"],
        ["1回戦","2回戦","3回戦","4回戦","5回戦","6回戦","準々決勝","準決勝","決勝"]
        ]

        def check_author(msg: discord.Message):
            return ctx.author == msg.author

        def make_room_list(rooms, divisor):
            li = []
            count = 1
            for i in range(rooms//divisor):
                li.append(f"{count}-{count+divisor-1}組")
                count += divisor
            if count-1 != rooms:
                li.append(f"{count}-{rooms}組")
            return li

        for category_name in category_names:

            if category_name == "各組連絡用":
                await ctx.send("`各組連絡用の詳細設定`\n`総組数と除数を数字で入力してください 除数を入力しない場合は10になります`\n`ex. 100組を10毎にチャンネル作成する場合『100 10』を入力`")
                answer: discord.Message = await bot.wait_for("message", check=check_author, timeout=None)
                if " " in answer.content:
                    answer = answer.content.split(" ")
                    rooms = int(answer[0])
                    divisor = int(answer[1])
                else:
                    rooms = int(answer.content)
                    divisor = 10
                room_list = make_room_list(rooms, divisor)
                category = await guild.create_category("🟡各組連絡用", position=0)
                for i in room_list:
                    await category.create_text_channel(f"{i}")
                await ctx.send("`🟡各組連絡用を作成しました`")

            elif category_name == "組分け":
                await ctx.send("`組分けの詳細設定`\n`総回戦数を半角数字で入力してください`\n`ex. 1~4回戦+準々決+準決+決勝の場合『7』を入力`")
                rounds: discord.Message = await bot.wait_for("message", check=check_author, timeout=None)
                category = await guild.create_category("🟡組分け", position=0)
                for i in round_list[int(rounds.content)-4]:
                    await category.create_text_channel(name=f"{i}-組分け")
                await category.set_permissions(target=role_everyone, send_messages=False)
                await category.set_permissions(target=role_mkh, send_messages=True)
                await category.set_permissions(target=role_hosa, send_messages=True)
                await ctx.send("`🟡組分けを作成しました`")

            elif category_name == "試合結果":
                await ctx.send("`試合結果の詳細設定`\n`総回戦数を半角数字で入力してください`\n`ex. 1~4回戦+準々決+準決+決勝の場合,『7』を入力`")
                rounds: discord.Message = await bot.wait_for("message", check=check_author, timeout=None)
                category = await guild.create_category("🟡試合結果", position=0)
                
                for i in round_list[int(rounds.content)-4]:
                    await category.create_text_channel(name=f"{i}-試合結果")
                await category.set_permissions(target=role_everyone, send_messages=False)
                await category.set_permissions(target=role_mkh, send_messages=True)
                await category.set_permissions(target=role_hosa, send_messages=True)
                await category.set_permissions(target=role_shinkou, send_messages=True)
                await ctx.send("`🟡試合結果を作成しました`")

            elif "杯" in category_name:
                category = await guild.create_category(f"🟡{category_name}", position=0)
                channel = await category.create_text_channel(name="メイン掲示板")
                await channel.set_permissions(target=role_everyone, send_messages = False)
                await channel.set_permissions(target=role_mkh, send_messages = True)
                await channel.set_permissions(target=role_hosa, send_messages = True)
                await channel.set_permissions(target=role_shinkou, send_messages = True)

                channel = await category.create_text_channel(name="基本ルール")
                await channel.set_permissions(target=role_everyone, send_messages = False)
                await channel.set_permissions(target=role_mkh, send_messages = True)
                await channel.set_permissions(target=role_hosa, send_messages = True)

                channel = await category.create_text_channel(name="主催・運営一覧")
                await channel.set_permissions(target=role_everyone, send_messages = False)
                await channel.set_permissions(target=role_mkh, send_messages = True)
                await channel.set_permissions(target=role_hosa, send_messages = True)

                channel = await category.create_text_channel(name="進捗状況")
                await channel.set_permissions(target=role_everyone, send_messages = False)
                await channel.set_permissions(target=role_mkh, send_messages = True)
                await channel.set_permissions(target=role_hosa, send_messages = True)

                channel = await category.create_text_channel(name="通過人数")
                await channel.set_permissions(target=role_everyone, send_messages = False)
                await channel.set_permissions(target=role_mkh, send_messages = True)
                await channel.set_permissions(target=role_hosa, send_messages = True)
                
                await category.create_text_channel(name="一般連絡用")
                await category.create_text_channel(name="進行登録連絡用")
                await category.create_text_channel(name="参加登録")
                await ctx.send(f"`🟡{category_name}を作成しました`")

            else:
                await ctx.send(f"`当てはまる候補がありません`\n**〇〇〇杯,各組連絡用,組分け,試合結果**`から選んでください`")
    
    @commands.command()
    @commands.check(check_mkh_guild)
    @commands.guild_only()
    @commands.has_role("運営")
    async def p(self, ctx: commands.Context, rooms):
        if self.data == [] and self.latest_msg == None:
            self.data.append(f"{ctx.guild.id}")
            for i in range(int(rooms)):
                self.data.append(False)
            msg = await ctx.send(f"{self.makemsg(data=self.data)}")
            self.latest_msg = msg
        else:
            await ctx.send("データが残っています `!preset`で削除することで再作成できます")

    @commands.command()
    @commands.check(check_mkh_guild)
    @commands.guild_only()
    @commands.has_role("運営")
    async def ptrue(self, ctx: commands.Context, *rooms):
        for i in rooms:
            self.data[int(i)] = True
        await self.update_message()
        await ctx.send("`データを更新しました`", delete_after=10)

    @commands.command()
    @commands.check(check_mkh_guild)
    @commands.guild_only()
    @commands.has_role("運営")
    async def pfalse(self, ctx: commands.Context, *rooms):
        for i in rooms:
            self.data[int(i)] = False
        await self.update_message()
        await ctx.send("`データを更新しました`", delete_after=10)

    @commands.command()
    @commands.check(check_mkh_guild)
    @commands.guild_only()
    @commands.has_role("運営")
    async def preset(self, ctx: commands.Context):
        self.data = []
        self.latest_msg = None
        await ctx.send("`データをリセットしました`")

    @commands.Cog.listener()
    @commands.has_role("進行役")
    async def on_message(self, message: discord.Message):
        if message.guild.id != 827891370324656148:
            return
        if message.author.bot:
            return
        if self.data == []:
            return
        message.content = message.content.replace(" ", "")
        if "組" in message.content:
            if "申請" in message.content:
                if "遅れ" not in message.content:
                    room = re.match(r"[\d]+組", message.content)
                    room = room.group().replace("組", "")
                    self.data[int(room)] = True
                    print(f"room: {room}\n message: {message.content}")
                    await self.update_message()
            elif "<:shinsei:863668171134205953>" in message.content:
                room = re.match(r"[\d]+組", message.content)
                room = room.group().replace("組", "")
                self.data[int(room)] = True
                print(f"room: {room}\n message: {message.content}")
                await self.update_message()
        elif "room" in message.content:
            if "sent" in message.content:
                room = re.match(r"room[\d]+", message.content)
                room = room.group().replace("room", "")
                self.data[int(room)] = True
                print(f"room: {room}\n message: {message.content}")
                await self.update_message()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        if payload.member == bot.user:
            return

        emoji_react_role = self.get_config(payload.guild_id)["ReactRoleEmoji"]
        emoji_host_role = self.get_config(payload.guild_id)["HostRoleEmoji"]

        msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        if str(payload.emoji) == emoji_react_role:
            role_part = discord.utils.get(bot.get_guild(payload.guild_id).roles, name="参加者")

            if msg.embeds[0].title == "参加者ロール / Participant Role":
                member = await bot.get_guild(payload.guild_id).fetch_member(payload.user_id)
                await member.add_roles(role_part)

        elif str(payload.emoji) == emoji_host_role:
            role_mkh = discord.utils.get(bot.get_guild(payload.guild_id).roles, name="運営")
            role_shinkou = discord.utils.get(bot.get_guild(payload.guild_id).roles, name="進行役")
            role_hosa = discord.utils.get(bot.get_guild(payload.guild_id).roles, name="主催補佐")

            member = await bot.get_guild(payload.guild_id).fetch_member(payload.user_id)

            if role_mkh in member.roles or role_hosa in member.roles:
                
                await msg.author.add_roles(role_shinkou)
                if "★進" in msg.content:
                    if len(msg.content.split("★進")[0]) < 11:
                        await msg.author.edit(nick=f"{msg.content.split('★進')[0]}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):

        if payload.member == bot.user:
            return

        emoji_react_role = self.get_config(payload.guild_id)["ReactRoleEmoji"]

        if str(payload.emoji) == emoji_react_role:
            msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            role_part = discord.utils.get(bot.get_guild(payload.guild_id).roles, name="参加者")

            if msg.embeds[0].title == "参加者ロール / Participant Role":
                member = await bot.get_guild(payload.guild_id).fetch_member(payload.user_id)
                await member.remove_roles(role_part)

bot = Bot()


#@bot.event
#async def on_ready():
    #JST = timezone(timedelta(hours=+9), 'JST')
    #await bot.get_channel(980850254628945930).send(f"```[{datetime.now(JST).strftime('%H:%M:%S')}]\nGuilds: {len(bot.guilds)} Users: {len(bot.users)}```")


bot.run(os.environ["token"])






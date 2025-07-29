import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, ui
import random, json, aiohttp
from datetime import datetime
import pytz

# تحميل الإعدادات
with open("config.json", "r") as f:
    config = json.load(f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
admin_role_name = config["admin_role"]

# التحقق إذا العضو إداري
def is_admin(member: discord.Member):
    return any(role.name == admin_role_name for role in member.roles)

# ========= أوامر عامة (Slash) ========= #
@tree.command(name="ping", description="Check bot latency")
async def ping_cmd(interaction: Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

@tree.command(name="userinfo", description="Show user info")
async def userinfo(interaction: Interaction):
    user = interaction.user
    embed = Embed(title="User Info", color=discord.Color.blurple())
    embed.add_field(name="Username", value=user.name)
    embed.add_field(name="ID", value=user.id)
    embed.set_thumbnail(url=user.avatar)
    await interaction.response.send_message(embed=embed)

@tree.command(name="serverinfo", description="Show server info")
async def serverinfo(interaction: Interaction):
    guild = interaction.guild
    embed = Embed(title="Server Info", color=discord.Color.green())
    embed.add_field(name="Name", value=guild.name)
    embed.add_field(name="Members", value=guild.member_count)
    await interaction.response.send_message(embed=embed)

@tree.command(name="avatar", description="Show your avatar")
async def avatar(interaction: Interaction):
    user = interaction.user
    await interaction.response.send_message(user.avatar.url)

@tree.command(name="say", description="Make the bot say something")
@app_commands.describe(text="Text to say")
async def say_cmd(interaction: Interaction, text: str):
    await interaction.response.send_message(text)

# ========= أوامر إدارية (Slash) ========= #
@tree.command(name="kick", description="Kick a user (admin only)")
@app_commands.describe(member="Member to kick", reason="Reason for kick")
async def kick(interaction: Interaction, member: discord.Member, reason: str = "No reason"):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("You don't have permission.", ephemeral=True)
    await member.kick(reason=reason)
    await interaction.response.send_message(f"{member.mention} was kicked.")

@tree.command(name="ban", description="Ban a user (admin only)")
@app_commands.describe(member="Member to ban", reason="Reason for ban")
async def ban(interaction: Interaction, member: discord.Member, reason: str = "No reason"):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("You don't have permission.", ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"{member.mention} was banned.")

# نموذج إنشاء قوانين
class RulesModal(ui.Modal, title="Create Rules"):
    title_input = ui.TextInput(label="Title", max_length=100)
    rules_input = ui.TextInput(label="Rules (use \\n for new line)", style=discord.TextStyle.paragraph)
    color_input = ui.TextInput(label="Embed Color (hex)", placeholder="#3498db", required=False)

    async def on_submit(self, interaction: Interaction):
        try:
            color = int(self.color_input.value.replace("#", "0x"), 16)
        except:
            color = 0x3498db
        embed = Embed(title=self.title_input.value, description=self.rules_input.value.replace("\\n", "\n"), color=color)
        view = ui.View()
        view.add_item(ui.Button(label="Agree", style=discord.ButtonStyle.success))
        await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="create_rules", description="Create rules with a form (admin only)")
async def create_rules(interaction: Interaction):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("You don't have permission.", ephemeral=True)
    await interaction.response.send_modal(RulesModal())

# ========= نظام help تفاعلي ========= #
class HelpView(discord.ui.View):
    @discord.ui.select(
        placeholder="اختر قسم الأوامر",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="أوامر عامة", emoji="⚙️"),
            discord.SelectOption(label="أوامر إدارية", emoji="🛠️"),
            discord.SelectOption(label="ألعاب وترفيه", emoji="🎮"),
            discord.SelectOption(label="الوقت والطقس", emoji="⏰")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "أوامر عامة":
            embed = Embed(title="⚙️ أوامر عامة", color=discord.Color.blurple())
            embed.add_field(name="/ping", value="تحقق من استجابة البوت. يرسل زمن الاستجابة بالميلي ثانية.", inline=False)
            embed.add_field(name="/say", value="جعل البوت يقول شيئًا باستخدام النص الذي توفره.", inline=False)
            embed.add_field(name="/avatar", value="عرض الصورة الرمزية للمستخدم.", inline=False)
            embed.add_field(name="/userinfo", value="عرض معلومات عن المستخدم.", inline=False)
            embed.add_field(name="/serverinfo", value="عرض معلومات عن السيرفر.", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

        elif select.values[0] == "أوامر إدارية":
            embed = Embed(title="🛠️ أوامر إدارية", color=discord.Color.red())
            embed.add_field(name="/create_rules", value="إنشاء قوانين جديدة باستخدام نموذج تفاعلي.", inline=False)
            embed.add_field(name="/kick", value="طرد مستخدم من السيرفر. (الإدارة فقط)", inline=False)
            embed.add_field(name="/ban", value="حظر مستخدم من السيرفر. (الإدارة فقط)", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

        elif select.values[0] == "ألعاب وترفيه":
            embed = Embed(title="🎮 ألعاب وترفيه", color=discord.Color.gold())
            embed.add_field(name="!anime", value="إرسال صورة عشوائية لأنمي.", inline=False)
            embed.add_field(name="!cat", value="إرسال صورة لقطة عشوائية.", inline=False)
            embed.add_field(name="!8ball", value="اسأل كرة السحر 8 للحصول على إجابة عشوائية.", inline=False)
            embed.add_field(name="!dice", value="رمي النرد واختيار رقم عشوائي بين 1 و 6.", inline=False)
            embed.add_field(name="!rps", value="لعب لعبة حجر ورقة مقص ضد البوت.", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

        elif select.values[0] == "الوقت والطقس":
            embed = Embed(title="⏰ الوقت والطقس", color=discord.Color.blue())
            embed.add_field(name="/weather", value="عرض حالة الطقس في مدينة معينة.", inline=False)
            embed.add_field(name="/time", value="عرض الوقت في مدينة معينة.", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

@tree.command(name="help", description="Show all commands")
async def help_cmd(interaction: Interaction):
    embed = Embed(title="أوامر البوت", description="اختر الفئة التي تريد مشاهدة أوامرها.", color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True)

# ========= أوامر ترفيهية (Prefix) ========= #
@bot.command()
async def anime(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.waifu.pics/sfw/waifu") as r:
            data = await r.json()
            await ctx.send(data["url"])

@bot.command()
async def cat(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search") as r:
            data = await r.json()
            await ctx.send(data[0]["url"])

@bot.command()
async def dice(ctx):
    result = random.randint(1, 6)
    await ctx.send(f"لقد رميت النرد: **{result}**")

@bot.command()
async def rps(ctx):
    choice = random.choice(["حجر", "ورقة", "مقص"])
    await ctx.send(f"أنا اخترت: **{choice}**")

@bot.command()
async def _8ball(ctx, *, question):
    responses = ["نعم", "لا", "ربما", "بالتأكيد", "اسأل مرة أخرى لاحقًا"]
    await ctx.send(f"**السؤال:** {question}\n**الجواب:** {random.choice(responses)}")

# ========= أوامر الطقس والوقت ========= #
@bot.command()
async def weather(ctx, city: str):
    api_key = "your_api_key_here"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ar"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data.get("cod") != 200:
                await ctx.send("لم أتمكن من الحصول على بيانات الطقس.")
                return
            main = data["main"]
            weather_desc = data["weather"][0]["description"]
            temp = main["temp"]
            embed = Embed(title=f"حالة الطقس في {city}", color=discord.Color.blue())
            embed.add_field(name="الوصف", value=weather_desc, inline=False)
            embed.add_field(name="الحرارة", value=f"{temp}°C", inline=False)
            await ctx.send(embed=embed)

@bot.command()
async def time(ctx, city: str):
    timezone = pytz.timezone(city)
    time = datetime.now(timezone)
    time_str = time.strftime("%Y-%m-%d %H:%M:%S")
    embed = Embed(title=f"الوقت في {city}", description=f"الوقت الحالي: {time_str}", color=discord.Color.green())
    await ctx.send(embed=embed)

# ========= تشغيل البوت ========= #
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

bot.run(config["token"])
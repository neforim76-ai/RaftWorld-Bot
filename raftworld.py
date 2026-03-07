import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta
import asyncio
import json
import sys
import os
import random
import string
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Настройки бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ========== ID РОЛЕЙ ==========
ROLE_HELPER_ID = 1470073437660778710      # ID роли "Хелпер"
ROLE_TEAM_ID = 1470073679055421440        # ID роли "Команда проекта"
ROLE_GL_MODER_ID = 1470072994129907712    # ID роли "Гл.Модер"
ROLE_ST_MODER_ID = 1470073041286336696    # ID роли "Ст.Модер"
ROLE_MODER_ID = 1470073171448430712       # ID роли "Модер"
ROLE_KP_WATCHER_ID = 1470072849489330362  # ID роли "Смотрящий за кп"
ROLE_ADMIN_ID = 1470072210344509490       # ID роли "Админ"
ROLE_CSP_ID = 1470074139510440129         # ID роли "ЧСП"
ROLE_BAN_CSP_ID = 1474024500877201499     # ID роли для бана/ЧСП
ROLE_MUTED_ID = 1474027480107974769       # ID роли "Мут"
ROLE_BANNED_ID = 1474027681753595995      # ID роли "Бан"
ROLE_AUTO_JOIN_ID = 1474026223410614424   # ID роли для новых игроков
ROLE_APPLICATION_ID = 1474026223410614424 # ID роли "Заполнение заявки"

# ========== РОЛИ ДЛЯ ВАРНОВ ==========
ROLE_WARN_1_ID = 1474014701745602560      # ID роли "1 варн"
ROLE_WARN_2_ID = 1474433681769627728      # ID роли "2 варн"
ROLE_WARN_3_ID = 1474433541352984639      # ID роли "3/3 варнов"

# ========== ID КАНАЛОВ ==========
PRIVATE_CATEGORY_ID = 1474383930563100672  # Категория для личных каналов
LOG_CHANNEL_ID = 1474386900923191517       # Канал для логов
APPLICATION_CHANNEL_ID = 1468558816936329359  # Канал для заявок (СОЗДАЙ!)

# ========== ФАЙЛЫ ==========
WARNS_FILE = "warns.json"
APPLICATIONS_FILE = "applications.json"

# ========== СЛОВАРИ ==========
warns = {}
applications = {}
user_channels = {}
processing_users = set()

# ========== ФОРМА ЗАЯВКИ ==========
APPLICATION_TEMPLATE = """
**Пожалуйста, заполните данные по шаблону ниже:**

**1) Ваш Discord:** (Укажите имя, например: @47teu7)

**2) Ваш Telegram:** (Укажите @username)

**3) Ваше имя:** (Имя, которым к вам обращаться)

**4) Скриншот привилегий:** (Прикрепите скрин)

**5) Ваш возраст:** (Сколько лет)

**6) Опыт работы:** (Где работали раньше)

**7) Почему хотите к нам:** (Кратко)

Заранее спасибо!
"""

# ========== ЗАГРУЗКА/СОХРАНЕНИЕ ==========
def load_data():
    global warns, applications
    # Загрузка варнов
    if os.path.exists(WARNS_FILE):
        try:
            with open(WARNS_FILE, 'r', encoding='utf-8') as f:
                warns = json.load(f)
                warns = {int(k): v for k, v in warns.items()}
        except:
            warns = {}
    else:
        warns = {}
    
    # Загрузка заявок
    if os.path.exists(APPLICATIONS_FILE):
        try:
            with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                applications = json.load(f)
                applications = {int(k): v for k, v in applications.items()}
        except:
            applications = {}
    else:
        applications = {}

def save_warns():
    with open(WARNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(warns, f, ensure_ascii=False, indent=4)

def save_applications():
    with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(applications, f, ensure_ascii=False, indent=4)

# ========== ГЕНЕРАЦИЯ ДАННЫХ ==========
def generate_email(name):
    """Генерирует email на основе имени"""
    clean_name = name.lower().replace(' ', '.').replace('@', '')
    clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '.')
    domains = ["kp.raftworld.ru", "member.kp.ru", "team.kp.ru"]
    domain = random.choice(domains)
    return f"{clean_name}@{domain}"

def generate_password(length=10):
    """Генерирует случайный пароль"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ========== ЗАГРУЗКА КАНАЛОВ ==========
async def load_channels():
    for guild in bot.guilds:
        category = guild.get_channel(PRIVATE_CATEGORY_ID)
        if category and isinstance(category, discord.CategoryChannel):
            for channel in category.text_channels:
                if channel.name.startswith("📌┃"):
                    channel_name = channel.name[2:]
                    for member in guild.members:
                        clean_member = member.name.replace(" ", "_").replace(".", "").replace(",", "")
                        if clean_member.lower() in channel_name.lower() or member.name.lower() in channel_name.lower():
                            user_channels[member.id] = channel.id
                            break

# ========== СПИСКИ РОЛЕЙ ==========
EXCLUDED_AUTO_ROLES = [
    ROLE_HELPER_ID, ROLE_TEAM_ID, ROLE_GL_MODER_ID, ROLE_ST_MODER_ID,
    ROLE_MODER_ID, ROLE_KP_WATCHER_ID, ROLE_ADMIN_ID, ROLE_CSP_ID,
    ROLE_MUTED_ID, ROLE_BANNED_ID, ROLE_BAN_CSP_ID,
    ROLE_WARN_1_ID, ROLE_WARN_2_ID, ROLE_WARN_3_ID
]

ALLOWED_ROLES_FOR_PROMOTION = [
    ROLE_KP_WATCHER_ID, ROLE_MODER_ID, ROLE_ST_MODER_ID,
    ROLE_GL_MODER_ID, ROLE_ADMIN_ID
]

ALLOWED_ROLES_FOR_BAN_CSP = [ROLE_BAN_CSP_ID, ROLE_ADMIN_ID]

ALLOWED_ROLES_FOR_WARNS = [
    ROLE_KP_WATCHER_ID, ROLE_MODER_ID, ROLE_ST_MODER_ID,
    ROLE_GL_MODER_ID, ROLE_BAN_CSP_ID, ROLE_ADMIN_ID
]

ROLES_CAN_SEE_PRIVATE_CHANNELS = [ROLE_GL_MODER_ID, ROLE_ADMIN_ID]

# ========== СОБЫТИЯ ==========
@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} успешно запущен!')
    print(f'📋 Серверов: {len(bot.guilds)}')
    print(f'👥 Команды загружены: !accept, !повышение, !бан, !чсп, !снят, !мут, !размут, !варн, !варны, !снятьварны')
    print(f'📝 Категория для личных каналов: {PRIVATE_CATEGORY_ID}')
    print(f'📋 Канал логов: {LOG_CHANNEL_ID}')
    print(f'📝 Канал заявок: {APPLICATION_CHANNEL_ID}')
    load_data()
    await load_channels()
    print(f'📊 Загружено варнов: {len(warns)}')
    print(f'📊 Загружено заявок: {len(applications)}')
    await bot.change_presence(activity=discord.Game(name="RaftWorld » KP | !варн"))

@bot.event
async def on_member_join(member):
    """При заходе нового игрока"""
    try:
        # Выдаем роль ожидания
        auto_role = member.guild.get_role(ROLE_AUTO_JOIN_ID)
        if auto_role:
            await member.add_roles(auto_role, reason="Новый игрок")
        
        # Отправляем приветствие в ЛС
        embed = discord.Embed(
            title="🎉 Добро пожаловать на RaftWorld KP!",
            description=f"Привет, {member.mention}!\n\n"
                       f"Для получения доступа к серверу, заполните заявку в канале **📝-заполнение-заявки**\n\n"
                       f"**Шаблон заявки:**\n{APPLICATION_TEMPLATE}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="RaftWorld » KP")
        
        try:
            await member.send(embed=embed)
        except:
            pass
        
        # Логируем
        await log_to_channel(
            guild=member.guild,
            title="🆕 НОВЫЙ УЧАСТНИК",
            description=f"{member.mention} зашел на сервер\nID: {member.id}",
            color=discord.Color.green()
        )
        
    except Exception as e:
        print(f"❌ Ошибка при приветствии: {e}")

@bot.event
async def on_message(message):
    """Отслеживаем сообщения в канале заявок"""
    if message.author.bot:
        return
    
    # Проверяем, что сообщение в канале заявок
    if message.channel.id == APPLICATION_CHANNEL_ID:
        await check_application(message)
    
    await bot.process_commands(message)

# ========== ПРОВЕРКА ЗАЯВОК ==========
async def check_application(message):
    """Проверяет заявку на соответствие шаблону"""
    content = message.content
    author = message.author
    
    # Проверяем наличие всех пунктов
    has_all_points = (
        "1)" in content and 
        "2)" in content and 
        "3)" in content and 
        "4)" in content and 
        "5)" in content and 
        "6)" in content and 
        "7)" in content
    )
    
    if not has_all_points:
        # Неправильный формат
        warning = await message.channel.send(
            f"{author.mention} ❌ Неправильный формат заявки!\n"
            f"Используй шаблон:\n{APPLICATION_TEMPLATE}"
        )
        await asyncio.sleep(10)
        await warning.delete()
        await message.delete()
        return
    
    # Парсим данные из заявки
    lines = content.split('\n')
    data = {}
    
    for line in lines:
        line = line.strip()
        if "1)" in line:
            data['discord'] = line.split("1)")[-1].strip().replace('**', '').replace('@', '')
        elif "2)" in line:
            data['telegram'] = line.split("2)")[-1].strip().replace('**', '').replace('@', '')
        elif "3)" in line:
            data['name'] = line.split("3)")[-1].strip().replace('**', '')
        elif "4)" in line:
            data['screenshot'] = "Есть" if message.attachments else "Нет"
        elif "5)" in line:
            data['age'] = line.split("5)")[-1].strip().replace('**', '')
        elif "6)" in line:
            data['experience'] = line.split("6)")[-1].strip().replace('**', '')
        elif "7)" in line:
            data['reason'] = line.split("7)")[-1].strip().replace('**', '')
    
    # Проверяем наличие скриншота
    if not message.attachments:
        warning = await message.channel.send(
            f"{author.mention} ❌ Вы не прикрепили скриншот!"
        )
        await asyncio.sleep(10)
        await warning.delete()
        await message.delete()
        return
    
    # Сохраняем заявку
    await save_application(author, data, message.attachments[0].url if message.attachments else None)
    
    # Отмечаем заявку как принятую
    await message.add_reaction('✅')
    await message.add_reaction('📝')
    
    # Отправляем подтверждение
    confirm = await message.channel.send(f"{author.mention} ✅ Заявка принята! Ожидайте решения администрации.")
    await asyncio.sleep(5)
    await confirm.delete()

async def save_application(member, data, screenshot_url):
    """Сохраняет заявку и отправляет данные"""
    
    # Генерируем email и пароль
    email = generate_email(data.get('name', member.name))
    password = generate_password(12)
    
    # Сохраняем в JSON
    applications[member.id] = {
        "user_id": member.id,
        "discord": data.get('discord'),
        "telegram": data.get('telegram'),
        "name": data.get('name'),
        "age": data.get('age'),
        "experience": data.get('experience'),
        "reason": data.get('reason'),
        "email": email,
        "password": password,
        "screenshot": screenshot_url,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "status": "pending"
    }
    
    save_applications()
    
    # Отправляем данные пользователю в ЛС
    try:
        embed = discord.Embed(
            title="📋 Ваша заявка принята!",
            description=f"Спасибо, {data.get('name')}!\n\n"
                       f"**Ваши данные для входа на сайт:**\n"
                       f"📧 Email: `{email}`\n"
                       f"🔑 Пароль: `{password}`\n\n"
                       f"После одобрения заявки вы сможете войти на сайт.\n"
                       f"Ожидайте решения администрации.",
            color=discord.Color.green()
        )
        embed.set_footer(text="RaftWorld » KP")
        await member.send(embed=embed)
    except:
        pass
    
    # Уведомляем админов в лог-канал
    guild = member.guild
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    
    if log_channel:
        admin_embed = discord.Embed(
            title="📋 НОВАЯ ЗАЯВКА",
            description=f"**Пользователь:** {member.mention}\n"
                       f"**Discord:** @{data.get('discord')}\n"
                       f"**Telegram:** @{data.get('telegram')}\n"
                       f"**Имя:** {data.get('name')}\n"
                       f"**Возраст:** {data.get('age')}\n"
                       f"**Опыт:** {data.get('experience')}\n"
                       f"**Причина:** {data.get('reason')}\n"
                       f"**[Скриншот]({screenshot_url})**\n\n"
                       f"**Email:** {email}\n"
                       f"**Пароль:** ||{password}||\n\n"
                       f"Для принятия: `!accept {member.mention}`",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        await log_channel.send(embed=admin_embed)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
async def get_member_from_args(ctx, args):
    """Получает участника из аргументов команды"""
    if len(args) > 0:
        if len(ctx.message.mentions) > 0:
            return ctx.message.mentions[0]
        
        arg = args[0].strip('<@!>')
        try:
            member = await ctx.guild.fetch_member(int(arg))
            if member:
                return member
        except:
            pass
        
        for member in ctx.guild.members:
            if arg.lower() in member.name.lower() or (member.nick and arg.lower() in member.nick.lower()):
                return member
    
    if ctx.message.reference:
        try:
            replied = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            return replied.author
        except:
            pass
    
    return None

async def log_to_channel(guild, title, description, color=discord.Color.blue()):
    """Логирование в канал"""
    if not LOG_CHANNEL_ID:
        return
    
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if not log_channel or not isinstance(log_channel, discord.TextChannel):
        return
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    
    await log_channel.send(embed=embed)

async def create_private_channel(member, source="unknown", app_data=None):
    """Создает личный канал для участника"""
    try:
        print(f"🔧 Создание канала для {member.name}")
        
        category = member.guild.get_channel(PRIVATE_CATEGORY_ID)
        if not category:
            for cat in member.guild.categories:
                if "личные" in cat.name.lower():
                    category = cat
                    break
            if not category:
                category = await member.guild.create_category("🔒 Личные каналы")
        
        clean_name = member.name.replace(" ", "_")[:20]
        channel_name = f"📌┃{clean_name}"
        
        # Проверяем, нет ли уже канала
        for channel in category.text_channels:
            if member.name.lower() in channel.name.lower():
                user_channels[member.id] = channel.id
                return channel
        
        # Настраиваем права
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True
            ),
            member.guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True
            )
        }
        
        for role_id in ROLES_CAN_SEE_PRIVATE_CHANNELS:
            role = member.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            reason=f"Личный канал для {member.name}"
        )
        
        user_channels[member.id] = channel.id
        
        # Приветствие
        if app_data:
            embed_desc = f"Привет, {member.mention}!\n\n"
            embed_desc += f"**Ваши данные для входа на сайт:**\n"
            embed_desc += f"📧 Email: `{app_data.get('email')}`\n"
            embed_desc += f"🔑 Пароль: `{app_data.get('password')}`\n\n"
            embed_desc += f"**Информация из заявки:**\n"
            embed_desc += f"👤 Имя: {app_data.get('name')}\n"
            embed_desc += f"💬 Discord: @{app_data.get('discord')}\n"
            embed_desc += f"📱 Telegram: @{app_data.get('telegram')}\n"
            embed_desc += f"📅 Возраст: {app_data.get('age')}\n"
            embed_desc += f"💼 Опыт: {app_data.get('experience')}\n"
            embed_desc += f"❓ Причина: {app_data.get('reason')}"
        else:
            embed_desc = f"Привет, {member.mention}!\n\n"
            embed_desc += f"Это ваш личный канал команды проекта.\n"
            embed_desc += f"**Что можно делать:**\n"
            embed_desc += f"• Скидывать док-ва\n"
            embed_desc += f"• Делиться файлами\n"
            embed_desc += f"• Отправлять отчеты\n\n"
            embed_desc += f"**Доступно для:**\n"
            embed_desc += f"• {member.mention} (вы)\n"
            embed_desc += f"• Гл.Модер\n"
            embed_desc += f"• Администрация"
        
        embed = discord.Embed(
            title="🎉 Добро пожаловать в личный канал!",
            description=embed_desc,
            color=discord.Color.blue()
        )
        embed.set_footer(text="RaftWorld » KP")
        
        welcome_msg = await channel.send(embed=embed)
        await welcome_msg.pin(reason="Закрепленное приветствие")
        
        await log_to_channel(
            guild=member.guild,
            title="📝 СОЗДАНИЕ КАНАЛА",
            description=f"Создан личный канал для {member.mention}\nКанал: {channel.mention}"
        )
        
        return channel
        
    except Exception as e:
        print(f"❌ Ошибка создания канала: {e}")
        return None

async def delete_private_channel(member):
    """Удаляет личный канал пользователя"""
    try:
        if member.id in user_channels:
            channel = member.guild.get_channel(user_channels[member.id])
            if channel:
                channel_name = channel.name
                await channel.delete(reason=f"Удаление канала {member.name}")
                del user_channels[member.id]
                
                await log_to_channel(
                    guild=member.guild,
                    title="🗑️ УДАЛЕНИЕ КАНАЛА",
                    description=f"Удален личный канал {channel_name} для {member.mention}"
                )
                return True
    except Exception as e:
        print(f"❌ Ошибка удаления канала: {e}")
    return False

async def update_warn_role(member):
    """Обновляет роль в зависимости от количества варнов"""
    user_id = member.id
    warn_count = warns.get(str(user_id), 0)
    
    warn_roles = [ROLE_WARN_1_ID, ROLE_WARN_2_ID, ROLE_WARN_3_ID]
    roles_to_remove = []
    for role_id in warn_roles:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            roles_to_remove.append(role)
    
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Обновление варн роли")
    
    if warn_count >= 3:
        role = member.guild.get_role(ROLE_WARN_3_ID)
        if role:
            await member.add_roles(role, reason="3/3 варнов")
    elif warn_count == 2:
        role = member.guild.get_role(ROLE_WARN_2_ID)
        if role:
            await member.add_roles(role, reason="2 варна")
    elif warn_count == 1:
        role = member.guild.get_role(ROLE_WARN_1_ID)
        if role:
            await member.add_roles(role, reason="1 варн")

async def remove_all_roles_except(member, keep_role_ids=None):
    """Удаляет все роли у пользователя, кроме указанных"""
    if keep_role_ids is None:
        keep_role_ids = []
    
    roles_to_remove = [role for role in member.roles
                      if role.name != "@everyone" and role.id not in keep_role_ids]
    
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Очистка ролей")
        return True
    return False

# ========== ПРОВЕРКИ ПРАВ ==========
def has_promotion_permission(member):
    if member.guild_permissions.administrator:
        return True
    for role in member.roles:
        if role.id in ALLOWED_ROLES_FOR_PROMOTION:
            return True
    return False

def has_ban_csp_permission(member):
    if member.guild_permissions.administrator:
        return True
    for role in member.roles:
        if role.id in ALLOWED_ROLES_FOR_BAN_CSP:
            return True
    return False

def has_warn_permission(member):
    if member.guild_permissions.administrator:
        return True
    for role in member.roles:
        if role.id in ALLOWED_ROLES_FOR_WARNS:
            return True
    return False

def has_unpunish_permission(member):
    if member.guild_permissions.administrator:
        return True
    return False

# ========== КОМАНДА ACCEPT ==========
@bot.command(name='accept')
async def accept(ctx, *, args: str = ""):
    """Принять пользователя"""
    if not has_promotion_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return
    
    member = await get_member_from_args(ctx, args.split() if args else [])
    
    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!")
        return
    
    if member.id in processing_users:
        await ctx.send("⚠️ Пользователь уже обрабатывается...")
        return
    
    helper_role = ctx.guild.get_role(ROLE_HELPER_ID)
    team_role = ctx.guild.get_role(ROLE_TEAM_ID)
    auto_role = ctx.guild.get_role(ROLE_AUTO_JOIN_ID)
    
    if not helper_role or not team_role:
        await ctx.send("❌ Ошибка: Роли не найдены!")
        return
    
    try:
        processing_users.add(member.id)
        
        # Проверяем наличие заявки
        app_data = applications.get(member.id)
        
        # Удаляем роли ожидания
        roles_to_remove = []
        if auto_role and auto_role in member.roles:
            roles_to_remove.append(auto_role)
        
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="Accept")
        
        # Выдаем основные роли
        roles_to_add = []
        roles_added_names = []
        
        if helper_role not in member.roles:
            roles_to_add.append(helper_role)
            roles_added_names.append(helper_role.name)
        if team_role not in member.roles:
            roles_to_add.append(team_role)
            roles_added_names.append(team_role.name)
        
        if roles_to_add:
            await member.add_roles(*roles_to_add, reason=f"Accept от {ctx.author}")
        
        # Создаем личный канал с данными из заявки
        await create_private_channel(member, source="accept", app_data=app_data)
        
        # Обновляем статус заявки
        if app_data:
            applications[member.id]['status'] = 'accepted'
            applications[member.id]['accepted_by'] = str(ctx.author)
            applications[member.id]['accepted_date'] = datetime.now().strftime("%d.%m.%Y %H:%M")
            save_applications()
        
        await ctx.send(f"✅ {member.mention} принят! Личный канал создан.")
        
        await log_to_channel(
            guild=ctx.guild,
            title="✅ ACCEPT",
            description=f"**Модератор:** {ctx.author.mention}\n"
                       f"**Пользователь:** {member.mention}\n"
                       f"**Выданы роли:** {', '.join(roles_added_names)}",
            color=discord.Color.green()
        )
        
    finally:
        if member.id in processing_users:
            processing_users.remove(member.id)

# ========== КОМАНДА ПОВЫШЕНИЕ ==========
@bot.command(name='повышение')
async def promotion(ctx, *, args: str = None):
    if not has_promotion_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return

    if not args:
        await ctx.send("❌ Укажите роль и пользователя!\n"
                      "Пример: `!повышение Модер @пользователь`\n"
                      "Доступные роли: Гл.Модер, Ст.Модер, Модер, Смотрящий за кп, Админ")
        return

    parts = args.split()
    role_name = parts[0]

    member = await get_member_from_args(ctx, parts[1:] if len(parts) > 1 else [])

    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!")
        return

    role_id = None
    display_name = ""
    role_name_clean = role_name.lower().strip()

    if role_name_clean in ["гл.модер", "гл модер", "главный модер", "гл"]:
        role_id = ROLE_GL_MODER_ID
        display_name = "Гл.Модер"
    elif role_name_clean in ["ст.модер", "ст модер", "старший модер", "ст"]:
        role_id = ROLE_ST_MODER_ID
        display_name = "Ст.Модер"
    elif role_name_clean in ["модер", "модератор"]:
        role_id = ROLE_MODER_ID
        display_name = "Модер"
    elif role_name_clean in ["смотрящий за кп", "смотрящий", "кп", "сзкп"]:
        role_id = ROLE_KP_WATCHER_ID
        display_name = "Смотрящий за кп"
    elif role_name_clean in ["админ", "admin"]:
        role_id = ROLE_ADMIN_ID
        display_name = "Админ"
    else:
        await ctx.send("❌ Неизвестная роль! Доступные: Гл.Модер, Ст.Модер, Модер, Смотрящий за кп, Админ")
        return

    main_role = ctx.guild.get_role(role_id)
    team_role = ctx.guild.get_role(ROLE_TEAM_ID)

    if not main_role:
        await ctx.send(f"❌ Ошибка: Роль {display_name} не найдена!")
        return

    if not team_role:
        await ctx.send("❌ Ошибка: Роль 'Команда проекта' не найдена!")
        return

    had_team_role_before = team_role in member.roles

    roles_to_add = []
    roles_added_names = []

    if main_role not in member.roles:
        roles_to_add.append(main_role)
        roles_added_names.append(main_role.name)

    if team_role not in member.roles:
        roles_to_add.append(team_role)
        roles_added_names.append(team_role.name)

    if not roles_to_add:
        await ctx.send(f"ℹ️ У {member.mention} уже есть все эти роли!")
        return

    try:
        await member.add_roles(*roles_to_add, reason=f"Повышение от {ctx.author}")

        if team_role in roles_to_add and not had_team_role_before:
            await create_private_channel(member, source="promotion")

        await ctx.send(f"✅ {member.mention} выданы роли: {', '.join(roles_added_names)}")

        await log_to_channel(
            guild=ctx.guild,
            title="📋 ПОВЫШЕНИЕ",
            description=f"**Модератор:** {ctx.author.mention}\n"
                       f"**Пользователь:** {member.mention}\n"
                       f"**Выданы роли:** {', '.join(roles_added_names)}",
            color=discord.Color.blue()
        )

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")

# ========== КОМАНДА ЧСП ==========
@bot.command(name='чсп')
async def csp(ctx, *, args: str = ""):
    if not has_ban_csp_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return

    member = await get_member_from_args(ctx, args.split() if args else [])

    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!\n"
                      "Пример: `!чсп @пользователь Причина`")
        return

    reason = "Не указана"
    if args:
        words = args.split()
        if len(words) > 1 and ctx.message.mentions:
            reason = ' '.join(words[1:])
        elif len(words) > 0 and not ctx.message.mentions:
            reason = args

    csp_role = ctx.guild.get_role(ROLE_CSP_ID)

    if not csp_role:
        await ctx.send("❌ Ошибка: Роль ЧСП не найдена!")
        return

    if csp_role in member.roles:
        await ctx.send(f"ℹ️ {member.mention} уже в ЧСП!")
        return

    try:
        await remove_all_roles_except(member, [ROLE_CSP_ID])
        await member.add_roles(csp_role, reason=f"ЧСП: {reason}")
        await delete_private_channel(member)

        embed = discord.Embed(
            title="⛔ ЧСП",
            description=f"{member.mention} отправлен в ЧСП",
            color=discord.Color.red()
        )
        embed.add_field(name="Причина", value=reason, inline=False)
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)

        await log_to_channel(
            guild=ctx.guild,
            title="⛔ ЧСП",
            description=f"**Модератор:** {ctx.author.mention}\n"
                       f"**Пользователь:** {member.mention}\n"
                       f"**Причина:** {reason}",
            color=discord.Color.red()
        )

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")

# ========== КОМАНДА БАН ==========
@bot.command(name='бан')
async def ban(ctx, *, args: str = ""):
    if not has_ban_csp_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return

    member = await get_member_from_args(ctx, args.split() if args else [])

    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!\n"
                      "Пример: `!бан @пользователь Причина`")
        return

    reason = "Не указана"
    if args:
        words = args.split()
        if len(words) > 1 and ctx.message.mentions:
            reason = ' '.join(words[1:])
        elif len(words) > 0 and not ctx.message.mentions:
            reason = args

    try:
        await delete_private_channel(member)

        try:
            await remove_all_roles_except(member, [])
        except:
            pass

        await member.ban(reason=f"Бан от {ctx.author}: {reason}")

        embed = discord.Embed(
            title="🔨 БАН",
            description=f"{member.mention} забанен",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="Причина", value=reason, inline=False)
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)

        await log_to_channel(
            guild=ctx.guild,
            title="🔨 БАН",
            description=f"**Модератор:** {ctx.author.mention}\n"
                       f"**Пользователь:** {member.mention}\n"
                       f"**Причина:** {reason}",
            color=discord.Color.dark_red()
        )

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")

# ========== КОМАНДА СНЯТ ==========
@bot.command(name='снят')
async def unpunish(ctx, *, args: str = ""):
    """Снятие ЧСП - очищает все роли, оставляя только роль Заполнение заявки"""
    if not has_unpunish_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только администраторы.")
        return

    member = await get_member_from_args(ctx, args.split() if args else [])

    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!\n"
                      "Пример: `!снят @пользователь`")
        return

    app_role = ctx.guild.get_role(ROLE_APPLICATION_ID)
    if not app_role:
        await ctx.send("❌ Ошибка: Роль 'Заполнение заявки' не найдена!")
        return

    try:
        await remove_all_roles_except(member, [ROLE_APPLICATION_ID])

        if app_role not in member.roles:
            await member.add_roles(app_role, reason="Снятие ЧСП - выдача роли заявки")

        embed = discord.Embed(
            title="✅ Снятие наказания",
            description=f"У {member.mention} удалены все роли, оставлена только роль 'Заполнение заявки'",
            color=discord.Color.green()
        )
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)

        await log_to_channel(
            guild=ctx.guild,
            title="✅ СНЯТИЕ ЧСП",
            description=f"**Модератор:** {ctx.author.mention}\n"
                       f"**Пользователь:** {member.mention}\n"
                       f"**Действие:** Все роли удалены, оставлена только 'Заполнение заявки'",
            color=discord.Color.green()
        )

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")

# ========== КОМАНДА ВАРН ==========
@bot.command(name='варн')
async def warn(ctx, *, args: str = ""):
    """Выдача варна пользователю"""
    if not has_warn_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return

    member = await get_member_from_args(ctx, args.split() if args else [])

    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!\n"
                      "Пример: `!варн @пользователь Причина`")
        return

    reason = "Не указана"
    if args:
        words = args.split()
        if len(words) > 1 and ctx.message.mentions:
            reason = ' '.join(words[1:])
        elif len(words) > 0 and not ctx.message.mentions:
            reason = args

    user_id = str(member.id)
    current_warns = warns.get(user_id, 0)
    new_warns = current_warns + 1

    warns[user_id] = new_warns
    save_warns()

    # Обновляем роль
    await update_warn_role(member)

    embed = discord.Embed(
        title="⚠️ ВАРН",
        description=f"{member.mention} получил варн",
        color=discord.Color.orange()
    )
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    embed.add_field(name="Всего варнов", value=f"{new_warns}/3", inline=False)

    await ctx.send(embed=embed)

    # Если 3/3 варнов, уведомляем Гл.Модеров
    if new_warns >= 3:
        gl_moder_role = ctx.guild.get_role(ROLE_GL_MODER_ID)
        if gl_moder_role:
            warn_embed = discord.Embed(
                title="⚠️ ВНИМАНИЕ! 3/3 ВАРНОВ",
                description=f"У {member.mention} набралось 3/3 варнов!\n"
                           f"**Причина последнего:** {reason}\n"
                           f"**Модератор:** {ctx.author.mention}\n\n"
                           f"Необходимо принять меры!",
                color=discord.Color.red()
            )
            await ctx.send(f"{gl_moder_role.mention}", embed=warn_embed)

    await log_to_channel(
        guild=ctx.guild,
        title="⚠️ ВАРН",
        description=f"**Модератор:** {ctx.author.mention}\n"
                   f"**Пользователь:** {member.mention}\n"
                   f"**Причина:** {reason}\n"
                   f"**Всего варнов:** {new_warns}/3",
        color=discord.Color.orange()
    )

# ========== КОМАНДА ВАРНЫ ==========
@bot.command(name='варны')
async def warns_list(ctx, *, args: str = ""):
    """Показывает количество варнов у пользователя"""
    member = await get_member_from_args(ctx, args.split() if args else [])

    if not member:
        member = ctx.author

    user_id = str(member.id)
    warn_count = warns.get(user_id, 0)

    embed = discord.Embed(
        title=f"📊 Варны {member.name}",
        description=f"Всего варнов: **{warn_count}/3**",
        color=discord.Color.blue()
    )

    # Показываем прогресс
    progress = "⬛" * warn_count + "⬜" * (3 - warn_count)
    embed.add_field(name="Прогресс", value=progress, inline=False)

    await ctx.send(embed=embed)

# ========== КОМАНДА СНЯТЬ ВАРНЫ ==========
@bot.command(name='снятьварны')
async def remove_warns(ctx, *, args: str = ""):
    """Снимает все варны с пользователя (только админы)"""
    if not has_unpunish_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только администраторы.")
        return

    member = await get_member_from_args(ctx, args.split() if args else [])

    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!")
        return

    user_id = str(member.id)
    if user_id in warns:
        del warns[user_id]
        save_warns()

    # Удаляем варн роли
    warn_roles = [ROLE_WARN_1_ID, ROLE_WARN_2_ID, ROLE_WARN_3_ID]
    roles_to_remove = []
    for role_id in warn_roles:
        role = ctx.guild.get_role(role_id)
        if role and role in member.roles:
            roles_to_remove.append(role)

    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Снятие варнов")

    await ctx.send(f"✅ У {member.mention} сняты все варны")

    await log_to_channel(
        guild=ctx.guild,
        title="✅ СНЯТИЕ ВАРНОВ",
        description=f"**Модератор:** {ctx.author.mention}\n"
                   f"**Пользователь:** {member.mention}",
        color=discord.Color.green()
    )

# ========== КОМАНДА МУТ ==========
@bot.command(name='мут')
async def mute(ctx, *, args: str = ""):
    if not has_ban_csp_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return

    if not args:
        await ctx.send("❌ Укажите время и пользователя!\n"
                      "Пример: `!мут 1ч @пользователь Спам`\n"
                      "Или: `!мут 30м Причина` (если ответили на сообщение)")
        return

    parts = args.split()
    time_str = parts[0]

    member = await get_member_from_args(ctx, parts[1:] if len(parts) > 1 else [])

    if not member:
        await ctx.send("❌ Не удалось определить пользователя!")
        return

    reason = "Не указана"
    if len(parts) > 1:
        reason_parts = parts[1:]
        if ctx.message.mentions:
            mention_index = -1
            for i, part in enumerate(reason_parts):
                if part.startswith('<@'):
                    mention_index = i
                    break
            if mention_index != -1:
                reason_parts = reason_parts[:mention_index] + reason_parts[mention_index+1:]

        if reason_parts:
            reason = ' '.join(reason_parts)

    muted_role = ctx.guild.get_role(ROLE_MUTED_ID)

    if not muted_role:
        await ctx.send("❌ Ошибка: Роль 'Мут' не найдена!")
        return

    if muted_role in member.roles:
        await ctx.send(f"ℹ️ {member.mention} уже в муте!")
        return

    time_seconds = parse_time(time_str)
    if time_seconds == 0:
        await ctx.send("❌ Неправильный формат времени! Используй: `1ч`, `30м`, `2д`")
        return

    try:
        await member.add_roles(muted_role, reason=f"Мут: {reason}")

        unmute_time = datetime.now() + timedelta(seconds=time_seconds)

        embed = discord.Embed(
            title="🔇 МУТ",
            description=f"{member.mention} получил мут",
            color=discord.Color.orange()
        )
        embed.add_field(name="Причина", value=reason, inline=False)
        embed.add_field(name="Длительность", value=format_time(time_seconds), inline=False)
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
        embed.add_field(name="Снимется", value=f"<t:{int(unmute_time.timestamp())}:R>", inline=False)
        await ctx.send(embed=embed)

        await log_to_channel(
            guild=ctx.guild,
            title="🔇 МУТ",
            description=f"**Модератор:** {ctx.author.mention}\n"
                       f"**Пользователь:** {member.mention}\n"
                       f"**Причина:** {reason}\n"
                       f"**Длительность:** {format_time(time_seconds)}",
            color=discord.Color.orange()
        )

        await asyncio.sleep(time_seconds)

        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Автоснятие мута")

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")

# ========== КОМАНДА РАЗМУТ ==========
@bot.command(name='размут')
async def unmute(ctx, *, args: str = ""):
    if not has_ban_csp_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return

    member = await get_member_from_args(ctx, args.split() if args else [])

    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!")
        return

    muted_role = ctx.guild.get_role(ROLE_MUTED_ID)

    if not muted_role:
        await ctx.send("❌ Ошибка: Роль 'Мут' не найдена!")
        return

    if muted_role not in member.roles:
        await ctx.send(f"ℹ️ У {member.mention} нет мута!")
        return

    try:
        await member.remove_roles(muted_role, reason=f"Размут от {ctx.author}")

        embed = discord.Embed(
            title="🔊 РАЗМУТ",
            description=f"С {member.mention} снят мут",
            color=discord.Color.green()
        )
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)

        await log_to_channel(
            guild=ctx.guild,
            title="🔊 РАЗМУТ",
            description=f"**Модератор:** {ctx.author.mention}\n"
                       f"**Пользователь:** {member.mention}",
            color=discord.Color.green()
        )

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")

# ========== ПАРСИНГ ВРЕМЕНИ ==========
def parse_time(time_string):
    """Парсит время из строки (1ч, 30м, 2д)"""
    time_string = time_string.lower()
    if time_string.endswith('ч'):
        try:
            hours = int(time_string[:-1])
            return hours * 3600
        except:
            return 0
    elif time_string.endswith('м'):
        try:
            minutes = int(time_string[:-1])
            return minutes * 60
        except:
            return 0
    elif time_string.endswith('д'):
        try:
            days = int(time_string[:-1])
            return days * 86400
        except:
            return 0
    return 0

def format_time(seconds):
    """Форматирует секунды в читаемый вид"""
    if seconds < 60:
        return f"{seconds} сек"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} мин"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ч {minutes} мин"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} д {hours} ч"

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    token = os.getenv('TOKEN')
    
    print("=== ДИАГНОСТИКА ТОКЕНА ===")
    print(f"🔍 Токен загружен: {bool(token)}")
    
    if token:
        print(f"🔍 Длина токена: {len(token)}")
        print(f"🔍 Первые 20 символов: {token[:20]}")
        print(f"🔍 Последние 20 символов: {token[-20:]}")
    else:
        print("❌ Токен не найден!")
        sys.exit(1)
    
    print("==========================")
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")


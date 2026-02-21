import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta
import asyncio
import json
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Настройки бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ⚠️ ВСЕ РОЛИ ДЛЯ НОВОГО БОТА ⚠️
# Администрация
ROLE_D_OWNER_ID = 1471152308883554485        # D.owner
ROLE_D_ADMIN_ID = 1471152311391752232        # D.ADMIN
ROLE_D_MLADMIN_ID = 1471152313883299860      # D.MLADMIN
ROLE_D_GLMODER_ID = 1471152315535982644      # D.GLMODER
ROLE_D_STMODER_ID = 1471152938905899198      # D.STMODER
ROLE_D_MODER_ID = 1471152938348183726        # D.MODER
ROLE_ADMIN_ID = 1471152940558454979          # Admin

# Роли ожидания
ROLE_WAIT_ID = 1471172631863492648           # Ожидает роли
ROLE_EXAM_ID = 1471152939539103807           # Ожидает сдачи экзамена

# Варны
ROLE_WARN_1_ID = 1474774866249908388         # 1/3 warn
ROLE_WARN_2_ID = 1474774948076851230         # 2/3 warn
ROLE_WARN_3_ID = 1474774982386122953         # 3/3 warn

# ID КАТЕГОРИИ для личных каналов
PRIVATE_CATEGORY_ID = 1474784485034954845

# КАНАЛ ДЛЯ ЛОГОВ
LOG_CHANNEL_ID = 1474784848144236809

# Файл для хранения варнов
WARNS_FILE = "warns_dkp.json"

# Словарь для хранения варнов {user_id: warn_count}
warns = {}

# Словарь для хранения созданных каналов {user_id: channel_id}
user_channels = {}

# Множество для отслеживания обрабатываемых пользователей
processing_users = set()

# Список ролей, которые НЕ НАДО выдавать автоматически
EXCLUDED_AUTO_ROLES = [
    ROLE_D_OWNER_ID,
    ROLE_D_ADMIN_ID,
    ROLE_D_MLADMIN_ID,
    ROLE_D_GLMODER_ID,
    ROLE_D_STMODER_ID,
    ROLE_D_MODER_ID,
    ROLE_ADMIN_ID,
    ROLE_WARN_1_ID,
    ROLE_WARN_2_ID,
    ROLE_WARN_3_ID
]

# Список ролей, которые могут использовать команды (D.owner и выше)
ALLOWED_ROLES_FOR_COMMANDS = [
    ROLE_D_OWNER_ID,
    ROLE_D_ADMIN_ID,
    ROLE_D_MLADMIN_ID,
    ROLE_D_GLMODER_ID,
    ROLE_D_STMODER_ID,
    ROLE_D_MODER_ID,
    ROLE_ADMIN_ID
]

# Список ролей, которые могут видеть личные каналы
ROLES_CAN_SEE_PRIVATE_CHANNELS = [
    ROLE_D_OWNER_ID,
    ROLE_D_ADMIN_ID,
    ROLE_D_MLADMIN_ID,
    ROLE_D_GLMODER_ID,
    ROLE_D_STMODER_ID,
    ROLE_D_MODER_ID,
    ROLE_ADMIN_ID
]

# Загрузка варнов из файла
def load_warns():
    global warns
    if os.path.exists(WARNS_FILE):
        try:
            with open(WARNS_FILE, 'r', encoding='utf-8') as f:
                warns = json.load(f)
                warns = {int(k): v for k, v in warns.items()}
        except:
            warns = {}
    else:
        warns = {}

# Сохранение варнов в файл
def save_warns():
    with open(WARNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(warns, f, ensure_ascii=False, indent=4)

# Загрузка каналов при запуске
async def load_channels():
    for guild in bot.guilds:
        category = guild.get_channel(PRIVATE_CATEGORY_ID)
        if category and isinstance(category, discord.CategoryChannel):
            for channel in category.text_channels:
                if channel.name.startswith("📌┃"):
                    for member in guild.members:
                        clean_member = member.name.replace(" ", "_").replace(".", "").replace(",", "")
                        if clean_member.lower() in channel.name.lower() or member.name.lower() in channel.name.lower():
                            user_channels[member.id] = channel.id
                            break

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} успешно запущен!')
    print(f'📋 Серверов: {len(bot.guilds)}')
    print(f'👥 Команды загружены: !accept, !варн, !варны, !снятьварны, !чсп, !бан, !снят')
    print(f'📝 Категория для личных каналов: {PRIVATE_CATEGORY_ID}')
    print(f'📋 Канал логов: {LOG_CHANNEL_ID}')
    load_warns()
    await load_channels()
    print(f'📊 Загружено варнов: {len(warns)}')
    await bot.change_presence(activity=discord.Game(name="RaftWorld » DKP"))

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

async def create_private_channel(member, source="unknown"):
    """Создает личный канал для участника"""
    if member.id in processing_users:
        print(f"⚠️ Пользователь {member.name} уже обрабатывается, пропускаем")
        return None
    
    try:
        processing_users.add(member.id)
        print(f"🔧 Создание канала для {member.name}")
        
        # Проверяем существующий канал
        if member.id in user_channels:
            existing_channel = member.guild.get_channel(user_channels[member.id])
            if existing_channel:
                return existing_channel
        
        # Получаем категорию
        category = member.guild.get_channel(PRIVATE_CATEGORY_ID)
        if not category:
            for cat in member.guild.categories:
                if cat.name == "🔒 Личные каналы DKP":
                    category = cat
                    break
            if not category:
                category = await member.guild.create_category("🔒 Личные каналы DKP")
        
        # Создаем имя канала
        clean_name = member.name.replace(" ", "_").replace(".", "").replace(",", "")
        channel_name = f"📌┃{clean_name}"
        
        # Проверяем существование
        for channel in category.text_channels:
            if channel.name == channel_name or clean_name.lower() in channel.name.lower():
                user_channels[member.id] = channel.id
                return channel
        
        if len(channel_name) > 32:
            channel_name = channel_name[:32]
        
        # Настраиваем права
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(
                read_messages=True, 
                send_messages=True, 
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            member.guild.me: discord.PermissionOverwrite(
                read_messages=True, 
                send_messages=True, 
                manage_channels=True
            )
        }
        
        # Добавляем права для админов
        for role_id in ROLES_CAN_SEE_PRIVATE_CHANNELS:
            role = member.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True,
                    read_message_history=True
                )
        
        # СОЗДАЕМ КАНАЛ
        channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            reason=f"Личный канал для {member.name}"
        )
        
        user_channels[member.id] = channel.id
        
        # Приветствие
        embed = discord.Embed(
            title="🎉 Добро пожаловать в личный канал!",
            description=f"Привет, {member.mention}!\n\n"
                       f"Это ваш личный канал DKP.\n"
                       f"**Что можно делать:**\n"
                       f"• Общаться с командой\n"
                       f"• Делиться файлами\n"
                       f"• Получать информацию\n\n"
                       f"**Доступно для:**\n"
                       f"• {member.mention} (вы)\n"
                       f"• D.owner и выше",
            color=discord.Color.blue()
        )
        embed.set_footer(text="RaftWorld » DKP")
        
        welcome_msg = await channel.send(embed=embed)
        await welcome_msg.pin(reason="Закрепленное приветствие")
        
        await log_to_channel(
            guild=member.guild,
            title="📝 СОЗДАНИЕ КАНАЛА",
            description=f"Создан личный канал для {member.mention}\nКанал: {channel.mention}"
        )
        
        return channel
        
    except Exception as e:
        print(f"❌ Ошибка при создании канала: {str(e)}")
        return None
    finally:
        if member.id in processing_users:
            processing_users.remove(member.id)

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
        print(f"❌ Ошибка при удалении канала: {str(e)}")
    return False

def has_permission(member):
    """Проверяет, есть ли у пользователя право на команды"""
    if member.guild_permissions.administrator:
        return True
    for role in member.roles:
        if role.id in ALLOWED_ROLES_FOR_COMMANDS:
            return True
    return False

def has_unpunish_permission(member):
    """Проверяет, есть ли у пользователя право на снятие (только D.owner)"""
    if member.guild_permissions.administrator:
        return True
    for role in member.roles:
        if role.id == ROLE_D_OWNER_ID:
            return True
    return False

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

async def update_warn_role(member):
    """Обновляет роль в зависимости от количества варнов"""
    user_id = member.id
    warn_count = warns.get(str(user_id), 0)
    
    # Удаляем старые варн роли
    warn_roles = [ROLE_WARN_1_ID, ROLE_WARN_2_ID, ROLE_WARN_3_ID]
    roles_to_remove = []
    for role_id in warn_roles:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            roles_to_remove.append(role)
    
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Обновление варн роли")
    
    # Выдаем новую роль
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

@bot.event
async def on_member_join(member):
    """Автоматическая выдача ролей новым участникам"""
    try:
        wait_role = member.guild.get_role(ROLE_WAIT_ID)
        exam_role = member.guild.get_role(ROLE_EXAM_ID)
        
        roles_to_add = []
        if wait_role:
            roles_to_add.append(wait_role)
        if exam_role:
            roles_to_add.append(exam_role)
        
        if roles_to_add:
            await member.add_roles(*roles_to_add, reason="Автоматические роли при заходе")
            print(f"✅ Выданы роли ожидания пользователю {member.name}")
            
            await log_to_channel(
                guild=member.guild,
                title="🆕 НОВЫЙ УЧАСТНИК",
                description=f"{member.mention} получил роли:\n" +
                           f"{wait_role.mention if wait_role else ''}\n" +
                           f"{exam_role.mention if exam_role else ''}"
            )
            
    except Exception as e:
        print(f"❌ Ошибка при выдаче ролей: {str(e)}")

@bot.event
async def on_member_update(before, after):
    """Отслеживаем изменение ролей"""
    if after.id in processing_users:
        return
    
    try:
        # Здесь можно добавить логику для автоматического создания канала
        # при получении определенной роли
        pass
            
    except Exception as e:
        print(f"❌ Ошибка в on_member_update: {str(e)}")

@bot.command(name='accept')
async def accept(ctx, *, args: str = ""):
    """Выдача роли (аналог !accept из первого бота)"""
    if not has_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return
    
    member = await get_member_from_args(ctx, args.split() if args else [])
    
    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!")
        return
    
    if member.id in processing_users:
        await ctx.send("⚠️ Пользователь уже обрабатывается, подождите...")
        return
    
    try:
        processing_users.add(member.id)
        
        # Удаляем роли ожидания
        wait_role = ctx.guild.get_role(ROLE_WAIT_ID)
        exam_role = ctx.guild.get_role(ROLE_EXAM_ID)
        
        roles_to_remove = []
        if wait_role and wait_role in member.roles:
            roles_to_remove.append(wait_role)
        if exam_role and exam_role in member.roles:
            roles_to_remove.append(exam_role)
        
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="Accept - удаление ролей ожидания")
        
        # Создаем личный канал
        await create_private_channel(member, source="accept")
        
        await ctx.send(f"✅ {member.mention} принят! Личный канал создан.")
        
        await log_to_channel(
            guild=ctx.guild,
            title="✅ ACCEPT",
            description=f"**Модератор:** {ctx.author.mention}\n"
                       f"**Пользователь:** {member.mention}\n"
                       f"**Действие:** Пользователь принят, создан личный канал",
            color=discord.Color.green()
        )
        
    finally:
        if member.id in processing_users:
            processing_users.remove(member.id)

@bot.command(name='варн')
async def warn(ctx, *, args: str = ""):
    """Выдача варна пользователю"""
    if not has_permission(ctx.author):
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
    
    # Если 3/3 варнов, уведомляем D.owner
    if new_warns >= 3:
        d_owner_role = ctx.guild.get_role(ROLE_D_OWNER_ID)
        if d_owner_role:
            warn_embed = discord.Embed(
                title="⚠️ ВНИМАНИЕ! 3/3 ВАРНОВ",
                description=f"У {member.mention} набралось 3/3 варнов!\n"
                           f"**Причина последнего:** {reason}\n"
                           f"**Модератор:** {ctx.author.mention}\n\n"
                           f"Необходимо принять меры!",
                color=discord.Color.red()
            )
            await ctx.send(f"{d_owner_role.mention}", embed=warn_embed)
    
    await log_to_channel(
        guild=ctx.guild,
        title="⚠️ ВАРН",
        description=f"**Модератор:** {ctx.author.mention}\n"
                   f"**Пользователь:** {member.mention}\n"
                   f"**Причина:** {reason}\n"
                   f"**Всего варнов:** {new_warns}/3",
        color=discord.Color.orange()
    )

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
    
    progress = "⬛" * warn_count + "⬜" * (3 - warn_count)
    embed.add_field(name="Прогресс", value=progress, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='снятьварны')
async def remove_warns(ctx, *, args: str = ""):
    """Снимает все варны с пользователя (только D.owner)"""
    if not has_unpunish_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только D.owner.")
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

@bot.command(name='чсп')
async def csp(ctx, *, args: str = ""):
    """Выдача ЧСП"""
    if not has_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return
    
    member = await get_member_from_args(ctx, args.split() if args else [])
    
    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!")
        return
    
    reason = "Не указана"
    if args:
        words = args.split()
        if len(words) > 1 and ctx.message.mentions:
            reason = ' '.join(words[1:])
        elif len(words) > 0 and not ctx.message.mentions:
            reason = args
    
    # Здесь можно добавить логику ЧСП
    await ctx.send(f"⛔ {member.mention} отправлен в ЧСП. Причина: {reason}")
    
    await log_to_channel(
        guild=ctx.guild,
        title="⛔ ЧСП",
        description=f"**Модератор:** {ctx.author.mention}\n"
                   f"**Пользователь:** {member.mention}\n"
                   f"**Причина:** {reason}",
        color=discord.Color.red()
    )

@bot.command(name='бан')
async def ban(ctx, *, args: str = ""):
    """Бан пользователя"""
    if not has_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return
    
    member = await get_member_from_args(ctx, args.split() if args else [])
    
    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!")
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
        await ctx.send(f"❌ Ошибка при бане: {str(e)}")

@bot.command(name='снят')
async def unpunish(ctx, *, args: str = ""):
    """Снятие наказания"""
    if not has_unpunish_permission(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только D.owner.")
        return
    
    member = await get_member_from_args(ctx, args.split() if args else [])
    
    if not member:
        await ctx.send("❌ Укажите пользователя через @ или ответьте на его сообщение!")
        return
    
    wait_role = ctx.guild.get_role(ROLE_WAIT_ID)
    exam_role = ctx.guild.get_role(ROLE_EXAM_ID)
    
    roles_to_add = []
    if wait_role:
        roles_to_add.append(wait_role)
    if exam_role:
        roles_to_add.append(exam_role)
    
    if roles_to_add:
        await member.add_roles(*roles_to_add, reason="Снятие наказания")
    
    embed = discord.Embed(
        title="✅ Снятие наказания",
        description=f"У {member.mention} сняты наказания, выданы роли ожидания",
        color=discord.Color.green()
    )
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)
    
    await log_to_channel(
        guild=ctx.guild,
        title="✅ СНЯТИЕ",
        description=f"**Модератор:** {ctx.author.mention}\n"
                   f"**Пользователь:** {member.mention}",
        color=discord.Color.green()
    )

# Запуск бота
if __name__ == "__main__":
    import sys
    token = os.getenv('TOKEN')
    
    print("=== ЗАПУСК БОТА RaftWorld » DKP ===")
    print(f"🔍 Токен загружен: {bool(token)}")
    
    if token:
        print(f"🔍 Длина токена: {len(token)}")
    else:
        print("❌ Токен не найден!")
        sys.exit(1)
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")

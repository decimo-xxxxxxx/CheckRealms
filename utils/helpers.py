from datetime import datetime, timedelta
import pytz
from dateutil.relativedelta import relativedelta
import discord
from discord import Forbidden
from config import CONFIG
from .storage import storage
from discord import RawReactionActionEvent

def get_last_monday_of_month():
    now = datetime.now(pytz.timezone('Asia/Tokyo'))
    last_day = now + relativedelta(day=31)
    # weekday() : Monday=0 … Sunday=6
    offset = (last_day.weekday() - 0) % 7
    return last_day - timedelta(days=offset)

def get_last_day_of_month():
    """今月の月末日を datetime.date で返す"""
    now = datetime.now(pytz.timezone('Asia/Tokyo'))
    last_day = now + relativedelta(day=31)
    return last_day.date()

async def send_initial_message(bot, user):
    try:
        startday = get_last_monday_of_month()
        endday = get_last_day_of_month()
        
        embed = discord.Embed(
            title="来月のRealms利用確認",
            description="以下のリアクションで回答してください：\n\n⭕ Yes\n❌ No",
            color=0x00ff00
        )
        embed.set_footer(text=f"回答期限:本日 ~ {endday.strftime('%m/%d')} 23:59 JST")
        message = await user.send(embed=embed)
        await message.add_reaction("⭕")
        await message.add_reaction("❌")
        storage.message_ids[user.id] = message.id
        storage.responses[user.id] = {'reaction': None, 'last_updated': None, 'month': endday.month}
    except Forbidden:
        print(f"{user.name} にDMを送信できませんでした")

async def notify_admin(bot, user, reaction):
    admin = await bot.fetch_user(CONFIG["ADMIN_ID"])
    try:
        await admin.send(
            f"**新しい回答が登録されました**\n"
            f"ユーザー: {user.display_name}\n"
            f"{datetime.now().month}月Realms利用: {reaction}\n"
            f"更新日時: {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Forbidden:
        print("管理者にDMを送信できませんでした")
        
async def send_reminder(bot,user):
    try:
        await user.send("⚠️ 回答期限が迫っています！まだ回答が確認できていません。")
    except discord.Forbidden:
        print(f"{user.name} にリマインダーを送信できませんでした")
        
async def send_monthly_messages(bot):
    channel = bot.get_channel(CONFIG["TARGET_CHANNEL"])
    if not channel:
        print("対象チャンネルが見つかりません")
        return

    members = [member for member in channel.members 
              if member.id not in CONFIG["EXCLUDE_USERS"] 
              and not member.bot]

    for member in members:
        await send_initial_message(bot,member)
        
async def check_reminders(bot,delta_days: int = 1):
    #日次チェック。締切日と締切翌日に未回答ユーザーにリマインドを送る。
    
    today = datetime.now(pytz.timezone('Asia/Tokyo'))
    deadline = get_last_day_of_month()

    if today == deadline or today == (deadline + timedelta(days=delta_days)):
        for user_id in storage.get_unresponded_users():
            user = await bot.fetch_user(user_id)
            if user:
                await send_reminder(bot,user)
                
async def on_raw_reaction_add(bot, payload: RawReactionActionEvent):
    # ボットのリアクションは無視
    if payload.user_id == bot.user.id:
        return

    # storage からそのユーザー宛のメッセージIDを取得
    msg_id = storage.message_ids.get(payload.user_id)
    if msg_id is None or payload.message_id != msg_id:
        return

    # リアクション絵文字を保存
    storage.responses[payload.user_id]['reaction'] = str(payload.emoji)
    storage.responses[payload.user_id]['last_updated'] = datetime.now(pytz.timezone('Asia/Tokyo'))

    # 管理者通知
    user = await bot.fetch_user(payload.user_id)
    await notify_admin(bot, user, payload.emoji)
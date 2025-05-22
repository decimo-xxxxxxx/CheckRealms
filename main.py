import discord
from discord import Intents
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from config import CONFIG
from utils import storage
import pytz



# 通知コマンド
from commands import notification_commands

tz  = pytz.timezone("Asia/Tokyo")
now = datetime.now(tz)

class RealmBot(commands.Bot):
    def __init__(self):
        intents = Intents.default()
        intents.members = True
        intents.reactions = True
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents
        )
        
        self.scheduler = AsyncIOScheduler(timezone='Asia/Tokyo')

    async def setup_hook(self):
        # コマンドのセットアップ
        await notification_commands.setup(self)
        await self.tree.sync()
        self.scheduler.start()
        
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        self.schedule_jobs()
    
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # discord.py 自体が payload を渡してくれるので、
        # ここで helpers のロジックを呼び出します。
        from utils.helpers import on_raw_reaction_add as helper
        await helper(self, payload)

    def schedule_jobs(self):
        from utils.helpers import send_monthly_messages, check_reminders, send_reminder,get_last_monday_of_month
        from apscheduler.triggers.cron import CronTrigger

        
        self.scheduler.add_job(
            send_monthly_messages,
            trigger=CronTrigger(
                day='last mon',
                hour=9,
                minute=0,
                timezone='Asia/Tokyo'
            ),
            args=[self],
        )

        self.scheduler.add_job(
            check_reminders,
            trigger=CronTrigger(
                hour=9,
                minute=0,
                timezone='Asia/Tokyo'
            ),
            args=[self],
            
            
        )
        
        
        # ---------- 開発モードだけテスト用ジョブを追加 ----------
        if CONFIG.get("ENV") == "development":
            channel = self.get_channel(CONFIG["TARGET_CHANNEL"])
            if channel:
                members = [
                m for m in channel.members
                if m.id not in CONFIG["EXCLUDE_USERS"] and not m.bot
            ]
            # 全メンバーを未回答ユーザーとして登録
            for m in members:
                storage.responses[m.id] = {
                    "reaction": None,
                    "last_updated": None,
                    "month": get_last_monday_of_month().month
                }
            # ── ここから追加 ──
            # 起動後1分で全員に直接 send_reminder をテスト
            for idx, m in enumerate(members):
                self.scheduler.add_job(
                    send_reminder,
                    trigger=DateTrigger(run_date=now + timedelta(minutes=1 + idx)),
                    args=[self, m],
                    id=f"dev_direct_remind_{m.id}"
                )

            # ── 追加ここまで ──

            # 起動後1分で send_monthly_messages → send_initial_message のテスト
            self.scheduler.add_job(
                send_monthly_messages,
                trigger=DateTrigger(run_date=now + timedelta(minutes=1)),
                args=[self],
                id="dev_test_send_initial",
            )

            # 起動後2分で check_reminders → send_reminder のテスト
            # storage 側で未回答ユーザーをあらかじめ入れておく
            self.scheduler.add_job(
                check_reminders,
                trigger=DateTrigger(run_date=now + timedelta(minutes=2)),
                args=[self, 0],   # delta_days=0 なら「締切当日」もリマインド
                id="dev_test_send_reminder",
            )

            # notify_admin は、send_initial_message 後にユーザーがリアクションを付けることで発動
            # そのため単独でジョブ化せず、実際にリアクション操作をして確認します。

        #  get_jobs() ログに出す
        for job in self.scheduler.get_jobs():
            print(f"[SCHEDULED] {job.id} → next run at {job.next_run_time}")
            
bot = RealmBot()

if __name__ == "__main__":
    bot.run(CONFIG["TOKEN"])
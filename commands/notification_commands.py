from discord import Interaction
from discord.ext import commands
from config import CONFIG
from utils.helpers import send_initial_message
from utils.storage import storage

async def setup(bot):
    @bot.tree.command(
        name="send_notification",
        description="手動でレルムズ利用確認の通知を全員に送信します"
    )
    @commands.has_permissions(administrator=True)
    async def send_notification(interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = bot.get_channel(CONFIG["TARGET_CHANNEL"])
            if not channel:
                await interaction.followup.send("対象チャンネルが見つかりません")
                return

            members = [member for member in channel.members 
                      if member.id not in CONFIG["EXCLUDE_USERS"] 
                      and not member.bot]

            success = 0
            failed = 0
            
            for member in members:
                try:
                    await send_initial_message(bot, member)
                    success += 1
                except Exception as e:
                    print(f"{member.name} への送信失敗: {str(e)}")
                    failed += 1

            await interaction.followup.send(
                f"通知送信完了\n成功: {success}件\n失敗: {failed}件\n"
                f"除外ユーザー: {', '.join(map(str, CONFIG['EXCLUDE_USERS']))}"
            )
            
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {str(e)}")
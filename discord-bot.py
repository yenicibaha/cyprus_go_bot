import discord
from discord.ext import tasks
import asyncio
from datetime import datetime
import re
import os

# Bot ayarları
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # Environment variable'dan al
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))  # Webhook mesajlarının geldiği kanal ID

# İstatistikler
stats = {
    'appstore': 0,
    'playstore': 0,
    'last_reset': datetime.now()
}

# Discord client oluştur
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def parse_redirect_message(message_content):
    """Discord mesajından yönlendirme bilgisini çıkar"""
    # App Store mesajı kontrolü
    if '🍎' in message_content and 'APP STORE' in message_content.upper():
        return 'appstore'
    # Play Store mesajı kontrolü
    elif '🤖' in message_content and ('PLAY STORE' in message_content.upper() or 'GOOGLE PLAY' in message_content.upper()):
        return 'playstore'
    return None

@client.event
async def on_ready():
    print(f'{client.user} olarak giriş yapıldı!')
    # Saatte bir çalışacak görevi başlat
    hourly_summary.start()
    # Mevcut mesajları say
    await count_existing_messages()

@client.event
async def on_message(message):
    # Bot'un kendi mesajlarını yok say
    if message.author == client.user:
        return
    
    # Webhook mesajlarını kontrol et
    if message.webhook_id is not None:
        redirect_type = parse_redirect_message(message.content)
        if redirect_type:
            stats[redirect_type] += 1
            print(f"Yeni {redirect_type} yönlendirmesi tespit edildi! Toplam: {stats[redirect_type]}")

async def count_existing_messages():
    """Kanaldaki mevcut mesajları say"""
    try:
        channel = client.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Kanal bulunamadı: {CHANNEL_ID}")
            return
        
        print("Mevcut mesajlar sayılıyor...")
        appstore_count = 0
        playstore_count = 0
        
        async for message in channel.history(limit=None):
            # Sadece webhook mesajlarını say
            if message.webhook_id is not None:
                redirect_type = parse_redirect_message(message.content)
                if redirect_type == 'appstore':
                    appstore_count += 1
                elif redirect_type == 'playstore':
                    playstore_count += 1
        
        stats['appstore'] = appstore_count
        stats['playstore'] = playstore_count
        
        print(f"Mevcut sayılar: App Store: {appstore_count}, Play Store: {playstore_count}")
    except Exception as e:
        print(f"Mesaj sayma hatası: {e}")

@tasks.loop(hours=1)
async def hourly_summary():
    """Her saat başı özet gönder"""
    try:
        channel = client.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Kanal bulunamadı: {CHANNEL_ID}")
            return
        
        now = datetime.now()
        time_str = now.strftime('%d %B %Y, %H:%M')
        
        embed = discord.Embed(
            title="📊 Saatlik Yönlendirme Özeti",
            description=f"**{time_str}** itibarıyla yönlendirme istatistikleri",
            color=0x5865F2
        )
        
        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value="\u200b",
            inline=False
        )
        
        embed.add_field(
            name="🍎 **App Store (iOS) Yönlendirme**",
            value=f"```\n{stats['appstore']:06d} yönlendirme\n```",
            inline=False
        )
        
        embed.add_field(
            name="🤖 **Play Store (Android) Yönlendirme**",
            value=f"```\n{stats['playstore']:06d} yönlendirme\n```",
            inline=False
        )
        
        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value="\u200b",
            inline=False
        )
        
        # İlerleme yüzdesi (opsiyonel)
        total = stats['appstore'] + stats['playstore']
        if total > 0:
            appstore_percent = (stats['appstore'] / total) * 100
            playstore_percent = (stats['playstore'] / total) * 100
            
            embed.add_field(
                name="📊 **Dağılım**",
                value=f"🍎 iOS: **{appstore_percent:.1f}%** | 🤖 Android: **{playstore_percent:.1f}%**",
                inline=False
            )
        
        embed.set_footer(text="Cyprus Go - Otomatik İstatistik Botu")
        embed.timestamp = now
        
        await channel.send(embed=embed)
        print(f"Saatlik özet gönderildi: App Store: {stats['appstore']}, Play Store: {stats['playstore']}")
        
    except Exception as e:
        print(f"Saatlik özet gönderme hatası: {e}")

@hourly_summary.before_loop
async def before_hourly_summary():
    """İlk çalıştırmadan önce bot'un hazır olmasını bekle"""
    await client.wait_until_ready()
    # İlk özeti hemen göndermek yerine, bir sonraki saat başını bekle
    # Örneğin saat 14:30'da başlatılırsa, 15:00'da ilk özeti gönder
    import time
    current_minute = datetime.now().minute
    wait_seconds = (60 - current_minute) * 60
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

# Bot'u çalıştır
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("HATA: DISCORD_BOT_TOKEN environment variable'ı ayarlanmamış!")
        exit(1)
    if not CHANNEL_ID:
        print("HATA: DISCORD_CHANNEL_ID environment variable'ı ayarlanmamış!")
        exit(1)
    
    client.run(BOT_TOKEN)


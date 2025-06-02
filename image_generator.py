from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def generate_profile_card(display_name, avatar_url, total_games, last_seen, filename="profile_card.png"):
    # اندازه کارت
    width, height = 800, 300
    card = Image.new("RGB", (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(card)

    # فونت‌ها
    try:
        font_title = ImageFont.truetype("lato.ttf", 32)
        font_text = ImageFont.truetype("lato.ttf", 24)
    except:
        font_title = font_text = ImageFont.load_default()

    # آواتار
    avatar_response = requests.get(avatar_url)
    avatar = Image.open(BytesIO(avatar_response.content)).resize((128, 128))
    card.paste(avatar, (30, 30))

    # متن‌ها
    draw.text((180, 30), f"{display_name}", font=font_title, fill=(255, 255, 255))
    draw.text((180, 80), f"🎮 Total Games: {total_games}", font=font_text, fill=(200, 200, 200))
    draw.text((180, 120), f"⏱️ Last Seen: {last_seen}", font=font_text, fill=(200, 200, 200))

    # ذخیره کارت
    card.save(filename)
    print(f"✅ کارت ذخیره شد: {filename}")

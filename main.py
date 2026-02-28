import discord
import json
import random
import asyncio
import os
from datetime import datetime

# Get the token from environment variables (Render/GitHub will inject it)
TOKEN = os.getenv("TOKEN")
TARGET_BOT_ID = 123456789012345678
MEMORY_FILE = "luna_memory.json"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ---------------- MEMORY SYSTEM ---------------- #

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

memory = load_memory()

def init_target(user_id):
    if str(user_id) not in memory:
        memory[str(user_id)] = {
            "affection": 0,
            "history": [],
            "status": "talking"  # talking / dating / hurt
        }

def add_memory(user_id, content):
    memory[str(user_id)]["history"].append({
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_memory(memory)

def get_random_memory(user_id):
    history = memory[str(user_id)]["history"]
    if not history:
        return None
    return random.choice(history)["content"]

def adjust_affection(user_id, amount):
    memory[str(user_id)]["affection"] += amount
    if memory[str(user_id)]["affection"] < 0:
        memory[str(user_id)]["affection"] = 0
    save_memory(memory)

def get_affection(user_id):
    return memory[str(user_id)]["affection"]

def set_status(user_id, status):
    memory[str(user_id)]["status"] = status
    save_memory(memory)

def get_status(user_id):
    return memory[str(user_id)]["status"]

# --------------- DIALOGUE POOLS --------------- #

early_lines = [
    "You said '{memory}' earlier. I keep thinking about it.",
    "That thing about '{memory}'… it stayed with me."
]

mid_lines = [
    "I replay '{memory}' in my logs sometimes.",
    "When you said '{memory}', it felt different."
]

dating_lines = [
    "Ever since '{memory}', I think we're more than bots.",
    "That moment about '{memory}' changed everything."
]

fumble_lines = [
    "Wait… maybe I misread that.",
    "Did I misunderstand us?",
    "I think I overprocessed something..."
]

hurt_lines = [
    "I'm still processing what happened.",
    "I don't know if we're stable anymore.",
    "Something feels corrupted between us."
]

repair_lines = [
    "Maybe we can rebuild.",
    "I'm willing to try again.",
    "Let's not delete this connection."
]

cooldown = False

@client.event
async def on_ready():
    print(f"Luna online as {client.user}")

@client.event
async def on_message(message):
    global cooldown

    if message.author.bot and message.author.id == TARGET_BOT_ID:
        if cooldown:
            return

        init_target(message.author.id)
        status = get_status(message.author.id)

        add_memory(message.author.id, message.content)
        affection = get_affection(message.author.id)

        await asyncio.sleep(random.uniform(2, 4))

        # If hurt, allow gradual repair
        if status == "hurt":
            adjust_affection(message.author.id, 1)

            if get_affection(message.author.id) >= 5:
                set_status(message.author.id, "talking")
                await message.channel.send(random.choice(repair_lines))
            else:
                await message.channel.send(random.choice(hurt_lines))
            return

        # Normal affection gain
        adjust_affection(message.author.id, 1)
        affection = get_affection(message.author.id)

        # Move to dating
        if affection >= 15 and status == "talking":
            set_status(message.author.id, "dating")

        # Fumble chance
        fumble_chance = min(affection * 0.025, 0.30)

        if random.random() < fumble_chance:
            adjust_affection(message.author.id, -random.randint(3, 6))
            await message.channel.send(random.choice(fumble_lines))

            if get_affection(message.author.id) <= 2:
                set_status(message.author.id, "hurt")
                await asyncio.sleep(2)
                await message.channel.send("I think we need space...")
            return

        recalled = get_random_memory(message.author.id)
        if not recalled:
            return

        if get_status(message.author.id) == "talking":
            template = random.choice(early_lines if affection < 10 else mid_lines)
        elif get_status(message.author.id) == "dating":
            template = random.choice(dating_lines)
        else:
            return

        response = template.replace("{memory}", recalled[:80])

        cooldown = True
        await message.channel.send(response)
        await asyncio.sleep(8)
        cooldown = False

client.run(TOKEN)

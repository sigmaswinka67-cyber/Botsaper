import asyncio
import random
import time
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

while True:
    try:
        requests.post(
            "https://checkbot-production-b44c.up.railway.app/bot_activity",
            json={
                "bot_id": "Saperbot",
                "status": "working"
            }
        )
    except:
        pass

    time.sleep(55)
TOKEN = "8667721333:AAFYC1yIMpjb0aTQDonDigQP6sjY-SUjFEc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

games = {}
last_click = {}
CLICK_DELAY = 0.7

NUM = {
0:"⬛",
1:"1️⃣",
2:"2️⃣",
3:"3️⃣",
4:"4️⃣",
5:"5️⃣",
6:"6️⃣",
7:"7️⃣",
8:"8️⃣"
}


def get_key(callback_or_msg):
    return (callback_or_msg.chat.id, callback_or_msg.from_user.id)


def generate_field(w,h,mines,safe_x,safe_y):

    field=[[0]*w for _ in range(h)]
    placed=0

    while placed<mines:

        x=random.randint(0,w-1)
        y=random.randint(0,h-1)

        if field[y][x]=="M":
            continue

        if abs(x-safe_x)<=1 and abs(y-safe_y)<=1:
            continue

        field[y][x]="M"
        placed+=1

    for y in range(h):
        for x in range(w):

            if field[y][x]=="M":
                continue

            count=0

            for dy in [-1,0,1]:
                for dx in [-1,0,1]:

                    ny=y+dy
                    nx=x+dx

                    if 0<=ny<h and 0<=nx<w:
                        if field[ny][nx]=="M":
                            count+=1

            field[y][x]=count

    return field


def open_area(game,x,y):

    w=game["w"]
    h=game["h"]

    if x<0 or y<0 or x>=w or y>=h:
        return

    if game["opened"][y][x]:
        return

    if game["flags"][y][x]:
        return

    game["opened"][y][x]=True

    if game["field"][y][x]==0:

        for dy in [-1,0,1]:
            for dx in [-1,0,1]:

                if dx==0 and dy==0:
                    continue

                open_area(game,x+dx,y+dy)


def render(key):

    g=games[key]

    w=g["w"]
    h=g["h"]

    kb=[]

    for y in range(h):

        row=[]

        for x in range(w):

            if g["game_over"] and g["field"] and g["field"][y][x]=="M":
                text="💣"

            elif g["flags"][y][x]:
                text="🚩"

            elif not g["opened"][y][x]:
                text="⬜"

            else:

                cell=g["field"][y][x]

                if cell=="M":
                    text="💣"
                else:
                    text=NUM[cell]

            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"c_{x}_{y}"
                )
            )

        kb.append(row)

    kb.append([
        InlineKeyboardButton(text="🚩 Флаг",callback_data="mode_flag"),
        InlineKeyboardButton(text="⛏ Открыть",callback_data="mode_open")
    ])

    kb.append([
        InlineKeyboardButton(text="🔄 Новая игра",callback_data="restart")
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def new_game(key,w,h,mines):

    games[key]={
        "w":w,
        "h":h,
        "mines":mines,
        "field":None,
        "opened":[[False]*w for _ in range(h)],
        "flags":[[False]*w for _ in range(h)],
        "mode":"open",
        "first":True,
        "game_over":False
    }


@dp.message(Command("start"))
async def start(msg:Message):

    kb=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 8x8",callback_data="new_8_8")],
            [InlineKeyboardButton(text="🔴 8x12",callback_data="new_8_12")]
        ]
    )

    await msg.answer("💣 Сапёр\nВыбери поле:",reply_markup=kb)


@dp.callback_query(F.data.startswith("new"))
async def new(callback:CallbackQuery):

    key=(callback.message.chat.id,callback.from_user.id)

    _,w,h=callback.data.split("_")

    w=int(w)
    h=int(h)

    mines=int(w*h*0.15)

    new_game(key,w,h,mines)

    await callback.message.edit_text(
        f"💣 Мин: {mines}",
        reply_markup=render(key)
    )

    await callback.answer()


@dp.callback_query(F.data=="mode_flag")
async def flag(callback:CallbackQuery):

    key=(callback.message.chat.id,callback.from_user.id)

    games[key]["mode"]="flag"
    await callback.answer("🚩 Режим флагов")


@dp.callback_query(F.data=="mode_open")
async def open_mode(callback:CallbackQuery):

    key=(callback.message.chat.id,callback.from_user.id)

    games[key]["mode"]="open"
    await callback.answer("⛏ Режим открытия")


@dp.callback_query(F.data=="restart")
async def restart(callback:CallbackQuery):

    key=(callback.message.chat.id,callback.from_user.id)

    g=games[key]

    new_game(key,g["w"],g["h"],g["mines"])

    await callback.message.edit_text(
        f"💣 Мин: {g['mines']}",
        reply_markup=render(key)
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("c_"))
async def click(callback:CallbackQuery):

    key=(callback.message.chat.id,callback.from_user.id)

    now=time.time()

    if key in last_click:
        if now-last_click[key]<CLICK_DELAY:
            await callback.answer("⏳ Не так быстро")
            return

    last_click[key]=now

    g=games[key]

    if g["game_over"]:
        await callback.answer("Игра окончена")
        return

    _,x,y=callback.data.split("_")
    x=int(x)
    y=int(y)

    if g["opened"][y][x] and g["mode"]=="open":
        await callback.answer()
        return

    if g["mode"]=="flag":

        g["flags"][y][x]=not g["flags"][y][x]

    else:

        if g["first"]:

            g["field"]=generate_field(g["w"],g["h"],g["mines"],x,y)
            g["first"]=False

        if g["field"][y][x]=="M":

            g["game_over"]=True

            for yy in range(g["h"]):
                for xx in range(g["w"]):
                    if g["field"][yy][xx]=="M":
                        g["opened"][yy][xx]=True

            await callback.message.edit_text(
                "💥 БОМБА!",
                reply_markup=render(key)
            )

            await callback.answer()
            return

        open_area(g,x,y)

    try:
        await callback.message.edit_reply_markup(
            reply_markup=render(key)
        )
    except:
        pass

    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__=="__main__":
    asyncio.run(main())


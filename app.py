import asyncio

import aiosqlite
from aiohttp import web

from db_utils import db_get_one, insert_one, db_get_first
from tg_utils import post_message

BOT_TOKEN = "some_token"


async def get_player_id(db, user_id):
    select_player = "SELECT * FROM player WHERE telegram_id = :telegram_id"
    insert_player = "INSERT INTO player(telegram_id) VALUES(:telegram_id)"
    return await db_get_one(db, "id", select_player, telegram_id=user_id) or await insert_one(db, insert_player, telegram_id=user_id)


async def close_sessions(db, player_id):
    close_sessions = "UPDATE game_session SET is_over = 1 WHERE player = :player_id"
    await db.execute(close_sessions, {"player_id": player_id})


async def get_session_key(db, player_id):
    select_session = "SELECT id FROM game_session WHERE player = :player_id and is_over = 0"
    return await db_get_one(db, "id", select_session, player_id=player_id)


async def get_word_key(db, word):
    select_word = "SELECT id FROM words WHERE word = :word"
    return await db_get_one(db, "id", select_word, word=word)


async def new_session(db, player_id, difficult):
    select_word = """
        select w.id, w.word, count(*) as difficult
        from words as w
        inner join solutions as s on s.parent_word = w.id
		where not exists (
		        select gs.word from game_session as gs
                where gs.is_over = 1
                and gs.word = w.id
                and gs.player = :player_id
                and strftime('%Y%d%m%H%M%S', datetime('now')) - gs.timestamp < 100000000
		)
        group by w.id, w.word
        having difficult between :low and :high
        ORDER BY RANDOM() LIMIT 1
    """

    insert_session = """
        insert into game_session(player, word, timestamp) 
        values(:player_id, :word_id, strftime('%Y%d%m%H%M%S', datetime('now')))
    """

    levels = {
        1: (5, 20),
        2: (20, 50),
        3: (50, 500),
        4: (500, 5000)
    }

    low, high = levels.get(difficult, (5, 20))

    row = await db_get_first(db, select_word, low=low, high=high, player_id=player_id)

    word = row["word"]
    word_id = row["id"]
    solution_count = row["difficult"]

    await insert_one(db, insert_session, player_id=player_id, word_id=word_id)

    return word, solution_count


async def get_session(db, session_id):
    select_session = """
        select gs.id, gs.is_over, pw.word, 
		       ifnull(group_concat(sw.word, ';'), '') as solved, 
			   count(*) as solved_count, 
			   p.possible, 
			   p.possible_count - count(*) - 1 as possible_left
        from game_session as gs
        left join game_answers as ga on ga.session = gs.id
        inner join player as p on gs.player = p.id 
        inner join words as pw on gs.word = pw.id
        left join words as sw on ga.word = sw.id
        inner join (
                select s.parent_word, group_concat(cw.word, ';') as possible, count(*) as possible_count
                from solutions as s
                inner join words as cw on s.child_word = cw.id
                group by s.parent_word
            ) as p on gs.word = p.parent_word
        where gs.id = :session_id
        group by gs.id, gs.is_over, pw.word
    """
    return await db_get_first(db, select_session, session_id=session_id)


async def add_answer(db, session_id, word_id):
    insert_answer = "insert into game_answers(session, word) values(:session_id, :word_id)"
    await insert_one(db, insert_answer, session_id=session_id, word_id=word_id)


async def gameplay(text, commands, user_id):
    async with aiosqlite.connect("wfw.db3") as db:
        db.row_factory = aiosqlite.Row
        try:
            player_id = await get_player_id(db, user_id)
            session_id = await get_session_key(db, player_id)

            if session_id and not commands:
                word_id = await get_word_key(db, text)
                if not word_id:
                    return "Нет такого слова в словаре"

                session = await get_session(db, session_id)

                if text in session["solved"]:
                    return "Вы уже угадали такое слово"
                elif text in session["possible"]:
                    await add_answer(db, session_id, word_id)
                    return "Отлично, вы угадали. Осталось отгадать {} слов".format(
                        session["possible_left"]
                    )
                else:
                    return "Из слова {} невозможно составить слово {}".format(text, session["word"])
            else:
                if "start" in commands:
                    return "Привет, я бот-игра \"Слова из слова\", /new_game чтобы начать новую игру."
                elif "new_game" in commands:
                    return "Выберите уровень сложности: \r\n\r\n/easy\r\n/normal\r\n/hard\r\n/expert"
                else:
                    if "easy" in commands:
                        difficult = 1
                    elif "normal" in commands:
                        difficult = 2
                    elif "hard" in commands:
                        difficult = 3
                    elif "expert" in commands:
                        difficult = 4
                    else:
                        return "Вы делаете что-то неопнятное для меня."

                    # Close all sessions
                    await close_sessions(db, player_id)

                    word, solution_count = await new_session(db, player_id, difficult)
                    return "Ваше слово \"{}\", вам нужно отгадать {} слов которые можно из этого слова составить.".format(
                        word, solution_count)
        finally:
            await db.commit()


async def handle_message(request):
    data = await request.json()

    message = data.get("message", None)
    if message:
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message["text"]
        commands = [
            text[ent["offset"] + 1:ent["length"]]
            for ent in message["entities"]
            if ent["type"] == "bot_command"
        ]

        response = await gameplay(text, commands, user_id)

        asyncio.ensure_future(
            post_message(BOT_TOKEN, chat_id, response)
        )

    return web.json_response({"success": True})


def init():
    app = web.Application()
    app.router.add_post("/handle_message", handle_message)
    return app


if __name__ == '__main__':
    web.run_app(init(), host="localhost")

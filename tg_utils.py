from aiohttp import ClientSession


async def json_post(url, json_data):
    async with ClientSession() as session:
        try:
            return await session.post(url, json=json_data)
        except Exception as e:
            print("post error: '{}'".format(str(e)))


async def post_message(bot_token, chat_id, text, reply_id=None):
    url = "https://api.telegram.org/bot{}/sendMessage".format(bot_token)
    json_data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_id:
        json_data["reply_to_message_id"] = reply_id

    return await json_post(url, json_data)

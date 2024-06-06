import requests
from logic.battle import face_battle
from model import Player
from pathlib import Path
import os
from pprint import pprint
from slack_bolt import App, Ack
from uuid import uuid4
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    token=os.environ["SLACK_BOT_TOKEN"],
    process_before_response=True,
)

def just_ack(ack: Ack):
    print("ack")
    ack()

def judge(body, say):
    mention = body["event"]
    text = mention["text"]
    channel = mention["channel"]
    thread_ts = mention["ts"]
    parent_thread_ts = mention.get("thread_ts")

    if 'thread_ts' not in body['event']:
        say(text="スレッドで実行してください", channel=channel, thread_ts=thread_ts)
        return

    responses = app.client.conversations_replies(
        channel=channel,
        ts=parent_thread_ts
    )

    entries = []

    for message in responses["messages"]:

        files = message.get("files", [])
        if files == []:
            continue
        file = files[0]
        resp = requests.get(file["url_private_download"], headers={
            "Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"
        })
        filename = uuid4()
        path = Path(f"/tmp/{filename}")
        with open(path, "wb") as f:
            f.write(resp.content)

        profile = app.client.users_profile_get(
            user=message["user"]
        )["profile"]

        pprint(profile)
        player = Player(user_name=profile["display_name"], image_path=path)
        entries.append(player)
    
    if entries == []:
        say(text="エントリーしているプレイヤーがいません", channel=channel, thread_ts=thread_ts)
        return
    
    texts = text.split(" ")
    if len(texts) != 2:
        say(text="テーマを指定してください", channel=channel, thread_ts=thread_ts)
        return
    
    theme = texts[1]

    result = face_battle(theme=theme, players=entries)

    say(text=result.output(), channel=channel, thread_ts=thread_ts)

app.event("app_mention")(
    ack=just_ack,
    lazy=[judge]
)

def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)

if __name__ == "__main__":
    app.start()

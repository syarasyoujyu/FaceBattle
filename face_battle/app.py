import requests
from logic.battle import face_battle
from model import Player
from typing import Tuple
from pprint import pprint
from slack_bolt import App, Ack
from uuid import uuid4
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from PIL import Image
import os,base64
from jinja2 import Template 
from loguru import logger
from litellm import completion

app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    token=os.environ["SLACK_BOT_TOKEN"],
    process_before_response=True,
)

def just_ack(ack: Ack):
    print("ack")
    ack()


def resize_image(path:str, max_size:int=200):
    """画像をリサイズ"""
    with Image.open(path) as img:
        # 縮小する比率を計算する
        ratio = min(max_size / img.size[0], max_size / img.size[1])
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        
        # 画像をリサイズする
        resized_img = img.resize(new_size, Image.LANCZOS)
        
        resized_img.save(path)

def send_request_to_gpt4o(messages:list)->str:
    """リクエストを送信し、レスポンスを取得する関数"""
    try:
        response = completion(
            model="gpt-4o",
            messages=messages,
            api_key=os.environ["OPENAI_API_KEY"],
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(e)
    return "エラーが発生しました。"

def point_and_descript(theme:str,image_path:str)->Tuple[int,str]:
    """画像ファイル(png)を読み込んで、Gpt-4oにリクエストを送信する関数"""
    # ファイルをバイナリモードで開いて読み込む
    with open(image_path, 'rb') as image_file:
        resize_image(image_path)
        # ファイルの内容を読み込む
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    # data URIスキームに従ってフォーマットする
    image_url = f"data:image/png;base64,{encoded_string}"
    content_template="""
お題[{{theme}}]にどれだけ沿っている顔かを、100点満点でシビア目に、１点刻みで採点し、その点数をpointに書いてください。
その後、採点理由をdescriptionに簡潔に記述してください。
なお、画像は{{image_url}}です。
例:
{'point': 57, 'description': '恋人にとられた悲しさをしっかり表現しています。しかし、全体的に驚きの感情の強さが不足しており、眉や口の動きがやや弱いように感じられます。もう少し強い感情表現が必要です。'},
{'point': 34, 'description': '目の前に好きなアイドルが現れた際の驚きや喜びがあまり伝わってきません。見た目にもう少し輝きや表情の明確な変化があると点数が上がるでしょう'}
{'point': 47, 'description': '目の驚きはある程度表現できていますが、全体的な表情が淡泊で、サプライズプレゼントをもらった時の強い喜びや驚きが十分に感じ取れません。もう少し口元や顔全体の明確な変化があると良いでしょう。'}"""
    content=Template(content_template).render(theme=theme,image_url=image_url)    # メッセージリストを作成
    pprint(len(image_url))
    messages = [
        {
            "role": "system",
            "content": "あなたは返答をすべてJSON形式で出力します。{'point':,'description':}の形式で出力してください。"
            },
        {
            "role": "user",
            "content": content
            },
    ]
    
    # Azure OpenAIにリクエストを送信し、レスポンスを取得する
    response = send_request_to_gpt4o(messages)
    content=response[response.find("{"):response.find("}")]
    point_from=content.find('point')+7
    point_to=content.find('description')-3
    description_from=content.find('description')+15
    description_to=len(content)-3
    point_str=content[point_from:point_to+1]
    delete_strings=[',',' ','　','\n']
    for delete_string in delete_strings:
        point_str=point_str.replace(delete_string,'')
    point=int(point_str)
    description=content[description_from:description_to+1]
    return point,description

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

    texts = text.split(" ")
    if len(texts) != 2:
        say(text="テーマを指定してください", channel=channel, thread_ts=thread_ts)
        return
    
    theme = texts[1]
    
    for message in responses["messages"]:

        files = message.get("files", [])
        if files == []:
            continue
        file = files[0]
        resp = requests.get(file["url_private_download"], headers={
            "Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"
        })
        filename = uuid4()
        path = f"/tmp/{filename}.png"
        with open(path, "wb") as f:
            f.write(resp.content)

        profile = app.client.users_profile_get(
            user=message["user"]
        )["profile"]

        pprint(profile)
        point, description = point_and_descript(theme=theme, image_path=path)
        player = Player(user_name=profile["real_name"], image_path=path, point=point, description=description)
        entries.append(player)
    
    if entries == []:
        say(text="エントリーしているプレイヤーがいません", channel=channel, thread_ts=thread_ts)
        return

    result = face_battle(theme=theme, players=entries)

    say(text=result.output(theme=theme), channel=channel, thread_ts=thread_ts)

app.event("app_mention")(
    ack=just_ack,
    lazy=[judge]
)

def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)

if __name__ == "__main__":
    app.start()

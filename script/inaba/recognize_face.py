from openai import OpenAI
import base64
import jinja2
from jinja2 import Template 
from loguru import logger
import os,openai
from litellm import completion

def send_request_to_gpt4o(messages:list)->str|None:
    """リクエストを送信し、レスポンスを取得する関数"""
    try:
        response = completion(
            model="gpt-4o",
            messages=messages,
            api_key=os.environ['OPENAI_API_KEY'],
        )
        print(response)
        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(e)
    return None
    
def make_title()->str:
    """タイトルを作成する関数"""
    title_content="""あなたは、とても楽しく、友達たちとエンジョイできるようなパーティーの主催者です。そこで、
あなたはどれだけお題に沿った顔を披露できるかというゲームを考えました。このゲームにピッタリで、採点できそうなお題を1つだけ考えてくださいできるだけパーティーの盛り上がりにつながるようなお題を考えてください。
なお、お題以外の情報を入力することを禁止します。
例：
移動教室を間違えた顔
マンガのネタバレを食らった顔
お風呂に入るのが嫌な顔
マリオカートで優勝した顔
先生をママと呼んだ時の顔
ハメ技を食らった顔
"""
    messages=[
        {
            "role": "user",
            "content": title_content
        }
    ]
    response=send_request_to_gpt4o(messages)
    return response

# メイン関数
def Judje(title:str,file_path:str)->str:
    """画像ファイル(png)を読み込んで、Gpt-4oにリクエストを送信する関数"""
    # ファイルをバイナリモードで開いて読み込む
    with open(file_path, 'rb') as image_file:
        # ファイルの内容を読み込む(３万以上だとOUT！)
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # data URIスキームに従ってフォーマットする
    image_url = f"data:image/png;base64,{encoded_string}"
    content_template="""
お題[{{title}}]にどれだけ沿っている顔かを、100点満点でシビア目に採点し、その点数をpointに書いてください。
その後、採点理由をdescriptionに簡潔に記述してください。
なお、画像は{{image_url}}です。
例:
{'point': 60, 'description': '恋人にとられた悲しさをしっかり表現しています。しかし、全体的に驚きの感情の強さが不足しており、眉や口の動きがやや弱いように感じられます。もう少し強い感情表現が必要です。'},
{'point': 30, 'description': '目の前に好きなアイドルが現れた際の驚きや喜びがあまり伝わってきません。見た目にもう少し輝きや表情の明確な変化があると点数が上がるでしょう'}"""
    content=Template(content_template).render(title=title,image_url=image_url)
    print(len(image_url))
    # メッセージリストを作成
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
    
    return response

if __name__ == '__main__':
    with open ('script/inaba/face_paths.txt','rb') as f:
        file_paths=f.read().splitlines()[:1]
    title=make_title()
    for file_path in file_paths:
        Judje(title,file_path)
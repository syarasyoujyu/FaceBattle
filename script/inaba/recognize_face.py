import openai
import base64
import Jinja2
from jinja2 import Template 
from loguru import logger
import os


def send_request_to_azure_openai(messages:str)->str|None:
    """Azure OpenAIにリクエストを送信し、レスポンスを取得する関数"""
    try:
        openai.api_key = os.environ["API_KEY"]

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            temperature=0.5,
            stream=False,
            top_p=1.0,
            stop=None,
            presence_penalty=0,
            frequency_penalty=0,
            messages=messages
        )
        return response
    except Exception as e:
        logger.warning(e)
    return None
    
def make_title()->str:
    """タイトルを作成する関数"""
    title_content="""あなたは、とても楽しく、友達たちとエンジョイできるようなパーティーの主催者です。そこで、
あなたはどれだけお題に沿った顔を披露できるかというゲームを考えました。このゲームにピッタリなお題を考えてください。"""
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": title_content
                }
            ]
        }
    ]
    response=send_request_to_azure_openai(messages)
    return response['choices'][0]['message']['content']

# メイン関数
def Judje(title:str,file_path:str)->str:
    """画像ファイル(png)を読み込んで、Azure OpenAIにリクエストを送信する関数"""
    # ファイルをバイナリモードで開いて読み込む
    with open(file_path, 'rb') as image_file:
        # ファイルの内容を読み込む
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # data URIスキームに従ってフォーマットする
    image_url = f"data:image/png;base64,{encoded_string}"
    content_template="""{{title}}にどれだけ沿っている顔かを、100点満点で採点してください。"""
    content=Template(content_template).render(title=title)
    # メッセージリストを作成
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "system",
                    "text": "点数のみを入力してください。点数以外を入力することを禁止します。"
                },
                {
                    "type": "text",
                    "text": content
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
    ]

    # Azure OpenAIにリクエストを送信し、レスポンスを取得する
    response = send_request_to_azure_openai(messages)

    # レスポンスにエラーが含まれているかチェックする
    if 'error' in response:
        logger.warning(response['error'])
        return None
    
    # 応答内容を取得する
    response_content = response['choices'][0]['message']['content']
    return response_content

if __name__ == '__main__':
    title=make_title()
    with open ('script/inaba/face_paths.txt','rb') as f:
        file_paths=f.read().splitlines()
    for file_path in file_paths:
        Judje(title,file_path)

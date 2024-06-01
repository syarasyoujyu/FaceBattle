import openai
import base64
import Jinja2
from jinja2 import Template 
from loguru import logger
# OpenAI APIの各種キーを設定
API_KEY = "APIキーをここに指定"
API_BASE = "エンドポイントを指定"
API_TYPE = "azure"
API_VERSION = "2023-05-15"
GPT_MODEL_NAME = "GPT-4oのデプロイ名をここに指定"

# Azure OpenAIにリクエストを送信し、レスポンスを取得する関数
def send_request_to_azure_openai(messages:str)->None:
    try:
        openai.api_key = API_KEY
        openai.api_base = API_BASE
        openai.api_type = API_TYPE
        openai.api_version = API_VERSION

        response = openai.ChatCompletion.create(
            engine=GPT_MODEL_NAME,
            temperature=0.5,
            stream=False,
            top_p=1.0,
            stop=None,
            presence_penalty=0,
            frequency_penalty=0,
            messages=messages
        )
    except Exception as e:
        logger.warning(e)
    return None
    

# メイン関数
def Judje(title:str)->str:
    # PNGファイルのパスを指定
    file_path = '<ここにインプットしたいPNGファイルパスを指定'

    # ファイルをバイナリモードで開いて読み込む
    with open(file_path, 'rb') as image_file:
        # ファイルの内容を読み込む
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # data URIスキームに従ってフォーマットする
    image_url = f"data:image/png;base64,{encoded_string}"
    content_template="""{{title}}にどれだけ沿っている顔か採点してください。"""
    content=Template(content_template).render(title=title)
    # メッセージリストを作成
    messages = [
        {
            "role": "user",
            "content": [
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
        print(response['error'])
    else:
        # 応答内容を取得する
        response_content = response['choices'][0]['message']['content']
        print(response_content)

if __name__ == '__main__':
    main()

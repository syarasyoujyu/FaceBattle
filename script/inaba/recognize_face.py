from openai import OpenAI
import base64
import jinja2
from jinja2 import Template 
from loguru import logger
import os,openai
from litellm import completion
from dotenv import load_dotenv
from PIL import Image
from PIL import Image
import base64
import os
from pydantic import BaseModel
#環境変数を読み込む
load_dotenv()

class Player(BaseModel):
    name:str
    point:int
    description:str

def resize_image(path, max_size=300):
    """画像をリサイズ"""
    with Image.open(path) as img:
        # 縮小する比率を計算する
        ratio = min(max_size / img.size[0], max_size / img.size[1])
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        
        # 画像をリサイズする
        resized_img = img.resize(new_size, Image.LANCZOS)
        
        # 画像を保存する
        resized_img.save(path)

def send_request_to_gpt4o(messages:list)->str|None:
    """リクエストを送信し、レスポンスを取得する関数"""
    try:
        response = completion(
            model="gpt-4o",
            messages=messages,
            api_key=os.environ['API_KEY'],
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(e)
    return None

# メイン関数
def Judje(title:str,file_path:str)->str:
    """画像ファイル(png)を読み込んで、Gpt-4oにリクエストを送信する関数"""
    # ファイルをバイナリモードで開いて読み込む
    with open(file_path, 'rb') as image_file:
        # ファイルの内容を読み込む(３万以上だとOUT！)
        resize_image(file_path)
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    # data URIスキームに従ってフォーマットする
    image_url = f"data:image/png;base64,{encoded_string}"
    content_template="""
お題[{{title}}]にどれだけ沿っている顔かを、100点満点でシビア目に、１点刻みで採点し、その点数をpointに書いてください。
その後、採点理由をdescriptionに簡潔に記述してください。
なお、画像は{{image_url}}です。
例:
{'point': 57, 'description': '恋人にとられた悲しさをしっかり表現しています。しかし、全体的に驚きの感情の強さが不足しており、眉や口の動きがやや弱いように感じられます。もう少し強い感情表現が必要です。'},
{'point': 34, 'description': '目の前に好きなアイドルが現れた際の驚きや喜びがあまり伝わってきません。見た目にもう少し輝きや表情の明確な変化があると点数が上がるでしょう'}
{'point': 47, 'description': '目の驚きはある程度表現できていますが、全体的な表情が淡泊で、サプライズプレゼントをもらった時の強い喜びや驚きが十分に感じ取れません。もう少し口元や顔全体の明確な変化があると良いでしょう。'}"""
    content=Template(content_template).render(title=title,image_url=image_url)    # メッセージリストを作成
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
    Json_response=response[response.find("{"):response.find("}")]
    return Json_response

def praise_top_player(top_player:Player,title:str)->str:
    """優勝者を褒めるコメントを作成する関数"""
    praise_template="""{{top_player_description}}から、{{top_player_name}}さんのどこが評価されたのかを述べて、ほめてください。なお、この大会は「{{title}}の真似をする大会」で、コメントは一文でお願いします。
例1:SSAMMAさんは、怒りの表情がとてもよく表れているという点で、非常に優れています!
例2:UMMAさんは、マリオカートで勝った時特有の喜びがとてもよく表れていて、素晴らしいです!
"""
    top_player_name,top_player_description=top_player.name,top_player.description
    praise_content=Template(source=praise_template).render(top_player_name=top_player_name,top_player_description=top_player_description,title=title)
    messages=[
        {
            "role":"user",
            "content":praise_content
        }
    ]
    response=send_request_to_gpt4o(messages)
    return response
    

def make_comment(top_players:list,title:str)->str:
    """優勝者の名前を受け取り、コメントを作成する関数"""
    top_player_names=[player.name for player in top_players]
    praise_comments=[praise_top_player(player,title) for player in top_players]
    point=top_players[0].point
    comment="""優勝者は{{point}}点で、
{% for top_player_name  in top_player_names %}{{top_player_name}}さん{% if loop.index < top_player_names|length %},{% endif %}{% endfor %}
です！おめでとうございます！
{% for praise_comment in praise_comments %}
{{praise_comment}}
{% endfor %}
"""
    comment=Template(comment).render(point=point,top_player_names=top_player_names,praise_comments=praise_comments)
    return comment
    
    


if __name__ == '__main__':
    #playerのリストを作成
    players=[]
    with open ('script/inaba/face_paths.txt','rb') as f:
        file_paths=f.read().splitlines()
    title="怒っている顔"
    for file_path in file_paths:
        content=Judje(title,file_path)
        
        #pointとdescriptionを取得
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
        player=Player(name='inaba',point=point,description=description,image_url=file_path)
        players.append(player)
    #playerをpointでソート
    players.sort(key=lambda x:x.point,reverse=True)
    #優勝者を決める
    top_point=players[0].point
    top_players=[player for player in players if player.point==top_point]
    top_player_names=[player.name for player in top_players]
    comment=make_comment(top_players,title)
    print(comment)
    
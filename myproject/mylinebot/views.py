from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser

from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, TextMessage
from linebot.models import ConfirmTemplate, MessageAction, TemplateSendMessage,PostbackEvent,PostbackAction
import pandas as pd
from rdflib.plugins.sparql import prepareQuery
import os
import openai
from rdflib import Graph
import json

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
# 壓瘡相關 start
question_set="""
CQ1.1 What factors put individuals at risk for pressure injury development?
CQ1.2 What are the unique pressure injury risk factors to consider for special populations (if any)?
CQ1.3 What are accurate and effective methods for pressure injury risk assessment?
CQ2.1 Are scale/ tools effective methods to assess the skin and soft tissue?
CQ2.2 What are effective methods of assessing erythema?
CQ2.3 Is ultrasound an effective method for assessing the skin and soft tissue?
CQ2.4 Is evaluation of skin and tissue moisture an effective method of assessing the skin and soft tissue?
CQ2.5 Is evaluation of skin and tissue temperature an effective method of assessing the skin and soft tissue?
CQ2.6 What additional technologies are accurate and effective methods of assessing skin and soft tissue?
CQ2.7 What methods are effective for assessing skin and soft tissue in individuals with darkly pigmented skin?
CQ3.1 Is massage effective in preventing pressure injuries?
CQ3.2 Are topical products effective in preventing pressure injuries?
CQ3.3 Are prophylactic dressings effective for preventing pressure injuries?
CQ3.4 Are continence management strategies effective in preventing and treating pressure injuries?
CQ3.5 Are low friction or microclimate control fabrics effective for preventing pressure injuries?
CQ4.1 What are accurate and effective methods for assessing nutritional status of individuals with or at risk of pressure injuries?
CQ4.2 What nutritional interventions are effective in preventing pressure injuries?
CQ4.3 Is there an ideal nutritional regimen to reduce the risk of pressure injuries, and if so, what should it include?
CQ4.4 Are any nutritional supplements (e.g. formulas, specific vitamins/minerals) effective in reducing risk of pressure injury development?
CQ4.5 What nutritional interventions are effective in supporting pressure injury healing?
CQ4.6 Is there an optimal nutritional regimen to promote healing of pressure injuries, and if so, what should it include?
CQ4.7 Are any specific oral nutritional supplements or formula effective in promoting healing of pressure injuries?
CQ4.8 Nutrition for Neonates and children
CQ5.1 How often should repositioning be performed to reduce the risk of pressure injuries?
CQ5.2 What criteria should be used to determine and monitor frequency of turning?
CQ5.3 What positioning techniques are most effective in redistributing pressure and preventing shear?
CQ5.4 Do programs of early mobilization affect pressure injury rates?
CQ5.5 For Spinal cord.
CQ5.6 For critical ill.
CQ5.7 For Operating room/Surgery.
CQ6.1 What factors put individuals at risk for heel pressure injury development?
CQ6.2 What are accurate and effective methods for assessing heel skin and tissue?
CQ6.3 What are effective local management strategies (e.g., skin care, prophylactic dressings) in preventing heel pressure injuries?
CQ6.4 What heel repositioning interventions are effective in preventing heel pressure injuries?
CQ6.5 What support surfaces and devices are effective in preventing heel pressure injuries?
CQ6.6 What are effective strategies for treating heel pressure injuries?
CQ6.7 What factors affect healing of heel pressure injuries?
CQ7.1 What reactive support surfaces are effective in preventing pressure injuries?
CQ7.2 What active support surfaces are effective in preventing pressure injuries?
CQ7.3 When should an active support surface be used to prevent pressure injuries?
CQ7.4 What is the most effective seating support surface for preventing pressure injuries?
CQ7.5 What reactive support surfaces are effective in supporting pressure injury healing?
CQ7.6 What active support surfaces are effective in supporting pressure injury healing?
CQ7.7 When should an active support surface be used to support pressure injury healing?
CQ7.8 What is the most effective seating support surface for healing pressure injuries?
CQ7.9 Support Surface Use During Transportation.
CQ7.10 For Obesity.
CQ7.11 For Surgery.
CQ8.1 What factors should be considered when selecting and fitting a medical device?
CQ8.2 What local management strategies are effective in preventing MDRPIs?
CQ8.3 Is a prophylactic dressing effective for preventing MDRPIs? If so, what factors should be considered when selecting a prophylactic dressing?
"""
# dict={'label':'','guildline':''}
#可測試問題範例
# 怎樣會讓增加足跟壓力損傷的可能？
#有新生兒和兒童的營養相關的建議嗎?
openai.api_key = 'Plz Input Your OPEN_AI API_KEY'


# # 壓瘡相關 end
user_dialogues = {}

def update_user_dialogue(user_id, message):
    """更新用對話歷史紀錄。"""
    if user_id not in user_dialogues:
        user_dialogues[user_id] = []
    user_dialogues[user_id].append(message)
    print("=====歷史紀錄=====")
    print(user_dialogues[user_id])

def get_user_dialogue(user_id):
    """提取用戶對話歷史紀錄。"""
    return user_dialogues.get(user_id, [])

def send_question_to_chatgpt(user_id):
    """把問題及對話紀錄丟給gpt"""
    dialogue_history = get_user_dialogue(user_id)
    response = send_question_to_openai_gpt3_normalQuestion(dialogue_history)
    # 更新對話紀錄，包括 ChatGPT 的回覆
    update_user_dialogue(user_id, {"chatgpt": response})
    return response

def send_question_to_openai_gpt3_normalQuestion(dialogue_history):
    dialogue_history_str = "\n".join(
    [f"{key}: {value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)}" 
     for message in dialogue_history 
     for key, value in message.items()]
)

    print(dialogue_history_str)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {'role': 'system','content': f'你是一個處理壓瘡的機器人，使用者會向你提出一些問題及相關的解決方法！，請直接回答使用者問題即可！ 以下為你與用戶先前的對話記錄:\n{dialogue_history_str}'},
            {'role': 'user','content': '如何預防壓瘡？'},
            {'role': 'assistant', 'content': '''您可為避免壓瘡出現，提供以下建議：\n
1. 規律翻身：協助病患定期改變體位，避免長時間施壓於同一區域。\n
2. 保持乾燥：確保皮膚保持乾燥，避免長時間接觸濕氣。\n
3. 良好的營養：提供充足的營養，包括蛋白質、維生素和礦物質，以促進皮膚健康。\n
4. 使用合適的壓瘡墊：選擇適合的床墊或坐墊，以分散壓力並減少接觸力。\n
5. 檢查皮膚：定期檢查皮膚，尤其是容易受壓的部位，如臀部、腳底和脊椎。\n
6. 定期按摩：輕輕按摩受壓部位，促進血液循環並減少壓力。\n
7. 注意溢傷液：當壓瘡出現時，及早處理溢傷液，避免感染和加重傷口。\n
8. 教育患者及照護者：提供患者及其照護者有關壓瘡預防和護理的教育，以增加其對壓瘡注意事項的了解。\n

希望以上建議能對您有所幫助！如果您有其他問題或需要進一步的解釋，請隨時告訴我。'''},
        ]
    )
    return response.choices[0].message.content


def send_question_to_openai_gpt3(question):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
        {"role": "system", "content": "你是一個處理壓瘡的機器人，使用者會input口語化的問題，請回傳最相關的代碼及問題，並用{'label':'','guildline':''}此json格式回傳即可，不可以加入其他元素，以下是你所有的問題集："+question_set+"。如果使用者所輸入的內容與壓瘡內容無關，請回答{'label':'None','guildline':'None'}，絕對不可以用其他方式回應！"},
        {"role": "user", "content": "按摩能有效預防壓力性傷害嗎？"},            
        {"role": "assistant", "content": "{'label':'CQ3.1','guildline':'Is massage effective in preventing pressure injuries?'}"},
        {"role": "user", "content": "選擇和安裝醫療器材時應考慮哪些因素？"},            
        {"role": "assistant", "content": "{'label':'CQ8.1','guildline':'What factors should be considered when selecting and fitting a medical device?'}"},
        {"role": "user", "content": "你是誰？"},            
        {"role": "assistant", "content": "{'label':'None','guildline':'None'}"},
        {"role": "user", "content": question},
    ]
    )
    return response.choices[0].message.content

def perform_rdf_query(cq_label):
    g = Graph()
    g.parse("myproject/mylinebot/Guideline0607_MAX.ttl", format="turtle")

    title_label = cq_label[2]  # 例如 '8' 從 'CQ8.1'

    query = prepareQuery(f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX PI: <http://example.org/PI#>

    SELECT ?lab ?CQ_comment ?RefNo ?SOR_lab ?SOE_lab ?comment
    WHERE {{
        ?CQ rdf:type PI:CQ{title_label}_Clinical_Question;
            rdfs:comment ?CQ_comment;
            rdfs:label ?lab;
            PI:has_guideline ?RefNo.
        ?RefNo PI:has_recommendation ?SOR;
                PI:has_evidence ?SOE;
                rdfs:comment ?comment.
        ?SOR rdfs:label ?SOR_lab.
        ?SOE rdfs:label ?SOE_lab.
        FILTER(CONTAINS(?lab, "{cq_label}"))
    }}
    ORDER BY (?CQ)
    """)

    results = g.query(query)
    return [(row.RefNo.toPython(), row.SOR_lab.toPython(), row.SOE_lab.toPython(), row.comment.toPython()) for row in results]
def format_rdf_response(response):
    formatted_responses = []
    for item in response:
        formatted_message = (
            f"原則編號: {item[0]}\n"
            f"推薦強度: {item[1]}\n"
            f"證據強度: {item[2]}\n"
            f"原則內容: {item[3]}"
        )
        formatted_responses.append(formatted_message)
    return formatted_responses
def perform_rdf_query2(qrg_label):
    g = Graph()
    # g.parse("path/to/your/Guideline0607_MAX.ttl", format="turtle")

    query = prepareQuery(f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX PI: <http://example.org/PI#>
SELECT distinct ?comment ?SOE_lab ?SOR_lab ?part_lab ?chapter_com 
?subHeading_com ?CQ ?CQ_com ?QI ?QI_com ?SP_lab
WHERE {{
      SERVICE <http://localhost:3030/temp_inf/query> {{   
        {{PI:{qrg_label} rdfs:comment ?comment; 
	 PI:has_recommendation ?SOR;
	PI:has_evidence ?SOE; 
	 rdf:type ?chapter. 
	 ?SOR rdfs:label ?SOR_lab.
	?SOE rdfs:label ?SOE_lab. 
	?chapter rdfs:subClassOf ?part;
	 rdfs:comment ?chapter_com. 
	?part rdfs:subClassOf PI:Knowledge_Structure;
	 rdfs:label ?part_lab.
	optional {{
	 ?SubHeading PI:has_guideline PI:{qrg_label}; 
	 rdf:type PI:SubHeadings;
	rdfs:comment ?subHeading_com. }} }}
	
	UNION {{ optional {{
	 ?CQ PI:has_guideline PI:{qrg_label}; 
	 rdf:type PI:Clinical_Questions;
	 rdfs:comment ?CQ_com. }} }}
	 
	UNION {{ optional {{
	 ?QI PI:has_guideline PI:{qrg_label}; 
	 rdf:type PI:Quality_indicators;
	 rdfs:comment ?QI_com. }} }}
	 
	UNION {{ optional {{
	 PI:{qrg_label} rdf:type ?SP.
	?SP rdfs:subClassOf PI:Special_Populations;
	 rdfs:label ?SP_lab. }} }}  
    }}
    }}
    """  )
    results = g.query(query)
    return [(row.comment, row.SOE_lab, row.SOR_lab, row.part_lab, row.chapter_com, row.subHeading_com, row.CQ, row.CQ_com, row.QI, row.QI_com, row.SP_lab) for row in results]

def format_rdf_response2(response):
    formatted_responses = []
    titles = ["Comment", "SOE Label", "SOR Label", "Part Label", "Chapter Comment", 
              "SubHeading Comment", "CQ", "CQ Comment", "QI", "QI Comment", "SP Label"]

    for item in response:
        formatted_message_lines = []
        for title, value in zip(titles, item):
            if value:  # 檢查值是否存在
                formatted_message_lines.append(f"{title}: {value}")
        
        formatted_message = "\n".join(formatted_message_lines)
        formatted_responses.append(formatted_message)

    return formatted_responses



@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
 
        try:
            events = parser.parse(body, signature)  # 傳入的事件
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
 
        for event in events:
            if isinstance(event, MessageEvent):  # 如果有訊息事件
                user_id = event.source.user_id
                user_message = event.message.text

                # 更新用户對話歷史
                update_user_dialogue(user_id, {"user": user_message})
                print(event.message.text)
                if event.message.text == "@開始發問":
                    line_bot_api.reply_message(  # 回復傳入的訊息文字
                    event.reply_token,
                    TextSendMessage(text='您好，我是壓瘡小幫手，有什麼問題都可以問我哦！輸入問題後我會根據壓瘡指南給您對應的資訊哦！如果有錯誤的話建議再重新打一次，內容盡量完整一點，謝謝您。')
                )

                
                elif '@' in event.message.text:
                    user_dialogues[user_id] = []#清空先前對話紀錄，太多會超出提問範圍
                    reCQ = send_question_to_openai_gpt3(event.message.text)
                    json_string = reCQ.replace("'", '"')
                    # 使用 json.loads() 转换为字典
                    dictionary = json.loads(json_string)
                    cq_label = dictionary["label"]
                
                    if cq_label=='None':
                        line_bot_api.reply_message(  # 回復傳入的訊息文字
                        event.reply_token,
                        TextSendMessage(text='查無結果')
                    )
                    else:
                        # 發送確認消息和按鈕模板，包括 cq_label
                        text=""
                        confirm_template_message = TemplateSendMessage(
                            alt_text='Confirm template',
                            template=ConfirmTemplate(
                                text=f"符合的問題為{dictionary['guildline']}",
                                actions=[
                                    PostbackAction(label="是", data=f"confirm_yes,{cq_label}"),
                                    PostbackAction(label="否", data="confirm_no")
                                ]
                            )
                        )
                        # 更新用户對話歷史
                        update_user_dialogue(user_id, {"user": user_message})
                        # 更新對話紀錄，包括 ChatGPT 的回覆
                        update_user_dialogue(user_id, {"chatgpt": text})
                        
                        line_bot_api.reply_message(event.reply_token, confirm_template_message)
                else:
                    response=send_question_to_chatgpt(user_id)
                    #聊天模式
                    line_bot_api.reply_message(  # 回復傳入的訊息文字
                    event.reply_token,
                    TextSendMessage(text=response)
                )

            elif isinstance(event, PostbackEvent):  # 處理按鈕的回應
                data = event.postback.data.split(',')

                if data[0] == "confirm_yes":
                    cq_label = data[1]
                    # 使用 cq_label 進行SPARQL查詢
                    ans = perform_rdf_query(cq_label)
                    formatted_ans = format_rdf_response(ans)

                    # 提取所有的 QRG 編號
                    principle_numbers = []
                    for msg in formatted_ans:
                        split_text = msg.split("http://example.org/PI#")
                        if len(split_text) > 1:
                            principle_number = split_text[1].split("\n")[0]
                            principle_numbers.append(principle_number)

                    # 對每個編號進行處理並發送推送消息
                    user_id = event.source.user_id  # 替換為獲取用戶ID的適當方法
                    for number in principle_numbers:
                        ans2 = perform_rdf_query2(number)
                        formatted_ans2 = format_rdf_response2(ans2)
                        combined_message = "\n".join(formatted_ans2)
                        message = TextSendMessage(text=combined_message)
                        line_bot_api.push_message(user_id, message)
                        # 更新對話紀錄，包括 ChatGPT 的回覆
                        update_user_dialogue(user_id, {"chatgpt": combined_message})



                elif data[0] == "confirm_no":
                    # 提醒用戶重新輸入問題
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='請重新輸入問題')
                    )

        return HttpResponse()
    else:
        return HttpResponseBadRequest()

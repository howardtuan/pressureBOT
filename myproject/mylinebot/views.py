from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser

from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, TextMessage

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
openai.api_key = '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'


# 壓瘡相關 end

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
            f"Reference No: {item[0]}\n"
            f"SOR Label: {item[1]}\n"
            f"SOE Label: {item[2]}\n"
            f"Comment: {item[3]}"
        )
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
                print(event.message.text)
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
                    ans = perform_rdf_query(cq_label)
                    formatted_ans = format_rdf_response(ans)
                    messages = [TextSendMessage(text="符合的問題為"+dictionary["guildline"])]
                    messages.extend([TextSendMessage(text=msg) for msg in formatted_ans])

                    # 一次回復多條訊息
                    line_bot_api.reply_message(
                        event.reply_token,
                        messages
                    )
                    print(ans)
                    print('=====')
                    print(str(ans))
                
        
        return HttpResponse()
    else: 
        return HttpResponseBadRequest()


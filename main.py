# 安装依赖 pip3 install requests html5lib bs4 schedule

import time
import requests
import json
import schedule
from bs4 import BeautifulSoup


# 从测试号信息获取
appID = "wx5e968a83d0d1f6f5"
appSecret = "a2f72f2cfafaaa600fb970e2b3c29a2e"
#收信人ID即 用户列表中的微信号，见上文
OPEN_IDS = [
    "oB4rx2MnJWT5rX6iGtdTG_rOP8IE",          # 原来的（女朋友）
    "oB4rx2NzwJGsDwSXT7yE3ILBNvSo"           # 新加的这个人
]
# 天气预报模板ID
weather_template_id = "XQc7dLCTV7m_GKBo3D6hVZjnr8dXz3Yc3ewUwc8sPds"
# 时间表模板ID
timetable_template_id = ""


def get_weather(my_city):
    import os

    # 临时硬编码新 Key（本地测试用，测试完注释掉或删除这行）
    api_key = "6801c91aa4ebf3a66c1664fc0caa7d36" # ← 把你的新 Key 粘贴在这里，不要有空格或换行

    # 正式用 secrets（测试完恢复这行）
    # api_key = os.getenv("WEATHER_API_KEY")
    # if not api_key:
    #     print("错误：未找到 WEATHER_API_KEY")
    #     return "鲁山县", "获取失败", "未知", "未知风"

    adcode = "410423"  # 鲁山县正确 adcode

    url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={api_key}&city={adcode}&extensions=all"

    try:
        resp = requests.get(url, timeout=10, verify=False).json()
        print("高德API完整响应:", resp)  # 调试用，看返回什么

        if resp.get("status") != "1":
            print("API错误:", resp.get("info"))
            return "鲁山县", "API错误", "未知", "未知风"

        city_name = "鲁山县"
        weather_desc = "未知"
        wind_str = "未知风"
        temp_range = "暂无数据"

        # 优先实时
        if "lives" in resp and resp["lives"]:
            live = resp["lives"][0]
            weather_desc = live.get("weather", "未知")
            wind_str = f"{live.get('winddirection', '未知')}风 {live.get('windpower', '未知')}级"
            current_temp = live.get("temperature", "未知")
            temp_range = f"{current_temp}℃ (实时)"

        else:
            print("无实时数据(lives缺失)，使用预报模拟")

        # 预报补充
        if "forecasts" in resp and resp["forecasts"]:
            today = resp["forecasts"][0]["casts"][0]
            weather_desc = today.get("dayweather", weather_desc)  # 白天天气优先
            wind_str = f"{today.get('daywind', '未知')}风 {today.get('daypower', '未知')}级"
            temp_range = f"{today['nighttemp']}～{today['daytemp']}℃"
            city_name = resp["forecasts"][0].get("city", city_name)

        print(f"最终提取: 城市={city_name}, 温度={temp_range}, 天气={weather_desc}, 风={wind_str}")
        return city_name, temp_range, weather_desc, wind_str

    except Exception as e:
        print(f"请求/解析失败: {e}")
        return "鲁山县", "网络异常", "未知", "未知风"

def get_access_token():
    # 获取access token的url
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}' \
        .format(appID.strip(), appSecret.strip())
    response = requests.get(url).json()
    print(response)
    access_token = response.get('access_token')
    return access_token


def get_daily_love():
    # 每日一句情话
    url = "https://api.lovelive.tools/api/SweetNothings/Serialization/Json"
    r = requests.get(url)
    all_dict = json.loads(r.text)
    sentence = all_dict['returnObj'][0]
    daily_love = sentence
    return daily_love

def send_weather(access_token, weather):
    import datetime
    today = datetime.date.today()
    today_str = today.strftime("%Y年%m月%d日")

    for open_id in OPEN_IDS:  # 循环发送给每个人
        body = {
            "touser": open_id.strip(),
            "template_id": weather_template_id.strip(),
            "url": "https://weixin.qq.com",
            "data": {
                "date": {
                    "value": today_str
                },
                "region": {
                    "value": weather[0]
                },
                "weather": {
                    "value": weather[2]
                },
                "temp": {
                    "value": weather[1]
                },
                "wind_dir": {
                    "value": weather[3]
                },
                "today_note": {
                    "value": get_daily_love()
                }
            }
        }
        url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
        response = requests.post(url, json=body)
        print(f"发送给 {open_id[:10]}... 的天气消息结果: {response.text}")
def send_timetable(access_token, message):
    for open_id in OPEN_IDS:
        body = {
            "touser": open_id,
            "template_id": timetable_template_id.strip(),
            "url": "https://weixin.qq.com",
            "data": {
                "message": {"value": message}
            }
        }
        url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
        response = requests.post(url, json=body)
        print(f"发送给 {open_id[:10]}... 的 timetable 结果: {response.text}")



def weather_report(city):
    # 1.获取access_token
    access_token = get_access_token()
    # 2. 获取天气
    weather = get_weather(city)
    print(f"天气信息： {weather}")
    # 3. 发送消息
    send_weather(access_token, weather)


def timetable(message):
    # 1.获取access_token
    access_token = get_access_token()
    # 3. 发送消息
    send_timetable(access_token, message)


if __name__ == '__main__':
    weather_report("鲁山")  # my_city 参数现在不影响adcode，但保持调用习惯
    # timetable(...) 如果需要
    # timetable("第二教学楼十分钟后开始英语课")

    # schedule.every().day.at("18:30").do(weather_report, "南京")
    # schedule.every().monday.at("13:50").do(timetable, "第二教学楼十分钟后开始英语课")
    #while True:
    #    schedule.run_pending()
    #    time.sleep(1)

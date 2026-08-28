"""Minh hoạ FUNCTION CALLING thuần với Google Gemini SDK.

Tool `get_weather` được định nghĩa schema thủ công VÀ thực thi ngay trong
chính file app này. Model chỉ QUYẾT ĐỊNH gọi tool nào; app mới là nơi chạy.

Cách chạy:
    pip install -r ../requirements.txt
    export GEMINI_API_KEY=...
    python weather_function_calling.py
"""

import json
import time

import httpx
from google import genai
from google.genai import types

client = genai.Client()

MODEL = "gemini-3.6-flash"

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế "
    "(ví dụ: mang ô, mặc áo mỏng, ...)."
)

# 1. App tự định nghĩa schema của tool
get_weather_declaration = types.FunctionDeclaration(
    name="get_weather",
    description="Lấy thời tiết hiện tại của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(
                type=types.Type.STRING, description="Tên thành phố"
            )
        },
        required=["city"],
    ),
)

get_weather_forecast_declaration = types.FunctionDeclaration(
    name="get_weather_forecast",
    description="Lấy dự báo thời tiết thật cho ngày mai và ngày kia của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(
                type=types.Type.STRING,
                description="Tên thành phố, ví dụ Hà Nội hoặc Đà Nẵng",
            )
        },
        required=["city"],
    ),
)

TOOLS = [
    types.Tool(
        function_declarations=[
            get_weather_declaration,
            get_weather_forecast_declaration,
        ]
    )
]


# 2. App tự thực thi tool (trong thực tế sẽ gọi API thời tiết thật)
def get_weather(city: str) -> str:
    """Trả về thời tiết (mock) của *city*. Dùng làm tool cho model."""
    mock_data = {
        "Hà Nội": {
            "nhiệt_độ": "29°C",
            "thời_tiết": "trời mưa nhẹ",
            "độ_ẩm": "82%",
            "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"},
        },
        "Hồ Chí Minh": {
            "nhiệt_độ": "33°C",
            "thời_tiết": "mưa rào",
            "độ_ẩm": "75%",
            "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"},
        },
        "Đà Nẵng": {
            "nhiệt_độ": "30°C",
            "thời_tiết": "nhiều mây",
            "độ_ẩm": "78%",
            "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"},
        },
    }
    default = {"nhiệt_độ": "28°C", "thời_tiết": "không có dữ liệu chi tiết"}
    return json.dumps({"city": city, **mock_data.get(city, default)}, ensure_ascii=False)


WMO_WEATHER_CODES = {
    0: "trời quang",
    1: "chủ yếu quang đãng",
    2: "mây rải rác",
    3: "nhiều mây",
    45: "sương mù",
    48: "sương mù đóng băng",
    51: "mưa phùn nhẹ",
    53: "mưa phùn vừa",
    55: "mưa phùn dày",
    61: "mưa nhẹ",
    63: "mưa vừa",
    65: "mưa lớn",
    71: "tuyết nhẹ",
    73: "tuyết vừa",
    75: "tuyết dày",
    80: "mưa rào nhẹ",
    81: "mưa rào vừa",
    82: "mưa rào mạnh",
    95: "dông",
    96: "dông kèm mưa đá nhẹ",
    99: "dông kèm mưa đá mạnh",
}


def _get_json_with_retry(url: str, params: dict, attempts: int = 3) -> dict:
    """Gọi GET và thử lại khi gặp lỗi mạng tạm thời hoặc lỗi server."""
    for attempt in range(1, attempts + 1):
        try:
            with httpx.Client(timeout=20.0) as http_client:
                response = http_client.get(url, params=params)

            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        except (httpx.TransportError, httpx.TimeoutException, httpx.HTTPStatusError):
            if attempt == attempts:
                raise
            time.sleep(0.5 * (2 ** (attempt - 1)))

    raise RuntimeError("Không thể gọi API sau nhiều lần thử")


def get_weather_forecast(city: str) -> str:
    """Lấy dự báo thật ngày mai và ngày kia từ Open-Meteo."""
    try:
        location_data = _get_json_with_retry(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": city, "count": 1, "language": "vi", "format": "json"},
        )
        locations = location_data.get("results", [])
        if not locations:
            return json.dumps(
                {"city": city, "error": "Không tìm thấy thành phố"},
                ensure_ascii=False,
            )

        location = locations[0]
        forecast_data = _get_json_with_retry(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "timezone": "auto",
                "forecast_days": 3,
            },
        )
        daily = forecast_data["daily"]

        forecasts = []
        for index, label in ((1, "ngày mai"), (2, "ngày kia")):
            weather_code = daily["weather_code"][index]
            forecasts.append(
                {
                    "ngày": label,
                    "date": daily["time"][index],
                    "thời_tiết": WMO_WEATHER_CODES.get(
                        weather_code, f"mã thời tiết {weather_code}"
                    ),
                    "nhiệt_độ_cao_nhất": daily["temperature_2m_max"][index],
                    "nhiệt_độ_thấp_nhất": daily["temperature_2m_min"][index],
                    "khả_năng_mưa": daily["precipitation_probability_max"][index],
                }
            )

        return json.dumps(
            {
                "city": location["name"],
                "country": location.get("country", ""),
                "timezone": location.get("timezone", ""),
                "source": "Open-Meteo",
                "forecast": forecasts,
            },
            ensure_ascii=False,
        )
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
        return json.dumps(
            {"city": city, "error": f"Không lấy được dữ liệu dự báo: {error}"},
            ensure_ascii=False,
        )


FUNCTIONS = {
    "get_weather": get_weather,
    "get_weather_forecast": get_weather_forecast,
}


def run(prompt: str) -> str:
    """Gửi *prompt* tới Gemini, tự động xử lý function calling và trả về câu trả lời cuối."""
    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    # 3. Gọi model — model quyết định có gọi tool hay không
    resp = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            tools=TOOLS,
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    # 4. Vòng lặp: nếu model yêu cầu tool, app TỰ THỰC THI rồi đưa kết quả trả lại
    while resp.function_calls:
        # Thêm phản hồi của model vào lịch sử hội thoại
        contents.append(resp.candidates[0].content)

        function_responses = []
        for fc in resp.function_calls:
            print(f"  [model yêu cầu] {fc.name}({fc.args})")
            function = FUNCTIONS.get(fc.name)
            if function is None:
                result = json.dumps(
                    {"error": f"Tool không được hỗ trợ: {fc.name}"},
                    ensure_ascii=False,
                )
            else:
                result = function(**fc.args)  # <-- app chạy, không phải model
            print(f"  [app thực thi]  -> {result}")
            function_responses.append(
                types.Part.from_function_response(
                    name=fc.name, response={"result": result}
                )
            )

        # Gửi kết quả tool trả về cho model
        contents.append(types.Content(role="user", parts=function_responses))
        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )

    # 5. Model tổng hợp câu trả lời cuối
    return resp.text


if __name__ == "__main__":
    question = "Thời tiết Hà Nội hôm nay, ngày mai và ngày kia thế nào?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))

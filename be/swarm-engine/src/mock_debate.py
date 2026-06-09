import json
import time
import sys
from src.personas import AGENT_PERSONAS
from src.agents import should_awake_agent


def run_mock_debate(ticker: str, category: str, current_price: float, similar_events: list):
    """
    Simulates a high-fidelity live debate between the 10 specialist agents
    tailored to the specific asset ticker, category, current price, and context.
    Prints JSON messages to stdout to be parsed dynamically by the backend core.
    """
    messages = [
        {
            "code": "TECH_A",
            "msg": f"Tôi nhận thấy chỉ số RSI của {ticker} trên khung Daily đã chạm ngưỡng quá bán sâu. Mức giá {current_price} đang nhận được lực cầu bắt đáy rất mạnh từ các ngưỡng MA hỗ trợ."
        },
        {
            "code": "FUND_A",
            "msg": f"Mặc dù kỹ thuật có tín hiệu hồi phục, nhưng từ góc độ định giá, tỷ lệ P/E và giá trị dòng tiền nội tại của {ticker} vẫn đang chịu áp lực điều chỉnh. Chúng ta cần cẩn trọng tránh bẫy tăng giá giả."
        },
        {
            "code": "MACRO_A",
            "msg": f"Đúng vậy, chu kỳ siết chặt tiền tệ và lạm phát CPI toàn cầu vẫn chưa kết thúc hoàn toàn. DXY giữ vững mốc 104 điểm sẽ tiếp tục đè nặng lên tài sản rủi ro như {ticker}."
        },
        {
            "code": "GEOPOL_A",
            "msg": f"Đừng quên rủi ro địa chính trị đang gia tăng. Báo cáo OPEC gần đây cho thấy nguồn cung Dầu thô bị thắt chặt và các lệnh trừng phạt thương mại sẽ sớm lan sang chuỗi linh kiện công nghệ bán dẫn."
        },
        {
            "code": "SENT_A",
            "msg": f"Dữ liệu mạng xã hội (Twitter/Reddit) cho thấy tâm lý đám đông đối với {ticker} đang chuyển từ hoảng loạn cực độ (Extreme Fear) sang tích cực mua tích lũy. Retail FOMO bắt đầu xuất hiện nhen nhóm."
        },
        {
            "code": "CRYPTO_A",
            "msg": f"Nếu phân tích on-chain của {ticker}, lượng lớn coins đang được rút khỏi ví sàn chuyển về ví lạnh (cold storage). Điều này báo hiệu áp lực bán tháo đã cạn kiệt, chu kỳ tăng tích lũy mới đang hình thành."
        },
        {
            "code": "FOREX_A",
            "msg": f"Tôi đồng ý. Chênh lệch lãi suất và luồng dịch chuyển dòng tiền tệ quốc tế đang có lợi cho sự ổn định ngắn hạn của {ticker}."
        },
        {
            "code": "COMM_A",
            "msg": f"Về mặt cung cầu vật lý, thời tiết cực đoan và việc gián đoạn tàu dầu qua Biển Đỏ có thể đẩy chi phí vận hành logistics của nhóm {ticker} tăng thêm 15%."
        },
        {
            "code": "RISK_M",
            "msg": f"Dựa trên các rủi ro đã nêu, tôi đề xuất điểm Entry an toàn ở mức {current_price * 0.98:.2f}, đặt điểm cắt lỗ (Stop Loss) nghiêm ngặt tại {current_price * 0.92:.2f} và mục tiêu chốt lời (Take Profit) tại {current_price * 1.15:.2f}."
        },
        {
            "code": "MOD_O",
            "msg": f"Tổng kết cuộc tranh luận từ các chuyên gia: Tín hiệu kỹ thuật ủng hộ đà hồi phục ngắn hạn tại {current_price}, mặc dù rủi ro vĩ mô và vận hành vẫn tồn tại. Tỷ lệ đồng thuận đạt 82.5%. Verdict cuối cùng: BUY."
        }
    ]
    
    # Filter specialists depending on category
    cat_upper = category.upper()
    if cat_upper != "CRYPTO":
        messages = [m for m in messages if m["code"] != "CRYPTO_A"]
    if cat_upper != "FOREX":
        messages = [m for m in messages if m["code"] != "FOREX_A"]
    if cat_upper != "STOCKS" and cat_upper != "INDEX":
        messages = [m for m in messages if m["code"] != "FUND_A"]
        
    for item in messages:
        code = item["code"]
        persona = AGENT_PERSONAS[code]
        agent_name = persona["name"]
        avatar = persona["avatar_code"]
        full_msg = item["msg"]
        
        should_awake, skip_reason = should_awake_agent(code, category, similar_events)
        if not should_awake:
            print(json.dumps({
                "agent_name": agent_name,
                "avatar_code": avatar,
                "message": f"[{agent_name} did not join the debate: {skip_reason}]",
                "status": "COMPLETED"
            }))
            sys.stdout.flush()
            time.sleep(0.5)
            continue

        
        # 1. Send TYPING
        print(json.dumps({
            "agent_name": agent_name,
            "avatar_code": avatar,
            "message": "",
            "status": "TYPING"
        }))
        sys.stdout.flush()
        time.sleep(0.3)
        
        # 2. Send SPEAKING chunks
        chunk_size = 5
        for i in range(0, len(full_msg), chunk_size):
            chunk = full_msg[i:i+chunk_size]
            print(json.dumps({
                "agent_name": agent_name,
                "avatar_code": avatar,
                "message_chunk": chunk,
                "status": "SPEAKING"
            }))
            sys.stdout.flush()
            time.sleep(0.04) # fast typing simulation
            
        # 3. Send COMPLETED
        print(json.dumps({
            "agent_name": agent_name,
            "avatar_code": avatar,
            "message": full_msg,
            "status": "COMPLETED"
        }))
        sys.stdout.flush()

        # 4. Send METRICS for tracking
        prompt_tokens = 250
        completion_tokens = max(1, len(full_msg) // 4)
        total_tokens = prompt_tokens + completion_tokens
        model_name = "gemini-2.5-flash" if item["code"] == "MOD_O" else "gemini-2.5-flash-lite"
        print(json.dumps({
            "type": "metrics",
            "agent_name": agent_name,
            "event": "awake",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "model": model_name
        }))
        sys.stdout.flush()

        if code == "MOD_O":
            drift = 0.015 # +1.5% drift over 5 days
            p5s = [current_price * (1 + drift * 0.0001 * (i + 1)) for i in range(5)]
            p5m = [current_price * (1 + drift * 0.001 * (i + 1)) for i in range(5)]
            p5h = [current_price * (1 + drift * 0.02 * (i + 1)) for i in range(5)]
            p5d = [current_price * (1 + drift * 0.2 * (i + 1)) for i in range(5)]
            print(json.dumps({
                "type": "consensus_forecast",
                "ticker": ticker,
                "verdict": "BUY",
                "confidence": 82.5,
                "predict_price_5s": p5s,
                "predict_price_5m": p5m,
                "predict_price_5h": p5h,
                "predict_price_5d": p5d,
                "baseline_trajectory": p5d,
                "advanced_trajectory": p5d
            }))
            sys.stdout.flush()

        time.sleep(1.0) # pause between agents


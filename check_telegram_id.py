import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')

def get_bot_updates():
    if not token:
        print("❌ .env 파일에서 TELEGRAM_TOKEN을 찾을 수 없습니다.")
        return

    print(f"🔍 봇 토큰 확인됨: {token[:10]}...{token[-5:]}")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get("ok"):
            print(f"❌ API 호출 실패: {data.get('description')}")
            return
            
        results = data.get("result", [])
        if not results:
            print("\nℹ️ 최근 활동 내역이 없습니다.")
            print("💡 해결 방법:")
            print("1. 텔레그램에서 봇에게 아무 메시지나 보내보세요.")
            print("2. 봇을 채널/그룹에 다시 초대하거나 관리자 권한을 부여한 후 다시 실행해 보세요.")
            return

        print("\n✅ 최근 발견된 채팅 정보:")
        seen_ids = set()
        for update in results:
            chat = None
            if "message" in update:
                chat = update["message"]["chat"]
            elif "my_chat_member" in update:
                chat = update["my_chat_member"]["chat"]
            elif "channel_post" in update:
                chat = update["channel_post"]["chat"]
                
            if chat and chat['id'] not in seen_ids:
                chat_type = chat.get('type')
                title = chat.get('title', chat.get('first_name', 'N/A'))
                print(f"--------------------------------")
                print(f"📌 이름/제목: {title}")
                print(f"🆔 채팅 ID: {chat['id']}")
                print(f"👤 타입: {chat_type}")
                seen_ids.add(chat['id'])
        
        print("\n위 목록에서 올바른 ID를 찾아 .env 파일의 TELEGRAM_CHAT_ID를 업데이트해 주세요.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    get_bot_updates()

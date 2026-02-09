from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# JSON Pretty Print automatically enable
app.json.compact = False 

# Aapka Credit Text
MY_CREDIT = "@BJ_Devs on Telegram"

def get_social_media_data(video_url, api_source):
    """
    Yeh function Instagram aur TikTok ki alag alag APIs ko handle karega
    """
    try:
        # URL determine karein based on source
        if api_source == "tiktok":
            # User ki nayi TikTok API
            api_endpoint = f"https://bj-tiktok-dl.manzoor-coder.workers.dev/?url={video_url}"
        elif api_source == "instagram":
            # User ki purani Instagram API
            api_endpoint = f"https://bj-test-kin-pbrz.vercel.app/download?url={video_url}"
        else:
            return {"status": False, "message": "Unknown Source"}
        
        # API Call
        response = requests.get(api_endpoint)
        response.raise_for_status()
        data = response.json()
        
        # --- Response Cleaning & Reformatting ---
        
        # Final response dict banayenge jisme sabse pehle Credit ho
        final_response = {
            "creator": MY_CREDIT
        }
        
        # Original data ko copy karein lekin purane credits hata dein
        # Yeh keys hatani hain taake aapka credit hi show ho
        keys_to_remove = ['creator', 'join', 'author', 'status', 'message', 'ok']
        
        # Agar API ka response seedha list hai ya dict hai, us hisaab se merge karein
        if isinstance(data, dict):
            # 'status' ya 'ok' hum khud set kar denge
            final_response['ok'] = True
            
            for key, value in data.items():
                if key not in keys_to_remove:
                    final_response[key] = value
        else:
            # Agar direct data list hai
            final_response['ok'] = True
            final_response['data'] = data

        return final_response

    except Exception as e:
        return {
            "creator": MY_CREDIT,
            "ok": False,
            "message": "API Error",
            "error": str(e)
        }

def get_aio_data(video_url):
    """
    Baaki websites ke liye scraping logic
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 15; SM-F958 Build/AP3A.240905.015) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.86 Mobile Safari/537.36',
            'Referer': 'https://allinonedownloader.pro/',
            'Origin': 'https://allinonedownloader.pro'
        }

        session = requests.Session()

        try:
            resp = session.get('https://allinonedownloader.pro/', headers=headers)
            resp.raise_for_status()
        except:
            return {"ok": False, "message": "Failed to connect to AIO"}

        soup = BeautifulSoup(resp.text, 'html.parser')
        token_input = soup.find('input', {'name': 'token'})
        if not token_input:
            return {"ok": False, "message": "Token not found"}
        token = token_input.get('value')

        post_url = 'https://allinonedownloader.pro/wp-json/aio-dl/video-data/'
        payload = {'url': video_url, 'token': token}
        
        post_resp = session.post(post_url, data=payload, headers=headers)
        post_resp.raise_for_status()
        raw_data = post_resp.json()

        # Cleaning Logic
        duration = raw_data.get('duration', '00:00')
        cleaned_medias = []
        
        if 'medias' in raw_data and isinstance(raw_data['medias'], list):
            for media in raw_data['medias']:
                # Thumbnails remove
                media.pop('thumbnail', None)
                media.pop('image', None)
                media.pop('cover', None)
                cleaned_medias.append(media)
        else:
            raw_data.pop('thumbnail', None)
            raw_data.pop('image', None)
            cleaned_medias.append(raw_data)

        return {
            "creator": MY_CREDIT,
            "ok": True,
            "title": raw_data.get('title', 'Video'),
            "source": raw_data.get('source', 'Unknown'),
            "duration": duration,
            "medias": cleaned_medias
        }

    except Exception as e:
        return {"creator": MY_CREDIT, "ok": False, "message": str(e)}

@app.route('/', methods=['GET'])
def home():
    video_url = request.args.get('url')

    if not video_url:
        return jsonify({
            "creator": MY_CREDIT,
            "ok": False,
            "message": "Please provide a URL parameter."
        }), 400

    # Domain Detection
    domain_check = video_url.lower()

    if "tiktok.com" in domain_check:
        # Nayi TikTok Logic
        result = get_social_media_data(video_url, "tiktok")
        
    elif "instagram.com" in domain_check:
        # Purani Instagram Logic
        result = get_social_media_data(video_url, "instagram")
        
    else:
        # Fallback Scraper
        result = get_aio_data(video_url)

    return jsonify(result)

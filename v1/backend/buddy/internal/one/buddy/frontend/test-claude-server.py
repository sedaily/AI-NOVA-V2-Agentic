from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/claude/chat', methods=['POST', 'OPTIONS'])
def claude_chat():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        message = data.get('message')
        model = data.get('model', 'claude-opus-4-20250514')
        api_key = data.get('apiKey') or os.environ.get('CLAUDE_API_KEY')
        
        if not message:
            return jsonify({'error': '메시지가 필요합니다.'}), 400
        
        print(f'📨 Claude API 요청: model={model}, message_length={len(message)}')
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': model,
                'max_tokens': 4096,
                'messages': [{'role': 'user', 'content': message}]
            }
        )
        
        if response.status_code != 200:
            print(f'❌ Claude API 오류: {response.status_code}')
            return jsonify({
                'error': f'Claude API 오류: {response.status_code}',
                'details': response.text
            }), response.status_code
        
        print('✅ Claude API 응답 성공')
        return jsonify(response.json())
        
    except Exception as e:
        print(f'❌ 서버 오류: {str(e)}')
        return jsonify({
            'error': '서버 오류가 발생했습니다.',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    print('🚀 Claude 프록시 서버 시작: http://127.0.0.1:5000')
    print('📍 엔드포인트: POST /api/claude/chat')
    app.run(host='127.0.0.1', port=5000, debug=True)

"""
Gemini TTS Tool
Google Gemini 기반 TTS 음성 생성
"""

import os
import httpx
import logging
import base64
from typing import Optional
from datetime import datetime
import boto3

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
S3_BUCKET = os.getenv("S3_TTS_BUCKET", "sedaily-tts-audio")
S3_REGION = os.getenv("AWS_REGION", "ap-northeast-2")


async def generate_tts(
    text: str,
    voice: str = "ko-KR-Wavenet-A",
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
) -> Optional[str]:
    """
    Gemini TTS로 음성 생성

    Args:
        text: 음성으로 변환할 텍스트
        voice: 음성 종류
        speaking_rate: 말하기 속도 (0.25 ~ 4.0)
        pitch: 음높이 (-20.0 ~ 20.0)

    Returns:
        S3 URL 또는 None
    """
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set")
        return None

    if not text or len(text.strip()) == 0:
        return None

    # 텍스트 길이 제한 (5000자)
    if len(text) > 5000:
        text = text[:5000]

    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": "ko-KR",
            "name": voice,
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": speaking_rate,
            "pitch": pitch,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            # Base64 디코딩
            audio_content = base64.b64decode(data.get("audioContent", ""))

            if not audio_content:
                logger.error("No audio content in response")
                return None

            # S3 업로드
            s3_url = await _upload_to_s3(audio_content)
            return s3_url

    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini TTS HTTP error: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini TTS error: {e}")
        return None


async def _upload_to_s3(audio_content: bytes) -> Optional[str]:
    """
    S3에 오디오 파일 업로드

    Args:
        audio_content: MP3 바이너리 데이터

    Returns:
        S3 URL
    """
    try:
        s3_client = boto3.client("s3", region_name=S3_REGION)

        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts/{timestamp}_{hash(audio_content) % 10000:04d}.mp3"

        # 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=filename,
            Body=audio_content,
            ContentType="audio/mpeg",
        )

        # URL 생성
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"

        logger.info(f"TTS uploaded to S3: {url}")
        return url

    except Exception as e:
        logger.error(f"S3 upload error: {e}")
        return None


async def generate_tts_polly(
    text: str,
    voice_id: str = "Seoyeon",
    engine: str = "neural",
) -> Optional[str]:
    """
    AWS Polly로 TTS 생성 (대안)

    Args:
        text: 음성으로 변환할 텍스트
        voice_id: Polly 음성 ID (Seoyeon = 한국어 여성)
        engine: neural 또는 standard

    Returns:
        S3 URL 또는 None
    """
    if len(text) > 3000:
        text = text[:3000]

    try:
        polly_client = boto3.client("polly", region_name=S3_REGION)

        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            Engine=engine,
            LanguageCode="ko-KR",
        )

        audio_stream = response.get("AudioStream")
        if audio_stream:
            audio_content = audio_stream.read()
            return await _upload_to_s3(audio_content)

        return None

    except Exception as e:
        logger.error(f"Polly TTS error: {e}")
        return None

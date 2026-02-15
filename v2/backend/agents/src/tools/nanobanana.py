"""
NanoBanana API Tool
AI 이미지 생성 (뉴스 대표 이미지)
"""

import os
import httpx
import logging
from typing import Optional
from datetime import datetime
import boto3

logger = logging.getLogger(__name__)

NANOBANANA_API_URL = os.getenv("NANOBANANA_API_URL", "https://api.nanobanana.ai")
NANOBANANA_API_KEY = os.getenv("NANOBANANA_API_KEY", "")
S3_BUCKET = os.getenv("S3_IMAGE_BUCKET", "sedaily-news-images")
S3_REGION = os.getenv("AWS_REGION", "ap-northeast-2")


async def generate_image(
    prompt: str,
    style: str = "news_thumbnail",
    width: int = 1200,
    height: int = 630,
    negative_prompt: Optional[str] = None,
) -> Optional[str]:
    """
    뉴스 대표 이미지 생성

    Args:
        prompt: 이미지 생성 프롬프트 (영문 권장)
        style: 스타일 프리셋
        width: 이미지 너비
        height: 이미지 높이
        negative_prompt: 제외할 요소

    Returns:
        S3 URL 또는 None
    """
    if not NANOBANANA_API_KEY:
        logger.warning("NANOBANANA_API_KEY not set")
        return None

    # 기본 네거티브 프롬프트 (뉴스 이미지용)
    if not negative_prompt:
        negative_prompt = "text, watermark, logo, signature, blurry, low quality, nsfw, violence, gore, offensive"

    # 뉴스 이미지 스타일 강화
    enhanced_prompt = f"{prompt}, professional news media style, high quality, editorial photography"

    payload = {
        "prompt": enhanced_prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "style": style,
        "num_inference_steps": 30,
        "guidance_scale": 7.5,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # 이미지 생성 요청
            response = await client.post(
                f"{NANOBANANA_API_URL}/v1/generate",
                json=payload,
                headers={
                    "Authorization": f"Bearer {NANOBANANA_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            # 이미지 URL 또는 base64 가져오기
            image_url = data.get("image_url")
            image_base64 = data.get("image_base64")

            if image_url:
                # URL에서 이미지 다운로드 후 S3 업로드
                img_response = await client.get(image_url)
                img_response.raise_for_status()
                image_content = img_response.content
            elif image_base64:
                import base64
                image_content = base64.b64decode(image_base64)
            else:
                logger.error("No image in response")
                return None

            # S3 업로드
            s3_url = await _upload_to_s3(image_content)
            return s3_url

    except httpx.HTTPStatusError as e:
        logger.error(f"NanoBanana API HTTP error: {e}")
        return None
    except Exception as e:
        logger.error(f"NanoBanana API error: {e}")
        return None


async def _upload_to_s3(image_content: bytes) -> Optional[str]:
    """
    S3에 이미지 업로드

    Args:
        image_content: 이미지 바이너리 데이터

    Returns:
        S3 URL
    """
    try:
        s3_client = boto3.client("s3", region_name=S3_REGION)

        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated/{timestamp}_{hash(image_content) % 10000:04d}.png"

        # 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=filename,
            Body=image_content,
            ContentType="image/png",
        )

        # URL 생성
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"

        logger.info(f"Image uploaded to S3: {url}")
        return url

    except Exception as e:
        logger.error(f"S3 upload error: {e}")
        return None


async def generate_infographic(
    data: dict,
    chart_type: str = "bar",
    title: str = "",
) -> Optional[str]:
    """
    인포그래픽 이미지 생성

    Args:
        data: 차트 데이터
        chart_type: 차트 종류 (bar, line, pie, comparison)
        title: 인포그래픽 제목

    Returns:
        S3 URL 또는 None
    """
    if not NANOBANANA_API_KEY:
        return None

    # 데이터를 프롬프트로 변환
    data_str = ", ".join([
        f"{item.get('label', '')}: {item.get('value', '')}{item.get('unit', '')}"
        for item in data.get("data_points", [])
    ])

    prompt = f"""Infographic, {chart_type} chart visualization,
    Title: {title}
    Data: {data_str}
    Professional business style, clean design, blue and white color scheme,
    Korean business infographic, no text, data visualization"""

    return await generate_image(
        prompt=prompt,
        style="infographic",
        width=1200,
        height=800,
    )

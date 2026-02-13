"""
AWS Transcribe API 핸들러
음성 파일을 텍스트로 변환
"""
import json
import os
import uuid
import boto3
from datetime import datetime
import base64
import time

from utils.response import create_response

def create_cors_response(status_code, body):
    """CORS 헤더를 포함한 응답 생성"""
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
from utils.logger import setup_logger
from src.config.aws import AWS_REGION, S3_CONFIG

logger = setup_logger(__name__)

# AWS 클라이언트 초기화
s3_client = boto3.client('s3', region_name=AWS_REGION)
transcribe_client = boto3.client('transcribe', region_name=AWS_REGION)

def lambda_handler(event, context):
    """
    음성 파일을 텍스트로 변환하는 Lambda 핸들러
    """
    # OPTIONS 요청 처리 (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return create_cors_response(200, {})

    try:
        # 요청 파싱
        headers = event.get('headers', {})

        # 인증 확인 (임시로 비활성화 또는 간단하게 처리)
        auth_token = headers.get('authorization', '') or headers.get('Authorization', '')
        # 임시로 인증 체크를 느슨하게 처리
        logger.info(f"Auth token received: {bool(auth_token)}")

        # multipart/form-data 파싱
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)

        if is_base64:
            body = base64.b64decode(body)

        # 파일 처리 (간단한 구현 - 실제로는 multipart parser 필요)
        # AWS API Gateway는 multipart 처리가 복잡하므로,
        # Base64 인코딩된 오디오 데이터를 JSON으로 받는 방식으로 변경

        if isinstance(body, bytes):
            body = body.decode('utf-8')

        try:
            request_data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return create_cors_response(400, {'error': 'Invalid JSON format'})

        audio_data = request_data.get('audio')  # Base64 encoded audio
        audio_format = request_data.get('format', 'webm')

        if not audio_data:
            logger.error("No audio data provided")
            return create_cors_response(400, {'error': 'No audio data provided'})

        # Base64 디코딩
        audio_bytes = base64.b64decode(audio_data)

        # S3에 임시 파일 업로드
        job_name = f"transcribe-{uuid.uuid4()}"
        s3_key = f"transcribe-temp/{job_name}.{audio_format}"

        # S3 버킷 이름 설정
        bucket_name = S3_CONFIG.get('bucket')
        if not bucket_name:
            bucket_name = f"sedaily-column-transcribe-{AWS_REGION}"

        # S3에 업로드
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=audio_bytes,
            ContentType=f"audio/{audio_format}"
        )

        # S3 파일 URL
        s3_uri = f"s3://{bucket_name}/{s3_key}"

        # 오디오 형식 매핑 (AWS Transcribe 지원 형식)
        format_mapping = {
            'wav': 'wav',
            'mp3': 'mp3',
            'mp4': 'mp4',
            'flac': 'flac',
            'm4a': 'mp4',
            'ogg': 'ogg',
            'webm': 'webm',
            'amr': 'amr',
            'mpeg': 'mp3'
        }

        media_format = format_mapping.get(audio_format.lower(), 'mp3')
        logger.info(f"Audio format: {audio_format} -> MediaFormat: {media_format}")

        # Transcribe 작업 시작
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': s3_uri},
            MediaFormat=media_format,
            LanguageCode='ko-KR',  # 한국어
            OutputBucketName=bucket_name,
            OutputKey=f"transcribe-output/{job_name}.json"
        )

        logger.info(f"Transcription job started: {job_name}")

        # 작업 완료 대기 (최대 60초)
        max_wait_time = 60
        wait_interval = 2
        total_wait = 0

        while total_wait < max_wait_time:
            job_status = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )

            status = job_status['TranscriptionJob']['TranscriptionJobStatus']

            if status == 'COMPLETED':
                # 결과 가져오기
                output_key = f"transcribe-output/{job_name}.json"

                result_obj = s3_client.get_object(
                    Bucket=bucket_name,
                    Key=output_key
                )

                result_data = json.loads(result_obj['Body'].read())
                transcript_text = result_data['results']['transcripts'][0]['transcript']

                # 임시 파일 삭제
                s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
                s3_client.delete_object(Bucket=bucket_name, Key=output_key)

                logger.info(f"Transcription completed: {job_name}")

                return create_cors_response(200, {
                    'transcript': transcript_text,
                    'jobName': job_name,
                    'language': 'ko-KR'
                })

            elif status == 'FAILED':
                # 실패 시 정리
                s3_client.delete_object(Bucket=bucket_name, Key=s3_key)

                error_reason = job_status['TranscriptionJob'].get('FailureReason', 'Unknown error')
                logger.error(f"Transcription failed: {error_reason}")

                return create_cors_response(500, {
                    'error': 'Transcription failed',
                    'reason': error_reason
                })

            # 대기
            time.sleep(wait_interval)
            total_wait += wait_interval

        # 타임아웃
        logger.error(f"Transcription timeout: {job_name}")

        # 정리
        try:
            transcribe_client.delete_transcription_job(
                TranscriptionJobName=job_name
            )
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        except:
            pass

        return create_response(408, {
            'error': 'Transcription timeout',
            'message': 'The transcription process took too long. Please try again with a shorter audio file.'
        })

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })
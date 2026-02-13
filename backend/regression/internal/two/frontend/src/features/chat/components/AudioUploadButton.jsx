import React, { useRef, useState } from 'react';
import { Mic, Upload, Square, Pause } from 'lucide-react';
import toast from 'react-hot-toast';

const AudioUploadButton = ({ onFileUploaded, disabled }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // 파일 선택 처리
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // 오디오 파일 검증
    if (!file.type.startsWith('audio/')) {
      toast.error('오디오 파일만 업로드 가능합니다');
      return;
    }

    // 파일 크기 제한 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('파일 크기는 10MB 이하여야 합니다');
      return;
    }

    await transcribeAudio(file);
  };

  // 녹음 시작
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // MediaRecorder 설정
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        // 파일 정보 생성
        const file = new File([audioBlob], `녹음_${new Date().toISOString().slice(0, 19).replace(/:/g, '')}.webm`, {
          type: 'audio/webm'
        });

        // 자동으로 transcribe 시작
        await transcribeAudio(file);

        // 스트림 정리
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start(1000); // 1초마다 데이터 수집
      setIsRecording(true);

      toast.success('녹음이 시작되었습니다', {
        duration: 2000,
        position: 'top-center',
        style: {
          background: 'hsl(var(--bg-100))',
          color: 'hsl(var(--text-100))',
          border: '1px solid hsl(var(--accent-main-100))',
        },
      });
    } catch (error) {
      console.error('녹음 시작 실패:', error);
      toast.error('마이크 접근 권한이 필요합니다');
    }
  };

  // 녹음 일시정지/재개
  const togglePause = () => {
    if (!mediaRecorderRef.current) return;

    if (isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      toast.success('녹음이 재개되었습니다', { duration: 1500 });
    } else {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      toast.success('녹음이 일시정지되었습니다', { duration: 1500 });
    }
  };

  // 녹음 중지
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
    }
  };

  // AWS Transcribe를 통한 음성 변환
  const transcribeAudio = async (audioFile) => {
    setIsTranscribing(true);

    try {
      // 파일을 Base64로 변환
      const reader = new FileReader();
      const base64Audio = await new Promise((resolve, reject) => {
        reader.onload = () => {
          const base64 = reader.result.split(',')[1]; // data:audio/webm;base64,xxx 에서 xxx 부분만
          resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(audioFile);
      });

      // 파일 형식 감지
      let format = 'webm';
      if (audioFile.type) {
        // audio/wav -> wav, audio/mpeg -> mpeg 등
        format = audioFile.type.split('/')[1] || 'webm';
        // x-wav, x-m4a 등의 형식 처리
        if (format.startsWith('x-')) {
          format = format.substring(2);
        }
      }
      console.log('Audio file type:', audioFile.type, '-> format:', format);

      // Backend API 호출 (JSON 형식)
      const apiUrl = import.meta.env.VITE_API_URL || 'https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod';
      console.log('Calling Transcribe API:', `${apiUrl}/transcribe`);
      const response = await fetch(`${apiUrl}/transcribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          audio: base64Audio,
          format: format
        })
      });

      if (!response.ok) {
        throw new Error('Transcription failed');
      }

      const data = await response.json();

      if (data.transcript) {
        console.log('Transcription result:', data.transcript);

        // 파일 정보에 변환된 텍스트 추가
        const fileInfo = {
          id: Date.now() + Math.random(),
          name: audioFile.name || '오디오 파일',
          size: audioFile.size,
          type: audioFile.type,
          format: format.toUpperCase(),
          transcript: data.transcript,
          uploadedAt: new Date().toISOString()
        };

        // 파일 업로드 알림 (전송 버튼 활성화 및 카드 표시용)
        if (onFileUploaded) {
          onFileUploaded(fileInfo);
        }

        // 사용자에게 알림 표시
        toast.success(
          autoSend ? '음성을 텍스트로 변환하여 전송합니다' : '음성이 텍스트로 변환되었습니다',
          {
            duration: 3000,
            position: 'top-center',
            style: {
              background: 'hsl(var(--bg-100))',
              color: 'hsl(var(--text-100))',
              border: '1px solid hsl(var(--accent-main-100))',
            },
          }
        );
      }
    } catch (error) {
      console.error('Transcription error:', error);
      toast.error('음성 변환에 실패했습니다. 다시 시도해주세요.', {
        duration: 4000,
        position: 'top-center',
      });
    } finally {
      setIsTranscribing(false);
      // 입력 초기화
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };



  return (
    <div className="flex items-center gap-2">
      {/* 파일 업로드 버튼 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="audio/*"
        onChange={handleFileSelect}
        className="hidden"
        disabled={disabled || isTranscribing}
      />

      {!isRecording ? (
        <>
          {/* 오디오 파일 업로드 */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isTranscribing}
            className="inline-flex items-center justify-center relative shrink-0 select-none transition-all h-8 px-2 rounded-md hover:bg-bg-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            title="오디오 파일 업로드"
          >
            {isTranscribing ? (
              <div className="animate-spin h-4 w-4 border-2 border-accent-main-100 border-t-transparent rounded-full" />
            ) : (
              <Upload size={18} className="text-text-400" />
            )}
          </button>

          {/* 녹음 시작 버튼 */}
          <button
            onClick={startRecording}
            disabled={disabled || isTranscribing}
            className="inline-flex items-center justify-center relative shrink-0 select-none transition-all h-8 px-2 rounded-md hover:bg-bg-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            title="음성 녹음 시작"
          >
            <Mic size={18} className="text-text-400" />
          </button>
        </>
      ) : (
        <>
          {/* 녹음 중지 버튼 */}
          <button
            onClick={stopRecording}
            className="inline-flex items-center justify-center relative shrink-0 select-none transition-all h-8 px-2 rounded-md bg-red-500 hover:bg-red-600 text-white active:scale-95"
            title="녹음 중지"
          >
            <Square size={16} />
          </button>

          {/* 일시정지/재개 버튼 */}
          <button
            onClick={togglePause}
            className="inline-flex items-center justify-center relative shrink-0 select-none transition-all h-8 px-2 rounded-md hover:bg-bg-200 active:scale-95"
            title={isPaused ? "녹음 재개" : "녹음 일시정지"}
          >
            {isPaused ? (
              <Mic size={18} className="text-green-500" />
            ) : (
              <Pause size={18} className="text-text-400" />
            )}
          </button>

          {/* 녹음 상태 표시 */}
          <div className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${isPaused ? 'bg-yellow-500' : 'bg-red-500 animate-pulse'}`} />
            <span className="text-xs text-text-500">
              {isPaused ? '일시정지' : '녹음 중'}
            </span>
          </div>
        </>
      )}
    </div>
  );
};

export default AudioUploadButton;
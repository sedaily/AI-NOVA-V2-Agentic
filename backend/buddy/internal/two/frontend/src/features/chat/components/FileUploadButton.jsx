import React, { useRef, useState, forwardRef, useImperativeHandle, useEffect } from 'react';
import { PaperClipIcon } from '@heroicons/react/24/outline';
import * as pdfjsLib from 'pdfjs-dist';

// PDF.js worker 설정 - 컴포넌트 마운트 시 설정
const initPdfWorker = () => {
  if (typeof window !== 'undefined' && pdfjsLib) {
    // CloudFront URL 또는 로컬 경로 사용
    const workerUrl = window.location.hostname === 'localhost'
      ? '/pdf.worker.min.js'
      : `${window.location.origin}/pdf.worker.min.js`;

    pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;
    console.log('PDF.js Worker initialized:', workerUrl);
  }
};

const FileUploadButton = forwardRef(({ onFileContent, disabled }, ref) => {
  const fileInputRef = useRef(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  // 컴포넌트 마운트 시 PDF worker 초기화
  useEffect(() => {
    initPdfWorker();
  }, []);

  // 파일 크기 포맷팅 함수
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + sizes[i];
  };

  // 파일 확장자 추출
  const getFileExtension = (fileName) => {
    const parts = fileName.split('.');
    return parts.length > 1 ? parts.pop().toUpperCase() : 'FILE';
  };

  // 파일 처리 공통 함수
  const processFile = async (file) => {
    if (!file) return;

    // 이미 업로드된 파일인지 체크
    if (uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
      alert('이미 업로드된 파일입니다.');
      return;
    }

    setIsProcessing(true);

    try {
      // 파일 크기 체크 (500MB 제한으로 증가)
      if (file.size > 500 * 1024 * 1024) {
        alert('파일 크기는 500MB를 초과할 수 없습니다.');
        return;
      }

      let fileContent = '';
      let fileType = '';
      let pageCount = null;

      // 파일 타입별 처리
      if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
        // 텍스트 파일 처리
        fileContent = await file.text();
        fileType = 'text';
      } else if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        // PDF 파일 처리
        const result = await handlePdfFile(file);
        if (!result) return;
        fileContent = result.text;
        fileType = 'pdf';
        pageCount = result.pageCount;
      } else {
        alert('지원하지 않는 파일 형식입니다. txt, pdf 파일만 업로드 가능합니다.');
        return;
      }

      // 파일 정보 저장
      const fileInfo = {
        id: Date.now() + Math.random(),
        name: file.name,
        size: file.size,
        sizeFormatted: formatFileSize(file.size),
        type: fileType,
        extension: getFileExtension(file.name),
        content: fileContent,
        pageCount,
        uploadedAt: new Date()
      };

      // 파일 목록에 추가
      setUploadedFiles(prev => [...prev, fileInfo]);

      // 콜백 호출
      onFileContent(fileContent, {
        fileName: file.name,
        fileType,
        fileSize: file.size,
        pageCount
      });
    } catch (error) {
      console.error('파일 처리 오류:', error);
      alert('파일을 처리하는 중 오류가 발생했습니다.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileSelect = async (event) => {
    const files = Array.from(event.target.files);
    
    // 여러 파일 순차 처리
    for (const file of files) {
      await processFile(file);
    }
    
    // 같은 파일 재선택 가능하도록 초기화
    event.target.value = '';
  };


  // 외부에서 파일 처리를 위한 메서드 노출
  useImperativeHandle(ref, () => ({
    handleFile: processFile
  }));

  const handlePdfFile = async (file) => {
    try {
      console.log('PDF 파일 처리 시작:', file.name, 'Size:', file.size);
      // 클라이언트 사이드에서 PDF.js를 사용한 텍스트 추출
      const arrayBuffer = await file.arrayBuffer();
      console.log('ArrayBuffer 생성 완료');
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      console.log('PDF 문서 로드 완료, 페이지 수:', pdf.numPages);
      
      let fullText = '';
      const numPages = pdf.numPages;
      
      // 각 페이지에서 텍스트 추출
      for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map(item => item.str).join(' ');
        fullText += pageText + '\n\n';
      }
      
      // 추출한 텍스트가 비어있는지 확인
      if (!fullText.trim()) {
        alert('PDF에서 텍스트를 추출할 수 없습니다. 스캔된 이미지 PDF일 수 있습니다.');
        return null;
      }
      
      return {
        text: fullText.trim(),
        pageCount: numPages
      };
    } catch (error) {
      console.error('PDF 처리 오류:', error);
      alert('PDF 파일 처리 중 오류가 발생했습니다. 텍스트를 직접 복사하여 붙여넣어 주세요.');
      return null;
    }
  };

  return (
    <div className="relative group">
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.pdf"
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled || isProcessing}
          multiple
        />
      
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled || isProcessing}
        className={`p-2 rounded-lg transition-all duration-200 flex items-center justify-center ${
          disabled || isProcessing
            ? 'bg-bg-200 text-text-400 cursor-not-allowed'
            : 'bg-bg-200 hover:bg-bg-300 text-text-300 hover:text-text-100 hover:shadow-sm'
        }`}
        title={isProcessing ? '파일 처리 중...' : '파일 업로드 (txt, pdf)'}
        style={{
          backgroundColor: disabled || isProcessing ? 'hsl(var(--bg-200))' : 'hsl(var(--bg-200))',
          color: disabled || isProcessing ? 'hsl(var(--text-400))' : 'hsl(var(--text-300))'
        }}
      >
        {isProcessing ? (
          <div className="animate-spin h-5 w-5 border-2 border-text-400 border-t-transparent rounded-full" />
        ) : (
          <PaperClipIcon className="h-5 w-5" />
        )}
      </button>


      {/* 처리 중 상태 표시 */}
      {isProcessing && (
        <div className="absolute bottom-full left-0 mb-2 px-2 py-1 text-white text-xs rounded whitespace-nowrap animate-pulse z-50"
             style={{ backgroundColor: 'hsl(var(--accent-main-100))' }}>
          파일 처리 중...
        </div>
      )}
    </div>
  );
});

FileUploadButton.displayName = 'FileUploadButton';

export default FileUploadButton;
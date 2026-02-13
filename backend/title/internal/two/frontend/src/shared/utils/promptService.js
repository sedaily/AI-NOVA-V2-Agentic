// API 엔드포인트는 환경변수로 관리
const API_ENDPOINT = import.meta.env.VITE_PROMPT_API_URL || '';

// 프롬프트 조회 (설명, 지침, 파일 목록)
export const getPrompt = async (engineType) => {
  try {
    const response = await fetch(`${API_ENDPOINT}/prompts/${engineType}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching prompt:', error);
    throw error;
  }
};

// 프롬프트 업데이트 (설명, 지침만)
export const updatePrompt = async (engineType, updates) => {
  try {
    const response = await fetch(`${API_ENDPOINT}/prompts/${engineType}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error updating prompt:', error);
    throw error;
  }
};

// 파일 목록 조회
export const getFiles = async (engineType) => {
  try {
    const response = await fetch(`${API_ENDPOINT}/prompts/${engineType}/files`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.files || [];
  } catch (error) {
    console.error('Error fetching files:', error);
    throw error;
  }
};

// 파일 추가
export const addFile = async (engineType, file) => {
  const url = `${API_ENDPOINT}/prompts/${engineType}/files`;
  console.log('Adding file to:', url);
  console.log('Request body:', { fileName: file.fileName, fileContent: file.fileContent });
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        fileName: file.fileName,
        fileContent: file.fileContent,
      }),
    });

    console.log('Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Response error:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }

    const data = await response.json();
    console.log('Response data:', data);
    return data.file;
  } catch (error) {
    console.error('Error adding file:', error);
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      url: url
    });
    throw error;
  }
};

// 파일 수정
export const updateFile = async (engineType, fileId, updates) => {
  try {
    const response = await fetch(`${API_ENDPOINT}/prompts/${engineType}/files/${fileId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error updating file:', error);
    throw error;
  }
};

// 파일 삭제
export const deleteFile = async (engineType, fileId) => {
  try {
    const response = await fetch(`${API_ENDPOINT}/prompts/${engineType}/files/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error deleting file:', error);
    throw error;
  }
};
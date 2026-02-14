import React, { useState } from 'react';
import { getBuddyConfig } from '../../../config/buddyServiceConfig';
import { reconnectForBuddy } from '../services/websocketService';

const BuddyButtons = ({ currentBuddyService, setCurrentBuddyService }) => {
  const [showAllTools, setShowAllTools] = useState(false);

  return (
    <div className="flex justify-center px-16 py-3">
      <div className="flex flex-wrap gap-2 justify-center">
        {['일보버디', '제목생성_5종', '교열_경제분야', '보도자료_기업', '외신_영어', '퇴고_단문'].map((label) => {
          const buddyConfig = getBuddyConfig(label);
          const isSelected = currentBuddyService?.promptType === buddyConfig?.promptType;
          
          return (
            <button
              key={label}
              onClick={async () => {
                if (buddyConfig) {
                  setCurrentBuddyService(buddyConfig);
                  localStorage.setItem('currentBuddyType', label);
                  console.log('🎯 버디 선택:', label, buddyConfig);
                  try {
                    await reconnectForBuddy(label);
                  } catch (error) {
                    console.error('WebSocket 재연결 실패:', error);
                  }
                }
              }}
              className="px-2.5 py-1 text-sm font-medium transition-all duration-200 whitespace-nowrap"
              style={{
                fontFamily: '"Tiempos Text", "Source Serif 4", "Noto Serif KR", serif',
                color: 'var(--text-color)',
                backgroundColor: isSelected ? 'hsl(var(--bg-200))' : 'transparent',
                border: '1px solid hsl(var(--border-300)/25%)',
                borderRadius: '24px',
                boxShadow: isSelected ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)',
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = 'hsl(var(--bg-200))';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              {label}
            </button>
          );
        })}
        
        <button
          onClick={() => setShowAllTools(!showAllTools)}
          className="w-8 h-8 text-base font-medium transition-all duration-200 flex items-center justify-center"
          style={{
            color: 'var(--text-color)',
            backgroundColor: showAllTools ? 'hsl(var(--bg-200))' : 'transparent',
            border: '1px solid hsl(var(--border-300)/25%)',
            borderRadius: '50%',
            boxShadow: showAllTools ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)',
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              transform: showAllTools ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s'
            }}
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        
        {showAllTools && ['기사버디', '퇴고_장문', '제목창의_7종', '교열_사회분야', '보도자료_공공', '외신_일어'].map((label) => {
          const buddyConfig = getBuddyConfig(label);
          const isSelected = currentBuddyService?.promptType === buddyConfig?.promptType;
          
          return (
            <button
              key={label}
              onClick={async () => {
                if (buddyConfig) {
                  setCurrentBuddyService(buddyConfig);
                  localStorage.setItem('currentBuddyType', label);
                  console.log('🎯 버디 선택:', label, buddyConfig);
                  try {
                    await reconnectForBuddy(label);
                  } catch (error) {
                    console.error('WebSocket 재연결 실패:', error);
                  }
                }
              }}
              className="px-2.5 py-1 text-sm font-medium transition-all duration-200 whitespace-nowrap"
              style={{
                fontFamily: '"Tiempos Text", "Source Serif 4", "Noto Serif KR", serif',
                color: 'var(--text-color)',
                backgroundColor: isSelected ? 'hsl(var(--bg-200))' : 'transparent',
                border: '1px solid hsl(var(--border-300)/25%)',
                borderRadius: '24px',
                boxShadow: isSelected ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)',
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = 'hsl(var(--bg-200))';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default BuddyButtons;

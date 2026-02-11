/**
 * 버디 서비스 설정
 */

export const BUDDY_CONFIG = {
  '일보버디': {
    serviceCode: 'b1',
    promptTable: 'p2-two-prompts-two',
    promptType: 'ilbo'
  },
  '기사버디': {
    serviceCode: 'b1',
    promptTable: 'p2-two-prompts-two',
    promptType: 'article'
  },
  '보도자료_기업': {
    serviceCode: 'w1',
    promptTable: 'w1-prompts',
    promptType: 'corporate'
  },
  '보도자료_공공': {
    serviceCode: 'w1',
    promptTable: 'w1-prompts',
    promptType: 'public'
  },
  '외신_영어': {
    serviceCode: 'f1',
    promptTable: 'f1-prompts-two',
    promptType: 'english'
  },
  '외신_일어': {
    serviceCode: 'f1',
    promptTable: 'f1-prompts-two',
    promptType: 'japanese'
  },
  '퇴고_단문': {
    serviceCode: 'r1',
    promptTable: 'sedaily-column-prompts',
    promptType: 'short'
  },
  '퇴고_장문': {
    serviceCode: 'r1',
    promptTable: 'sedaily-column-prompts',
    promptType: 'long'
  },
  '제목생성_5종': {
    serviceCode: 't1',
    promptTable: 'nx-tt-dev-ver3-prompts',
    promptType: 'five_types'
  },
  '제목창의_7종': {
    serviceCode: 't1',
    promptTable: 'nx-tt-dev-ver3-prompts',
    promptType: 'seven_types'
  },
  '교열_경제분야': {
    serviceCode: 'p1',
    promptTable: 'nx-wt-prf-prompts',
    promptType: 'economy'
  },
  '교열_사회분야': {
    serviceCode: 'p1',
    promptTable: 'nx-wt-prf-prompts',
    promptType: 'society'
  }
};

// 통합 테이블 (일보버디 것 사용)
export const UNIFIED_TABLES = {
  conversations: 'p2-two-conversations-two',
  files: 'p2-two-files-two',
  usage: 'p2-two-usage-two',
  connections: 'p2-two-websocket-connections-two'
};

export const getBuddyConfig = (buddyType) => {
  return BUDDY_CONFIG[buddyType] || null;
};

/**
 * 버디 서비스 설정
 */

// 서비스별 API 엔드포인트
export const SERVICE_ENDPOINTS = {
  b1: {  // buddy - 일보버디, 기사버디
    rest: 'https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod',
    ws: 'wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod'
  },
  t1: {  // title - 제목생성
    rest: 'https://qyfams2iva.execute-api.us-east-1.amazonaws.com/prod',
    ws: 'wss://hsdpbajz23.execute-api.us-east-1.amazonaws.com/prod'
  },
  p1: {  // proofreading - 교열
    rest: 'https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod',
    ws: 'wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod'
  },
  f1: {  // foreign - 외신
    rest: 'https://razlubfzw1.execute-api.us-east-1.amazonaws.com/prod',
    ws: 'wss://5c6e29dg50.execute-api.us-east-1.amazonaws.com/prod'
  },
  w1: {  // bodo - 보도자료
    rest: 'https://16ayefk5lc.execute-api.us-east-1.amazonaws.com/prod',
    ws: 'wss://prsebeg7ub.execute-api.us-east-1.amazonaws.com/prod'
  },
  r1: {  // regression - 퇴고
    rest: 'https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod',
    ws: 'wss://ebqodb8ax9.execute-api.us-east-1.amazonaws.com/prod'
  }
};

export const BUDDY_CONFIG = {
  '일보버디': {
    serviceCode: 'b1',
    promptTable: 'p2-two-prompts-two',
    promptType: 'ilbo',
    engineType: '11'
  },
  '기사버디': {
    serviceCode: 'b1',
    promptTable: 'p2-two-prompts-two',
    promptType: 'article',
    engineType: '22'
  },
  '보도자료_기업': {
    serviceCode: 'w1',
    promptTable: 'w1-prompts',
    promptType: 'corporate',
    engineType: '11'
  },
  '보도자료_공공': {
    serviceCode: 'w1',
    promptTable: 'w1-prompts',
    promptType: 'public',
    engineType: '22'
  },
  '외신_영어': {
    serviceCode: 'f1',
    promptTable: 'f1-prompts-two',
    promptType: 'english',
    engineType: '11'
  },
  '외신_일어': {
    serviceCode: 'f1',
    promptTable: 'f1-prompts-two',
    promptType: 'japanese',
    engineType: '22'
  },
  '퇴고_단문': {
    serviceCode: 'r1',
    promptTable: 'sedaily-column-prompts',
    promptType: 'short',
    engineType: '11'
  },
  '퇴고_장문': {
    serviceCode: 'r1',
    promptTable: 'sedaily-column-prompts',
    promptType: 'long',
    engineType: '22'
  },
  '제목생성_5종': {
    serviceCode: 't1',
    promptTable: 'nx-tt-dev-ver3-prompts',
    promptType: 'five_types',
    engineType: 'C7'
  },
  '제목창의_7종': {
    serviceCode: 't1',
    promptTable: 'nx-tt-dev-ver3-prompts',
    promptType: 'seven_types',
    engineType: 'C7'
  },
  '교열_경제분야': {
    serviceCode: 'p1',
    promptTable: 'nx-wt-prf-prompts',
    promptType: 'economy',
    engineType: '11'
  },
  '교열_사회분야': {
    serviceCode: 'p1',
    promptTable: 'nx-wt-prf-prompts',
    promptType: 'society',
    engineType: '11'
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

// 버디 타입에 해당하는 서비스 엔드포인트 반환
export const getServiceEndpoint = (buddyType) => {
  const config = BUDDY_CONFIG[buddyType];
  if (!config) {
    // 기본값: buddy 서비스 (b1)
    return SERVICE_ENDPOINTS.b1;
  }
  return SERVICE_ENDPOINTS[config.serviceCode] || SERVICE_ENDPOINTS.b1;
};

// 서비스 코드로 엔드포인트 반환
export const getEndpointByServiceCode = (serviceCode) => {
  return SERVICE_ENDPOINTS[serviceCode] || SERVICE_ENDPOINTS.b1;
};

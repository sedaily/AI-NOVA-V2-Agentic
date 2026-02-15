import React, { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Save,
  Send,
  Sparkles,
  Bot,
  CheckCircle,
  FileText,
  Clock,
  ChevronDown,
  Bold,
  Italic,
  Underline,
  List,
  ListOrdered,
  Quote,
  Link2,
  Image,
  Undo,
  Redo,
  Wand2,
  X,
  Check,
  Loader2,
  Eye,
  TrendingUp,
  Flame,
  Newspaper,
  Globe,
  Building2,
  Landmark,
  Cpu,
  Upload,
  Clipboard,
  Monitor,
  Smartphone,
  FileEdit,
  Zap,
  ExternalLink,
  RefreshCw,
  ChevronRight,
  Copy,
  Trash2,
  AlertCircle,
  Type,
  RotateCcw,
} from "lucide-react";

// AI Agent Services
import articleAgentService, { ARTICLE_TYPE_CONFIG } from "../services/articleAgentService";
import useAgentWorkflow from "../hooks/useAgentWorkflow";
import AgentProgressPanel from "./AgentProgressPanel";

// 오늘의 이슈 데이터
const TRENDING_TOPICS = [
  {
    id: 1,
    category: "산업",
    title: "삼성전자 HBM4 양산 임박",
    description: "엔비디아 납품 계약 체결, 2분기 본격 양산 전망",
    icon: <Cpu className="w-5 h-5" />,
    color: "from-blue-500 to-cyan-500",
    keywords: ["삼성전자", "HBM4", "반도체", "엔비디아"],
    heat: 98,
  },
  {
    id: 2,
    category: "정책",
    title: "2026년 추경 15조원 편성",
    description: "민생안정·경기부양 목적, 이번 주 국회 제출 예정",
    icon: <Landmark className="w-5 h-5" />,
    color: "from-violet-500 to-purple-500",
    keywords: ["추경", "정부예산", "민생안정"],
    heat: 95,
  },
  {
    id: 3,
    category: "금융",
    title: "기준금리 인하 기대감 확산",
    description: "한국은행, 다음 달 금통위에서 동결 또는 인하 결정",
    icon: <Building2 className="w-5 h-5" />,
    color: "from-emerald-500 to-teal-500",
    keywords: ["기준금리", "한국은행", "금통위"],
    heat: 92,
  },
];

// 관련 뉴스 (보도자료 분석 후 표시)
const RELATED_NEWS = [
  {
    id: 1,
    title: "삼성전자, HBM3E 양산 본격화...SK하이닉스와 격차 좁힌다",
    source: "전자신문",
    time: "2시간 전",
    url: "#",
  },
  {
    id: 2,
    title: "엔비디아, 차세대 GPU 블랙웰 수요 폭발...HBM 공급 부족 우려",
    source: "연합뉴스",
    time: "3시간 전",
    url: "#",
  },
  {
    id: 3,
    title: "반도체 업계, AI 서버용 HBM 시장 2027년까지 3배 성장 전망",
    source: "서울경제",
    time: "5시간 전",
    url: "#",
  },
];

// 기사 유형
const ARTICLE_TYPES = [
  {
    id: "daily",
    title: "일보 작성",
    description: "간결한 팩트 중심의 속보형 기사",
    icon: <Zap className="w-6 h-6" />,
    color: "from-amber-500 to-orange-500",
    features: ["300~500자", "핵심 팩트 위주", "빠른 배포"],
  },
  {
    id: "print",
    title: "지면 기사",
    description: "심층 분석과 맥락을 담은 기사",
    icon: <Newspaper className="w-6 h-6" />,
    color: "from-violet-500 to-purple-600",
    features: ["1000~1500자", "배경 설명 포함", "인용구 활용"],
  },
  {
    id: "online",
    title: "온라인 기사",
    description: "클릭을 유도하는 웹 최적화 기사",
    icon: <Monitor className="w-6 h-6" />,
    color: "from-emerald-500 to-teal-500",
    features: ["800~1200자", "SEO 최적화", "소제목 활용"],
  },
];

const ArticleEditor = () => {
  const navigate = useNavigate();
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // 위자드 단계
  const [currentStep, setCurrentStep] = useState(1);
  const [sourceType, setSourceType] = useState(null); // 'press' | 'topic'
  const [pressRelease, setPressRelease] = useState("");
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [selectedArticleType, setSelectedArticleType] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  // 에디터 상태
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState([]);

  // AI Agent 상태
  const [engineType, setEngineType] = useState("11"); // 11: 기업, 22: 정부/공공
  const [generatedTitles, setGeneratedTitles] = useState([]);
  const [showTitleOptions, setShowTitleOptions] = useState(false);
  const [proofreadResult, setProofreadResult] = useState(null);
  const [showProofreadModal, setShowProofreadModal] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [isGeneratingTitles, setIsGeneratingTitles] = useState(false);
  const [isProofreading, setIsProofreading] = useState(false);
  const [isRevising, setIsRevising] = useState(false);

  // Agent 워크플로우 Hook
  const agentWorkflow = useAgentWorkflow();
  const [useAgentMode, setUseAgentMode] = useState(true); // Agent 모드 사용 여부

  // 글자수 계산
  const wordCount = content.length;
  const charCountWithoutSpaces = content.replace(/\s/g, "").length;

  // Agent 워크플로우 결과 동기화
  useEffect(() => {
    if (agentWorkflow.draft && agentWorkflow.draft !== content) {
      setContent(agentWorkflow.draft);
    }
    if (agentWorkflow.titles?.length > 0 && generatedTitles.length === 0) {
      setGeneratedTitles(agentWorkflow.titles);
    }
  }, [agentWorkflow.draft, agentWorkflow.titles]);

  // 보도자료 분석 (AI Agent 연동)
  const analyzePress = async () => {
    if (!pressRelease.trim()) return;
    setIsAnalyzing(true);
    setAiError(null);

    try {
      // AI로 보도자료 분석
      const analysis = await articleAgentService.analyzePressRelease(pressRelease, engineType);

      // 관련 뉴스 검색
      let relatedNews = RELATED_NEWS; // 폴백 데이터
      try {
        const searchResult = await articleAgentService.searchRelatedNews(
          analysis.keywords?.join(" ") || pressRelease.substring(0, 100)
        );
        if (searchResult.success && searchResult.citations?.length > 0) {
          relatedNews = searchResult.citations.slice(0, 5).map((cite, idx) => ({
            id: idx + 1,
            title: cite.title || cite,
            source: cite.source || "외부",
            time: "방금 전",
            url: cite.url || "#",
          }));
        }
      } catch (searchError) {
        console.warn("관련 뉴스 검색 실패, 기본 데이터 사용:", searchError);
      }

      setAnalysisResult({
        summary: analysis.summary || analysis.rawAnalysis || "분석 완료",
        keywords: analysis.keywords || ["경제", "산업"],
        category: analysis.suggestedAngles?.[0] || "경제 · 산업",
        relatedNews,
        economicImpact: analysis.economicImpact,
        suggestedAngles: analysis.suggestedAngles,
      });
      setCurrentStep(2);
    } catch (error) {
      console.error("보도자료 분석 실패:", error);
      setAiError("AI 분석에 실패했습니다. 다시 시도해주세요.");
      // 폴백: 기본 분석 결과
      setAnalysisResult({
        summary: "보도자료 분석 결과입니다.",
        keywords: ["경제", "산업"],
        category: "경제 · 산업",
        relatedNews: RELATED_NEWS,
      });
      setCurrentStep(2);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 토픽 선택 시
  const selectTopic = (topic) => {
    setSelectedTopic(topic);
    setSourceType("topic");
    setAnalysisResult({
      summary: topic.description,
      keywords: topic.keywords,
      category: topic.category,
      relatedNews: RELATED_NEWS,
    });
    setCurrentStep(2);
  };

  // 기사 유형 선택 후 AI 생성
  const generateArticle = async () => {
    setCurrentStep(4);
    setAiLoading(true);
    setAiError(null);

    const source = sourceType === "press" ? pressRelease : selectedTopic?.description;
    const articleType = ARTICLE_TYPES.find((t) => t.id === selectedArticleType);

    try {
      // Agent 워크플로우 모드 사용
      if (useAgentMode) {
        // 워크플로우 시작
        await agentWorkflow.startWorkflow({
          articleType: selectedArticleType,
          engineType,
          pressRelease: sourceType === "press" ? pressRelease : "",
          topic: sourceType === "topic" ? selectedTopic?.title : "",
          keywords: analysisResult?.keywords || [],
        });

        // 워크플로우 실행
        const result = await agentWorkflow.runWorkflow("full");

        // 결과 적용
        if (result.draft) {
          const lines = result.draft.split("\n").filter(line => line.trim());
          let extractedTitle = "";
          let extractedContent = "";

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith("#")) {
              extractedTitle = line.replace(/^#+\s*/, "").replace(/\*+/g, "");
              extractedContent = lines.slice(i + 1).join("\n").trim();
              break;
            } else if (i === 0 && !line.startsWith("-") && !line.startsWith("*")) {
              extractedTitle = line.replace(/\*+/g, "");
              extractedContent = lines.slice(1).join("\n").trim();
              break;
            }
          }

          setTitle(extractedTitle || result.titles?.[0]?.title || "새 기사");
          setContent(extractedContent || result.draft);
        }

        if (result.titles) {
          setGeneratedTitles(result.titles);
        }

        setCategory(analysisResult?.category || "경제 · 산업");

      } else {
        // 기존 방식: 단순 API 호출
        const generatedContent = await articleAgentService.generateArticle({
          pressRelease: sourceType === "press" ? pressRelease : null,
          topic: sourceType === "topic" ? selectedTopic?.title : null,
          articleType: selectedArticleType,
          engineType,
          additionalContext: analysisResult?.summary || "",
        });

        // 생성된 기사에서 제목과 본문 분리
        const lines = generatedContent.split("\n").filter(line => line.trim());
        let extractedTitle = "";
        let extractedContent = "";

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          if (line.startsWith("#")) {
            extractedTitle = line.replace(/^#+\s*/, "").replace(/\*+/g, "");
            extractedContent = lines.slice(i + 1).join("\n").trim();
            break;
          } else if (i === 0 && !line.startsWith("-") && !line.startsWith("*")) {
            extractedTitle = line.replace(/\*+/g, "");
            extractedContent = lines.slice(1).join("\n").trim();
            break;
          }
        }

        if (!extractedTitle) {
          extractedTitle = analysisResult?.summary?.substring(0, 50) || "새 기사";
          extractedContent = generatedContent;
        }

        setTitle(extractedTitle);
        setContent(extractedContent || generatedContent);
        setCategory(analysisResult?.category || "경제 · 산업");
      }

    } catch (error) {
      console.error("기사 생성 실패:", error);
      setAiError("기사 생성에 실패했습니다. 다시 시도해주세요.");

      // 폴백: 기본 템플릿
      setTitle("새 기사");
      setContent(`[기사 내용을 작성해주세요]

소재: ${source || "없음"}
유형: ${articleType?.title || "미선택"}`);
      setCategory("경제 · 산업");
    } finally {
      setAiLoading(false);
    }
  };

  // AI 제목 재생성
  const regenerateTitles = async () => {
    if (!content.trim()) return;
    setIsGeneratingTitles(true);
    setAiError(null);

    try {
      const titles = await articleAgentService.generateTitles(content, 5);
      setGeneratedTitles(titles);
      setShowTitleOptions(true);
    } catch (error) {
      console.error("제목 생성 실패:", error);
      setAiError("제목 생성에 실패했습니다.");
    } finally {
      setIsGeneratingTitles(false);
    }
  };

  // AI 교열
  const proofreadArticle = async () => {
    if (!content.trim()) return;
    setIsProofreading(true);
    setAiError(null);

    try {
      const result = await articleAgentService.proofreadArticle(content);
      setProofreadResult(result);
      setShowProofreadModal(true);
    } catch (error) {
      console.error("교열 실패:", error);
      setAiError("교열에 실패했습니다.");
    } finally {
      setIsProofreading(false);
    }
  };

  // AI 퇴고 (문장 다듬기)
  const reviseArticle = async () => {
    if (!content.trim()) return;
    setIsRevising(true);
    setAiError(null);

    try {
      const revisedContent = await articleAgentService.reviseArticle(content);
      setContent(revisedContent);
    } catch (error) {
      console.error("퇴고 실패:", error);
      setAiError("퇴고에 실패했습니다.");
    } finally {
      setIsRevising(false);
    }
  };

  // 교정 사항 적용
  const applyCorrection = (original, corrected) => {
    setContent(content.replace(original, corrected));
  };

  // 단계 렌더링
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return renderStep1();
      case 2:
        return renderStep2();
      case 3:
        return renderStep3();
      case 4:
        return renderStep4();
      default:
        return null;
    }
  };

  // Step 1: 소재 선택
  const renderStep1 = () => (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-10">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">어떤 소재로 기사를 작성할까요?</h1>
        <p className="text-gray-500">보도자료를 업로드하거나, 오늘의 이슈를 선택하세요</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-10">
        {/* 보도자료 입력 */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">보도자료 입력</h3>
              <p className="text-sm text-gray-500">텍스트를 붙여넣거나 파일 업로드</p>
            </div>
          </div>

          <textarea
            value={pressRelease}
            onChange={(e) => {
              setPressRelease(e.target.value);
              setSourceType("press");
            }}
            placeholder="보도자료 내용을 여기에 붙여넣으세요..."
            className="w-full h-40 p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500"
          />

          <div className="flex items-center gap-3 mt-4">
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".txt,.pdf,.doc,.docx"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition"
            >
              <Upload className="w-4 h-4" />
              파일 업로드
            </button>
            <button
              onClick={async () => {
                const text = await navigator.clipboard.readText();
                setPressRelease(text);
                setSourceType("press");
              }}
              className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition"
            >
              <Clipboard className="w-4 h-4" />
              붙여넣기
            </button>
          </div>

          {pressRelease && (
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              onClick={analyzePress}
              disabled={isAnalyzing}
              className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-xl font-medium disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  분석 중...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  AI 분석 시작
                </>
              )}
            </motion.button>
          )}
        </div>

        {/* 오늘의 이슈 */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
              <Flame className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">오늘의 이슈</h3>
              <p className="text-sm text-gray-500">실시간 트렌딩 토픽에서 선택</p>
            </div>
          </div>

          <div className="space-y-3">
            {TRENDING_TOPICS.map((topic, idx) => (
              <motion.button
                key={topic.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                onClick={() => selectTopic(topic)}
                className="w-full flex items-center gap-3 p-3 bg-gray-50 hover:bg-violet-50 rounded-xl text-left transition group"
              >
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${topic.color} flex items-center justify-center text-white flex-shrink-0`}>
                  {topic.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-violet-600 bg-violet-100 px-1.5 py-0.5 rounded">
                      {topic.category}
                    </span>
                    <span className="text-xs text-orange-500 font-medium">{topic.heat}%</span>
                  </div>
                  <p className="font-medium text-gray-900 text-sm truncate group-hover:text-violet-600">
                    {topic.title}
                  </p>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-violet-500" />
              </motion.button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Step 2: 관련 정보 확인
  const renderStep2 = () => (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">관련 정보를 확인하세요</h1>
        <p className="text-gray-500">AI가 분석한 내용과 관련 뉴스입니다</p>
      </div>

      {/* 분석 결과 */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="w-5 h-5 text-violet-600" />
          <h3 className="font-semibold text-gray-900">AI 분석 결과</h3>
        </div>

        <div className="bg-violet-50 rounded-xl p-4 mb-4">
          <p className="text-gray-700">{analysisResult?.summary}</p>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          {analysisResult?.keywords.map((keyword, idx) => (
            <span
              key={idx}
              className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm"
            >
              #{keyword}
            </span>
          ))}
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-500">
          <FileText className="w-4 h-4" />
          <span>추천 카테고리: {analysisResult?.category}</span>
        </div>
      </div>

      {/* 관련 뉴스 */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold text-gray-900">관련 뉴스</h3>
          </div>
          <button className="text-sm text-violet-600 hover:text-violet-700 flex items-center gap-1">
            <RefreshCw className="w-4 h-4" />
            새로고침
          </button>
        </div>

        <div className="space-y-3">
          {analysisResult?.relatedNews.map((news) => (
            <a
              key={news.id}
              href={news.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-xl transition group"
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 text-sm group-hover:text-violet-600 truncate">
                  {news.title}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {news.source} · {news.time}
                </p>
              </div>
              <ExternalLink className="w-4 h-4 text-gray-300 group-hover:text-violet-500 flex-shrink-0 ml-3" />
            </a>
          ))}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => setCurrentStep(1)}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
        >
          <ArrowLeft className="w-4 h-4" />
          이전 단계
        </button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setCurrentStep(3)}
          className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-xl font-medium"
        >
          다음 단계
          <ArrowRight className="w-4 h-4" />
        </motion.button>
      </div>
    </div>
  );

  // Step 3: 기사 유형 선택
  const renderStep3 = () => (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-10">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">어떤 기사를 작성할까요?</h1>
        <p className="text-gray-500">기사 유형에 따라 AI가 맞춤 초안을 생성합니다</p>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-10">
        {ARTICLE_TYPES.map((type, idx) => (
          <motion.button
            key={type.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            onClick={() => setSelectedArticleType(type.id)}
            className={`relative p-6 rounded-2xl border-2 text-left transition-all ${
              selectedArticleType === type.id
                ? "border-violet-500 bg-violet-50"
                : "border-gray-100 bg-white hover:border-gray-200"
            }`}
          >
            {selectedArticleType === type.id && (
              <div className="absolute top-4 right-4 w-6 h-6 bg-violet-500 rounded-full flex items-center justify-center">
                <Check className="w-4 h-4 text-white" />
              </div>
            )}

            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${type.color} flex items-center justify-center text-white mb-4`}>
              {type.icon}
            </div>

            <h3 className="font-semibold text-gray-900 mb-1">{type.title}</h3>
            <p className="text-sm text-gray-500 mb-4">{type.description}</p>

            <div className="space-y-1">
              {type.features.map((feature, fIdx) => (
                <div key={fIdx} className="flex items-center gap-2 text-xs text-gray-400">
                  <Check className="w-3 h-3" />
                  {feature}
                </div>
              ))}
            </div>
          </motion.button>
        ))}
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => setCurrentStep(2)}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
        >
          <ArrowLeft className="w-4 h-4" />
          이전 단계
        </button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={generateArticle}
          disabled={!selectedArticleType}
          className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-xl font-medium disabled:opacity-50"
        >
          <Sparkles className="w-4 h-4" />
          AI로 기사 생성
        </motion.button>
      </div>
    </div>
  );

  // Step 4: 에디터
  const renderStep4 = () => (
    <div className="flex gap-6">
      {/* 메인 에디터 */}
      <main className="flex-1 min-w-0">
        {/* 카테고리 */}
        <div className="mb-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-violet-100 text-violet-700 rounded-full text-sm">
            <FileText className="w-3.5 h-3.5" />
            {category}
          </span>
        </div>

        {/* 제목 */}
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="제목을 입력하세요"
          className="w-full text-3xl font-bold text-gray-900 placeholder-gray-300 border-0 bg-transparent focus:outline-none mb-6"
        />

        {/* 툴바 */}
        <div className="flex items-center gap-1 mb-4 pb-4 border-b border-gray-100">
          <div className="flex items-center gap-1 pr-3 border-r border-gray-200">
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"><Bold className="w-4 h-4" /></button>
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"><Italic className="w-4 h-4" /></button>
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"><Underline className="w-4 h-4" /></button>
          </div>
          <div className="flex items-center gap-1 px-3 border-r border-gray-200">
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"><List className="w-4 h-4" /></button>
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"><ListOrdered className="w-4 h-4" /></button>
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"><Quote className="w-4 h-4" /></button>
          </div>
          <div className="flex items-center gap-1 px-3">
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"><Link2 className="w-4 h-4" /></button>
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"><Image className="w-4 h-4" /></button>
          </div>
        </div>

        {/* 본문 */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6 min-h-[400px]">
          {aiLoading ? (
            <div className="flex flex-col items-center justify-center h-80">
              <Loader2 className="w-10 h-10 text-violet-500 animate-spin mb-4" />
              <p className="text-gray-600 font-medium">AI가 기사를 작성하고 있습니다...</p>
              <p className="text-sm text-gray-400 mt-1">잠시만 기다려주세요</p>
            </div>
          ) : (
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="본문을 입력하세요..."
              className="w-full h-full min-h-[360px] text-gray-800 border-0 bg-transparent focus:outline-none resize-none leading-relaxed"
            />
          )}
        </div>

        {/* 하단 정보 */}
        <div className="flex items-center justify-between mt-4 text-sm text-gray-400">
          <div className="flex items-center gap-4">
            <span>{wordCount.toLocaleString()}자</span>
            <span>공백 제외 {charCountWithoutSpaces.toLocaleString()}자</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span>예상 읽기 시간: {Math.max(1, Math.ceil(wordCount / 500))}분</span>
          </div>
        </div>
      </main>

      {/* AI 도구 패널 */}
      <aside className="w-72 flex-shrink-0">
        <div className="sticky top-24 space-y-4">
          {/* Agent 워크플로우 진행 상태 */}
          {useAgentMode && (agentWorkflow.isRunning || agentWorkflow.progress > 0) && (
            <AgentProgressPanel
              isRunning={agentWorkflow.isRunning}
              currentStep={agentWorkflow.currentStep}
              progress={agentWorkflow.progress}
              phase={agentWorkflow.phase}
              qualityScore={agentWorkflow.qualityScore}
              logs={agentWorkflow.logs}
              error={agentWorkflow.error}
            />
          )}

          {/* 에러 표시 */}
          {aiError && (
            <div className="bg-red-50 border border-red-100 rounded-xl p-3">
              <div className="flex items-center gap-2 text-red-600 text-sm">
                <AlertCircle className="w-4 h-4" />
                <span>{aiError}</span>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-gray-100 p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">AI 도구</h3>
            <div className="space-y-2">
              <button
                onClick={regenerateTitles}
                disabled={isGeneratingTitles || !content.trim()}
                className="w-full flex items-center gap-3 p-3 bg-violet-50 hover:bg-violet-100 rounded-xl transition disabled:opacity-50"
              >
                {isGeneratingTitles ? (
                  <Loader2 className="w-5 h-5 text-violet-600 animate-spin" />
                ) : (
                  <Type className="w-5 h-5 text-violet-600" />
                )}
                <span className="text-sm font-medium text-gray-700">
                  {isGeneratingTitles ? "생성 중..." : "제목 재생성"}
                </span>
              </button>
              <button
                onClick={proofreadArticle}
                disabled={isProofreading || !content.trim()}
                className="w-full flex items-center gap-3 p-3 bg-emerald-50 hover:bg-emerald-100 rounded-xl transition disabled:opacity-50"
              >
                {isProofreading ? (
                  <Loader2 className="w-5 h-5 text-emerald-600 animate-spin" />
                ) : (
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                )}
                <span className="text-sm font-medium text-gray-700">
                  {isProofreading ? "검토 중..." : "교열하기"}
                </span>
              </button>
              <button
                onClick={reviseArticle}
                disabled={isRevising || !content.trim()}
                className="w-full flex items-center gap-3 p-3 bg-amber-50 hover:bg-amber-100 rounded-xl transition disabled:opacity-50"
              >
                {isRevising ? (
                  <Loader2 className="w-5 h-5 text-amber-600 animate-spin" />
                ) : (
                  <Wand2 className="w-5 h-5 text-amber-600" />
                )}
                <span className="text-sm font-medium text-gray-700">
                  {isRevising ? "다듬는 중..." : "문장 다듬기"}
                </span>
              </button>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">분석 정보</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">카테고리</span>
                <span className="text-gray-900">{category}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">기사 유형</span>
                <span className="text-gray-900">{ARTICLE_TYPES.find(t => t.id === selectedArticleType)?.title}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">엔진</span>
                <span className="text-gray-900">{engineType === "11" ? "기업" : "정부/공공"}</span>
              </div>
            </div>
          </div>

          {/* 엔진 선택 */}
          <div className="bg-white rounded-2xl border border-gray-100 p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">AI 엔진</h3>
            <div className="flex gap-2">
              <button
                onClick={() => setEngineType("11")}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition ${
                  engineType === "11"
                    ? "bg-violet-500 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                기업
              </button>
              <button
                onClick={() => setEngineType("22")}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition ${
                  engineType === "22"
                    ? "bg-violet-500 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                정부/공공
              </button>
            </div>
          </div>

          {/* Agent 모드 토글 */}
          <div className="bg-white rounded-2xl border border-gray-100 p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-gray-900">Agent 모드</h3>
                <p className="text-xs text-gray-500 mt-0.5">16개 AI 에이전트 협업</p>
              </div>
              <button
                onClick={() => setUseAgentMode(!useAgentMode)}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  useAgentMode ? "bg-violet-500" : "bg-gray-200"
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    useAgentMode ? "translate-x-5" : ""
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* 제목 선택 모달 */}
      <AnimatePresence>
        {showTitleOptions && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowTitleOptions(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl max-w-lg w-full p-6 max-h-[80vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">제목 선택</h3>
                <button
                  onClick={() => setShowTitleOptions(false)}
                  className="p-2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="space-y-3">
                {generatedTitles.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setTitle(item.title);
                      setShowTitleOptions(false);
                    }}
                    className="w-full p-4 text-left bg-gray-50 hover:bg-violet-50 rounded-xl transition group"
                  >
                    <span className="text-xs text-violet-600 bg-violet-100 px-2 py-0.5 rounded-full">
                      {item.type}
                    </span>
                    <p className="mt-2 text-gray-900 font-medium group-hover:text-violet-600">
                      {item.title}
                    </p>
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 교열 결과 모달 */}
      <AnimatePresence>
        {showProofreadModal && proofreadResult && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowProofreadModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl max-w-2xl w-full p-6 max-h-[80vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold text-gray-900">교열 결과</h3>
                  {proofreadResult.overallScore && (
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      proofreadResult.overallScore >= 80
                        ? "bg-emerald-100 text-emerald-700"
                        : proofreadResult.overallScore >= 60
                        ? "bg-amber-100 text-amber-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {proofreadResult.overallScore}점
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setShowProofreadModal(false)}
                  className="p-2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* 수정 사항 */}
              {proofreadResult.corrections?.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">수정 사항</h4>
                  <div className="space-y-2">
                    {proofreadResult.corrections.map((item, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded-xl">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-red-500 line-through text-sm">{item.original}</span>
                          <ArrowRight className="w-4 h-4 text-gray-400" />
                          <span className="text-emerald-600 font-medium text-sm">{item.corrected}</span>
                        </div>
                        <p className="text-xs text-gray-500">{item.reason}</p>
                        <button
                          onClick={() => applyCorrection(item.original, item.corrected)}
                          className="mt-2 text-xs text-violet-600 hover:text-violet-700"
                        >
                          적용하기
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 제안 사항 */}
              {proofreadResult.suggestions?.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">개선 제안</h4>
                  <ul className="space-y-1">
                    {proofreadResult.suggestions.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                        <Check className="w-4 h-4 text-violet-500 mt-0.5 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 원본 피드백 (JSON 파싱 실패 시) */}
              {proofreadResult.rawFeedback && (
                <div className="p-4 bg-gray-50 rounded-xl text-sm text-gray-700 whitespace-pre-wrap">
                  {proofreadResult.rawFeedback}
                </div>
              )}

              <button
                onClick={() => setShowProofreadModal(false)}
                className="w-full mt-4 py-2.5 bg-violet-500 text-white rounded-xl font-medium hover:bg-violet-600 transition"
              >
                확인
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#FAFAFA" }}>
      {/* 헤더 */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/")}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>

              {/* 스텝 인디케이터 */}
              <div className="hidden md:flex items-center gap-2">
                {["소재 선택", "관련 정보", "기사 유형", "작성"].map((step, idx) => (
                  <div key={idx} className="flex items-center">
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                        currentStep > idx + 1
                          ? "bg-violet-500 text-white"
                          : currentStep === idx + 1
                          ? "bg-violet-100 text-violet-600 ring-2 ring-violet-500"
                          : "bg-gray-100 text-gray-400"
                      }`}
                    >
                      {currentStep > idx + 1 ? <Check className="w-3 h-3" /> : idx + 1}
                    </div>
                    <span className={`ml-2 text-sm ${currentStep === idx + 1 ? "text-gray-900 font-medium" : "text-gray-400"}`}>
                      {step}
                    </span>
                    {idx < 3 && <ChevronRight className="w-4 h-4 text-gray-300 mx-2" />}
                  </div>
                ))}
              </div>
            </div>

            {currentStep === 4 && (
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg border border-gray-200">
                  <Save className="w-4 h-4" />
                  임시저장
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-lg font-medium"
                >
                  <Send className="w-4 h-4" />
                  발행하기
                </motion.button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 콘텐츠 */}
      <div className="max-w-5xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {renderStep()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ArticleEditor;

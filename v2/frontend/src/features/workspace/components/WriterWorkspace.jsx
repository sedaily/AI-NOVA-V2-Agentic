import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Plus,
  Search,
  Settings,
  ChevronRight,
  Bell,
  User,
  Edit3,
  Bot,
  MoreHorizontal,
  Clock,
  CheckCircle,
  Sparkles,
  ExternalLink,
  PenTool,
  Eye,
  Trash2,
  Copy,
  Star,
} from "lucide-react";

// 샘플 기사 데이터
const SAMPLE_ARTICLES = [
  {
    id: "1",
    title: "삼성전자, 반도체 투자 80조원 발표...AI 시대 선제 대응",
    excerpt: "삼성전자가 향후 5년간 반도체 분야에 80조원을 투자한다고 밝혔다. 이는 AI 반도체 시장 선점을 위한...",
    status: "draft",
    category: "경제 · 산업",
    createdAt: "2시간 전",
    wordCount: 1520,
  },
  {
    id: "2",
    title: "정부, 2026년 추경 15조원 편성 검토...민생 안정 초점",
    excerpt: "정부가 2026년 추가경정예산 15조원 규모를 검토 중인 것으로 알려졌다. 민생 안정과 경기 부양을...",
    status: "review",
    category: "정치 · 정책",
    createdAt: "어제",
    wordCount: 2100,
  },
  {
    id: "3",
    title: "코스피 3000선 재돌파 전망...외국인 매수세 지속",
    excerpt: "코스피 지수가 3000선을 재돌파할 것이라는 전망이 나왔다. 외국인 투자자들의 순매수세가...",
    status: "published",
    category: "경제 · 증권",
    createdAt: "2일 전",
    wordCount: 1850,
    views: 1520,
  },
  {
    id: "4",
    title: "LG에너지솔루션, 북미 배터리 공장 증설 발표",
    excerpt: "LG에너지솔루션이 북미 지역 배터리 생산 능력을 대폭 확대한다. 전기차 수요 증가에 대응하기 위해...",
    status: "published",
    category: "경제 · 산업",
    createdAt: "3일 전",
    wordCount: 1680,
    views: 2340,
  },
];

const STATUS_CONFIG = {
  draft: { label: "작성중", bgColor: "bg-amber-50", textColor: "text-amber-600", dotColor: "bg-amber-400" },
  review: { label: "검토중", bgColor: "bg-blue-50", textColor: "text-blue-600", dotColor: "bg-blue-400" },
  published: { label: "발행됨", bgColor: "bg-green-50", textColor: "text-green-600", dotColor: "bg-green-400" },
};

const WriterWorkspace = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("articles");
  const [articles] = useState(SAMPLE_ARTICLES);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [hoveredArticle, setHoveredArticle] = useState(null);

  // 필터링된 기사
  const filteredArticles = articles.filter((article) => {
    if (filterStatus !== "all" && article.status !== filterStatus) return false;
    if (searchQuery && !article.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#FAFAFA" }}>
      {/* 헤더 */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            {/* 로고 */}
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <span className="text-lg font-semibold text-gray-900">AI NOVA</span>
              </div>

              {/* 네비게이션 탭 */}
              <nav className="hidden md:flex items-center gap-1">
                {[
                  { id: "articles", label: "내 기사", icon: <FileText className="w-4 h-4" /> },
                  { id: "ai-write", label: "AI 글쓰기", icon: <Bot className="w-4 h-4" /> },
                  { id: "tools", label: "AI 도구", icon: <PenTool className="w-4 h-4" /> },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      activeTab === tab.id
                        ? "bg-violet-50 text-violet-600"
                        : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                    }`}
                  >
                    {tab.icon}
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* 우측 메뉴 */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate("/marketing")}
                className="hidden md:flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 transition"
              >
                <ExternalLink className="w-4 h-4" />
                서비스 소개
              </button>

              <button className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
              </button>

              <button className="flex items-center gap-2 pl-3 pr-2 py-1.5 bg-gray-50 hover:bg-gray-100 rounded-full transition">
                <span className="text-sm font-medium text-gray-700">홍길동</span>
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-400 to-purple-500 flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* 페이지 타이틀 & 액션 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">내 기사</h1>
            <p className="text-gray-500">총 {filteredArticles.length}개의 기사</p>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate("/editor")}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-xl font-medium shadow-lg shadow-violet-500/25 hover:shadow-xl hover:shadow-violet-500/30 transition-shadow"
          >
            <Plus className="w-5 h-5" />
            새 기사 작성
          </motion.button>
        </div>

        {/* 검색 & 필터 */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-6">
          {/* 검색 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="기사 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition"
            />
          </div>

          {/* 필터 칩 */}
          <div className="flex items-center gap-2">
            {[
              { id: "all", label: "전체" },
              { id: "draft", label: "작성중" },
              { id: "review", label: "검토중" },
              { id: "published", label: "발행됨" },
            ].map((filter) => (
              <button
                key={filter.id}
                onClick={() => setFilterStatus(filter.id)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  filterStatus === filter.id
                    ? "bg-gray-900 text-white"
                    : "bg-white text-gray-600 border border-gray-200 hover:border-gray-300"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {/* 기사 카드 리스트 */}
        <div className="space-y-4">
          <AnimatePresence>
            {filteredArticles.length > 0 ? (
              filteredArticles.map((article, index) => (
                <motion.div
                  key={article.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  onMouseEnter={() => setHoveredArticle(article.id)}
                  onMouseLeave={() => setHoveredArticle(null)}
                  className="group bg-white rounded-2xl p-5 border border-gray-100 hover:border-gray-200 hover:shadow-lg hover:shadow-gray-100/50 transition-all cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* 상태 & 카테고리 */}
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_CONFIG[article.status].bgColor} ${STATUS_CONFIG[article.status].textColor}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${STATUS_CONFIG[article.status].dotColor}`} />
                          {STATUS_CONFIG[article.status].label}
                        </span>
                        <span className="text-xs text-gray-400">{article.category}</span>
                      </div>

                      {/* 제목 */}
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-violet-600 transition-colors">
                        {article.title}
                      </h3>

                      {/* 요약 */}
                      <p className="text-sm text-gray-500 line-clamp-2 mb-3">
                        {article.excerpt}
                      </p>

                      {/* 메타 정보 */}
                      <div className="flex items-center gap-4 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {article.createdAt}
                        </span>
                        <span>{article.wordCount.toLocaleString()}자</span>
                        {article.views && (
                          <span className="flex items-center gap-1">
                            <Eye className="w-3.5 h-3.5" />
                            {article.views.toLocaleString()}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* 액션 버튼 */}
                    <div className={`flex items-center gap-1 transition-opacity ${hoveredArticle === article.id ? "opacity-100" : "opacity-0"}`}>
                      <button className="p-2 text-gray-400 hover:text-violet-600 hover:bg-violet-50 rounded-lg transition">
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition">
                        <Copy className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16"
              >
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 flex items-center justify-center">
                  <FileText className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-1">기사가 없습니다</h3>
                <p className="text-gray-500 mb-6">새 기사를 작성하여 시작해보세요.</p>
                <button
                  onClick={() => navigate("/editor")}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-violet-500 text-white rounded-xl font-medium hover:bg-violet-600 transition"
                >
                  <Plus className="w-5 h-5" />
                  새 기사 작성
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* AI 도구 퀵 액세스 */}
        <div className="mt-12">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">AI 도구</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              {
                icon: <Bot className="w-6 h-6" />,
                title: "AI 기사 작성",
                description: "보도자료로 기사 초안 생성",
                color: "from-violet-500 to-purple-600",
                action: () => navigate("/editor"),
              },
              {
                icon: <Sparkles className="w-6 h-6" />,
                title: "AI 제목 생성",
                description: "클릭을 부르는 헤드라인",
                color: "from-amber-500 to-orange-500",
                action: () => navigate("/editor"),
              },
              {
                icon: <CheckCircle className="w-6 h-6" />,
                title: "AI 교열",
                description: "맞춤법, 문법 자동 교정",
                color: "from-emerald-500 to-teal-500",
                action: () => navigate("/editor"),
              },
            ].map((tool, idx) => (
              <motion.button
                key={idx}
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={tool.action}
                className="flex items-center gap-4 p-4 bg-white rounded-2xl border border-gray-100 hover:border-gray-200 hover:shadow-lg transition-all text-left"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${tool.color} flex items-center justify-center text-white`}>
                  {tool.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{tool.title}</h3>
                  <p className="text-sm text-gray-500">{tool.description}</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-300 ml-auto" />
              </motion.button>
            ))}
          </div>
        </div>
      </main>

      {/* 플로팅 버튼 (모바일) */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => navigate("/editor")}
        className="fixed bottom-6 right-6 md:hidden w-14 h-14 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-full shadow-lg shadow-violet-500/30 flex items-center justify-center"
      >
        <Plus className="w-6 h-6" />
      </motion.button>
    </div>
  );
};

export default WriterWorkspace;

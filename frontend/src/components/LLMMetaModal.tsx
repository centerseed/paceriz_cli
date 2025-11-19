/**
 * LLM 元數據顯示 Modal
 *
 * 顯示週課表或週回顧的 LLM 生成記錄（prompt 和 response）
 */
import { useState } from 'react';
import { X, ChevronDown, ChevronUp } from 'lucide-react';

interface LLMMetaModalProps {
  isOpen: boolean;
  onClose: () => void;
  type: 'weekly-plan' | 'weekly-summary';
  data: any;
}

export default function LLMMetaModal({ isOpen, onClose, type, data }: LLMMetaModalProps) {
  const [activeTab, setActiveTab] = useState<'stage1' | 'stage2'>('stage1');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    stage1_prompt: false,
    stage1_response: false,
    stage2_prompt: false,
    stage2_response: false,
    summary_prompt: false,
  });

  if (!isOpen) return null;

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const renderTokenInfo = (tokens: any) => {
    if (!tokens) return null;
    return (
      <div className="text-sm text-gray-600 space-y-1">
        <div>Prompt Tokens: {tokens.prompt_tokens || 0}</div>
        <div>Completion Tokens: {tokens.completion_tokens || 0}</div>
        <div>Total Tokens: {tokens.total_tokens || 0}</div>
      </div>
    );
  };

  const renderCollapsibleSection = (
    title: string,
    content: string,
    sectionKey: string,
    extraInfo?: React.ReactNode
  ) => {
    const isExpanded = expandedSections[sectionKey];
    return (
      <div className="border border-gray-200 rounded-md">
        <button
          onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50"
        >
          <div className="flex items-center gap-2">
            <span className="font-semibold">{title}</span>
            {extraInfo}
          </div>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </button>
        {isExpanded && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <pre className="whitespace-pre-wrap text-sm font-mono text-gray-800 overflow-x-auto">
              {content || 'No content'}
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">
              {type === 'weekly-plan' ? '週課表 LLM 生成記錄' : '週回顧 LLM 生成記錄'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {type === 'weekly-plan' && data?.stage1 && data?.stage2 && (
              <>
                {/* Tabs */}
                <div className="flex gap-2 mb-6 border-b border-gray-200">
                  <button
                    onClick={() => setActiveTab('stage1')}
                    className={`px-4 py-2 font-semibold transition-colors ${
                      activeTab === 'stage1'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Stage 1 (文字生成)
                  </button>
                  <button
                    onClick={() => setActiveTab('stage2')}
                    className={`px-4 py-2 font-semibold transition-colors ${
                      activeTab === 'stage2'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Stage 2 (JSON 轉換)
                  </button>
                </div>

                {/* Stage 1 Content */}
                {activeTab === 'stage1' && (
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                      <div className="font-semibold text-blue-900 mb-2">Model Info</div>
                      <div className="text-sm text-blue-800">Model: {data.stage1.model}</div>
                      <div className="text-sm text-blue-800 mt-1">
                        Timestamp: {new Date(data.stage1.timestamp).toLocaleString('zh-TW')}
                      </div>
                      <div className="mt-3">
                        {renderTokenInfo(data.stage1.tokens)}
                      </div>
                    </div>

                    {renderCollapsibleSection(
                      'Prompt',
                      data.stage1.prompt,
                      'stage1_prompt'
                    )}

                    {renderCollapsibleSection(
                      'Response',
                      data.stage1.response,
                      'stage1_response'
                    )}
                  </div>
                )}

                {/* Stage 2 Content */}
                {activeTab === 'stage2' && (
                  <div className="space-y-4">
                    <div className="bg-purple-50 border border-purple-200 rounded-md p-4">
                      <div className="font-semibold text-purple-900 mb-2">Model Info</div>
                      <div className="text-sm text-purple-800">Model: {data.stage2.model}</div>
                      <div className="text-sm text-purple-800 mt-1">
                        Timestamp: {new Date(data.stage2.timestamp).toLocaleString('zh-TW')}
                      </div>
                      <div className="mt-3">
                        {renderTokenInfo(data.stage2.tokens)}
                      </div>
                    </div>

                    {renderCollapsibleSection(
                      'Prompt',
                      data.stage2.prompt,
                      'stage2_prompt'
                    )}

                    {renderCollapsibleSection(
                      'Response (JSON)',
                      data.stage2.response,
                      'stage2_response'
                    )}
                  </div>
                )}
              </>
            )}

            {type === 'weekly-summary' && data && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-md p-4">
                  <div className="font-semibold text-green-900 mb-2">Model Info</div>
                  <div className="text-sm text-green-800">Model: {data.model}</div>
                  <div className="text-sm text-green-800 mt-1">
                    Timestamp: {new Date(data.timestamp).toLocaleString('zh-TW')}
                  </div>
                  <div className="mt-3">
                    {renderTokenInfo(data.tokens)}
                  </div>
                </div>

                {renderCollapsibleSection(
                  'Prompt',
                  data.prompt,
                  'summary_prompt'
                )}
              </div>
            )}

            {!data && (
              <div className="text-center text-gray-500 py-12">
                No LLM metadata available
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              關閉
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

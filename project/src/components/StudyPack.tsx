import React, { useState } from 'react';
import { 
  BookOpen, 
  Star, 
  Clock, 
  Download, 
  ChevronRight,
  ChevronDown,
  Brain,
  Award,
  FileText,
  HelpCircle
} from 'lucide-react';
import { historyAPI } from '../services/api';
import { usePricingStore } from '../stores/pricingStore';

interface StudyPackProps {
  timeLimit: number;
  fileName: string;
  onStartOver: () => void;
  processedData: any;
  historyId?: number; // Add history ID for download functionality
}

export const StudyPack: React.FC<StudyPackProps> = ({ 
  timeLimit, 
  fileName, 
  onStartOver,
  processedData,
  historyId
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([0]));
  const [showQuiz, setShowQuiz] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const { userQuota } = usePricingStore();

  const toggleSection = (index: number) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSections(newExpanded);
  };

  const handleDownload = async () => {
    if (!historyId) {
      alert('Download not available for this session');
      return;
    }

    try {
      setDownloading(true);
      const blob = await historyAPI.downloadPDF(historyId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${fileName.replace('.pdf', '')}_study_pack_${timeLimit}min.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Download failed:', err);
      alert('Failed to download PDF');
    } finally {
      setDownloading(false);
    }
  };

  // Extract data from the API response
  const outline = processedData?.outline?.map((item: any) => item.title) || [];
  const sections = processedData?.condensed_content?.map((chunk: any, index: number) => ({
    title: chunk.headings?.[0] || `Section ${index + 1}`,
    importance: chunk.importance_score > 0.7 ? 'High' : chunk.importance_score > 0.4 ? 'Medium' : 'Low',
    content: chunk.text,
    keyPoints: chunk.keywords || [],
    readingTime: chunk.reading_time_minutes
  })) || [];
  const keyTakeaways = processedData?.key_points || [];
  const quiz = processedData?.quiz || [];
  const keyPointsWarning = processedData?.key_points_warning;
  const processingNotes = processedData?.processing_notes || [];

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'High':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'Low':
        return 'bg-green-100 text-green-700 border-green-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  function cleanEquation(text: string): string {
    // Collapse multiple spaces, join lines that look like equations
    return text
      .replace(/ {2,}/g, ' ')
      .replace(/([=+\-*/^()\dA-Za-z,.]+)\n([=+\-*/^()\dA-Za-z,.]+)/g, '$1 $2');
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Your Study Pack</h1>
              <p className="text-gray-600">{fileName}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>{processedData?.total_reading_time_minutes?.toFixed(1) || timeLimit} minutes</span>
            </div>
            <button 
              onClick={handleDownload}
              disabled={!!(downloading || !historyId || (userQuota && userQuota.plan_type === 'free'))}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                downloading || !historyId || (userQuota && userQuota.plan_type === 'free')
                  ? 'bg-gray-400 text-white cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              <Download className="w-4 h-4" />
              <span>{downloading ? 'Downloading...' : 'Download PDF'}</span>
            </button>
            {userQuota && userQuota.plan_type === 'free' && (
              <span className="text-red-500 text-xs ml-2">Subscribe to download PDFs</span>
            )}
          </div>
        </div>
      </div>

      {/* Quick Outline */}
      <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
        <div className="flex items-center space-x-3 mb-4">
          <FileText className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Study Outline</h2>
        </div>
        <div className="grid gap-2">
          {outline.length > 0 ? (
            outline.map((item: string, index: number) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-semibold text-blue-600">{index + 1}</span>
                </div>
                <span className="text-gray-800">{item}</span>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No outline available</p>
            </div>
          )}
        </div>
      </div>

      {/* Key Sections */}
      <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
        <div className="flex items-center space-x-3 mb-6">
          <Star className="w-5 h-5 text-yellow-500" />
          <h2 className="text-xl font-semibold text-gray-900">Must-Read Sections</h2>
        </div>
        
        <div className="space-y-4">
          {sections.length > 0 ? (
            sections.map((section: any, index: number) => (
              <div key={index} className="border border-gray-200 rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleSection(index)}
                  className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <h3 className="font-semibold text-gray-900">{section.title}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getImportanceColor(section.importance)}`}>
                      {section.importance}
                    </span>
                    {section.readingTime && (
                      <span className="text-sm text-gray-500">
                        {section.readingTime.toFixed(1)} min
                      </span>
                    )}
                  </div>
                  {expandedSections.has(index) ? (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  )}
                </button>
                
                {expandedSections.has(index) && (
                  <div className="p-4 bg-gray-50 border-t border-gray-200">
                    <div className="prose prose-sm max-w-none">
                      <div className="mb-8">
                        <h4 className="font-bold text-lg mb-2 text-purple-700">{section.title}</h4>
                        <div className="whitespace-pre-line text-gray-800 mb-2">
                          {cleanEquation(section.content)}
                        </div>
                      </div>
                      
                      {section.keyPoints && section.keyPoints.length > 0 && (
                        <div className="mt-4">
                          <h4 className="font-semibold text-gray-900 mb-2">Key Points:</h4>
                          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                            {section.keyPoints.slice(0, 5).map((point: string, idx: number) => (
                              <li key={idx}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Star className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No sections available</p>
            </div>
          )}
        </div>
      </div>

      {/* Key Takeaways */}
      {userQuota && userQuota.plan_type !== 'free' && keyTakeaways.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
          <div className="flex items-center space-x-3 mb-6">
            <Award className="w-5 h-5 text-purple-500" />
            <h2 className="text-xl font-semibold text-gray-900">Key Takeaways</h2>
            {keyPointsWarning && (
              <div className="ml-auto">
                <div className="flex items-center space-x-2 px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
                  <span>⚠️</span>
                  <span>Many key points</span>
                </div>
              </div>
            )}
          </div>
          
          {/* Warning banner if there are many key points */}
          {keyPointsWarning && (
            <div className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <span className="text-orange-600 text-lg">⚠️</span>
                <div>
                  <p className="text-orange-800 font-medium">{keyPointsWarning}</p>
                  <p className="text-orange-700 text-sm mt-1">
                    Consider using the 1-hour option for a more comprehensive summary.
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <div className="space-y-3">
            {keyTakeaways.map((takeaway: any, index: number) => (
              <div key={index} className={`flex items-start space-x-3 p-3 rounded-lg ${
                takeaway.category === 'warning' 
                  ? 'bg-red-50 border border-red-200' 
                  : takeaway.category === 'important'
                  ? 'bg-purple-50 border border-purple-200'
                  : 'bg-gray-50 border border-gray-200'
              }`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  takeaway.category === 'warning'
                    ? 'bg-red-100 text-red-600'
                    : takeaway.category === 'important'
                    ? 'bg-purple-100 text-purple-600'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  <span className="text-xs font-semibold">{index + 1}</span>
                </div>
                <div className="flex-1">
                  <p className={`${
                    takeaway.category === 'warning' ? 'text-red-800' : 'text-gray-800'
                  }`}>
                    {cleanEquation(typeof takeaway === 'string' ? takeaway : takeaway.point)}
                  </p>
                  {takeaway.warning && (
                    <div className="mt-2 flex items-center space-x-2 text-sm">
                      <span className="text-orange-600">📊</span>
                      <span className="text-orange-700">{takeaway.warning}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {userQuota && userQuota.plan_type === 'free' && (
        <div className="mt-8 text-center text-red-500 text-sm">
          Key takeaways are available for paid plans only. Upgrade to access!
        </div>
      )}

      {/* Processing Notes */}
      {processingNotes.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <Brain className="w-5 h-5 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900">Processing Notes</h2>
          </div>
          <div className="space-y-2">
            {processingNotes.map((note: string, index: number) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-600 text-lg">💡</span>
                <p className="text-blue-800">{note}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quiz Section */}
      {userQuota && userQuota.plan_type !== 'free' && quiz && quiz.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <HelpCircle className="w-5 h-5 text-green-500" />
              <h2 className="text-xl font-semibold text-gray-900">Knowledge Check</h2>
            </div>
            <button
              onClick={() => setShowQuiz(!showQuiz)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              {showQuiz ? 'Hide Quiz' : 'Take Quiz'}
            </button>
          </div>
          
          {showQuiz && (
            <div className="space-y-6">
              {quiz.map((question: any, index: number) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3">
                    {index + 1}. {question.question}
                  </h3>
                  <div className="space-y-2">
                    {question.options?.map((option: string, optionIndex: number) => (
                      <label key={optionIndex} className="flex items-center space-x-3 cursor-pointer">
                        <input
                          type="radio"
                          name={`question-${index}`}
                          value={optionIndex}
                          className="text-green-600 focus:ring-green-500"
                        />
                        <span className="text-gray-700">{option}</span>
                      </label>
                    ))}
                  </div>
                  {question.explanation && (
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-800">
                        <strong>Explanation:</strong> {question.explanation}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {userQuota && userQuota.plan_type === 'free' && (
        <div className="mt-8 text-center text-red-500 text-sm">
          Quiz is available for paid plans only. Upgrade to access quizzes!
        </div>
      )}

      {/* Start Over Button */}
      <div className="text-center">
        <button
          onClick={onStartOver}
          className="px-8 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          Start Over
        </button>
      </div>
    </div>
  );
};
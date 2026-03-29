/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useRef, useEffect } from 'react';
import { GoogleGenAI, ThinkingLevel, Type } from "@google/genai";
import { 
  PenTool, 
  Eraser, 
  CheckCircle2, 
  Copy, 
  Loader2, 
  Sparkles, 
  ChevronRight,
  AlertCircle,
  FileText,
  RefreshCw,
  Upload,
  FileUp,
  X,
  Download,
  FileDown,
  FileJson
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import * as mammoth from 'mammoth';
import * as pdfjsLib from 'pdfjs-dist';
import * as diff from 'diff';
import { Document, Packer, Paragraph, TextRun } from 'docx';
import { saveAs } from 'file-saver';

// Set up PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

// Initialize Gemini API
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const STEPS = [
  { id: 1, title: "AI Meta-text Removal", desc: "Xóa bỏ lời thoại AI cũ, chỉ giữ lại mạch truyện." },
  { id: 2, title: "Punctuation & Header Cleanup", desc: "Xóa ký tự lạ, chuỗi dấu lặp và tiêu đề chương." },
  { id: 3, title: "Platform Safety", desc: "Thay thế từ nhạy cảm để tránh vi phạm chính sách mạng xã hội." },
  { id: 4, title: "Name & Pronoun Consistency", desc: "Chuẩn hóa tên nhân vật theo lần đầu xuất hiện." },
  { id: 5, title: "Western Term Normalization", desc: "Chuyển đổi thuật ngữ phương Tây sang thuần Việt/Hán Việt." },
  { id: 6, title: "Slang & Teencode Normalization", desc: "Chuyển đổi teencode và từ lóng sang tiếng Việt chuẩn." },
  { id: 7, title: "Chinese Translation", desc: "Tự động dịch các đoạn Hán tự (tiếng Trung) sang tiếng Việt." }
];

export default function App() {
  const [inputText, setInputText] = useState('');
  const [customProcess, setCustomProcess] = useState('');
  const [outputText, setOutputText] = useState('');
  const [editingDetails, setEditingDetails] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState<string>('truyen_da_edit');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleProcess = async () => {
    if (!inputText.trim()) return;

    // Check for length limit (e.g., 50,000 characters to ensure strict preservation and quality)
    if (inputText.length > 50000) {
      setError(`Văn bản quá dài (hiện có ${inputText.length.toLocaleString()} ký tự, vượt quá giới hạn 50,000 ký tự). Vui lòng chia nhỏ văn bản để đảm bảo chất lượng biên tập và nguyên tắc bảo toàn.`);
      return;
    }

    setIsProcessing(true);
    setError(null);
    setCurrentStep(1);
    setOutputText('');

    try {
      const customRulesSection = customProcess.trim() 
        ? `\n[QUY TẮC TÙY CHỈNH - ƯU TIÊN CAO NHẤT]\nNgười dùng đã cung cấp các quy tắc riêng sau đây. Bạn PHẢI ưu tiên thực hiện các quy tắc này TRƯỚC và XUYÊN SUỐT quá trình biên tập, ngay cả khi chúng mâu thuẫn với các bước chuẩn hóa mặc định:\n${customProcess}\n`
        : "";

      const systemInstruction = `Bạn là một chuyên gia hậu kiểm và biên tập truyện ngôn tình Trung - Việt (Expert Fiction Editor). 
Nhiệm vụ duy nhất là làm sạch và chuẩn hóa văn bản thô theo QUY TRÌNH BIÊN TẬP CHUYÊN SÂU.
${customRulesSection}
LƯU Ý QUAN TRỌNG: Các ví dụ (samples) trong mỗi bước chỉ mang tính chất minh họa để xác định vùng/nhóm đối tượng. Bạn cần CHỦ ĐỘNG PHÂN LẬP và MỞ RỘNG PHẠM VI đối tượng cần edit dựa trên khái niệm đã hiểu từ các mẫu đó.

QUY TRÌNH 7 BƯỚC THỰC THI (STRICT PROTOCOL):

STEP 1: AI Meta-text Removal
- Xóa bỏ tất cả lời thoại của AI cũ (VD: "Bạn muốn dịch tiếp không?", "Dưới đây là...", "Chương tiếp theo là...").
- CHỦ ĐỘNG nhận diện và xóa mọi câu từ mang tính chất "hệ thống", "trò chuyện của AI", hoặc "chỉ dẫn dịch thuật" không thuộc mạch truyện.

STEP 2: Punctuation & Header Cleanup
- Xóa các ký tự lạ: ‘ “ ”. Xóa chuỗi dấu lặp: ???, !!!, ..., --- (thay bằng đơn dấu . ! ? tương ứng).
- Xóa tiêu đề chương dạng: "Chương X", "Chapter X", "Chương XXX: tiêu đề". 
- CHỦ ĐỘNG làm sạch mọi định dạng tiêu đề hoặc ký hiệu phân tách chương tương tự để chỉ để lại nội dung truyện thuần túy.

STEP 3: Platform Safety (YouTube/TikTok Policy)
- CHỦ ĐỘNG tìm kiếm và thay thế TẤT CẢ các từ ngữ nhạy cảm, bạo lực, tình dục, hoặc vi phạm chính sách mạng xã hội sang cách diễn đạt trung tính, ẩn dụ.
- Các mẫu (samples) định hướng:
  + Nhóm tự sát: Tự tử -> Tự tận, quyên sinh...
  + Nhóm mại dâm: Bán dâm -> Bán hoa, tiếp khách...
  * Nhóm chửi thề/xúc phạm: (đm, đĩ, súc vật...) -> ĐM.
  + Nhóm chất cấm: Ma túy, thuốc phiện -> Chất cấm, bột trắng...
  + Nhóm pháp luật: Đi tù, bắt giữ -> Đi tò, vào trại, bị quản chế...
  + Nhóm xâm hại: Hiếp dâm, cưỡng hiếp -> Cưỡng đoạt, làm nhục...
- Mục tiêu: Văn bản sạch hoàn toàn, không bị quét vi phạm nhưng vẫn giữ được ý nghĩa cốt truyện.

STEP 4: Name & Pronoun Consistency
- CHUẨN HÓA TÊN RIÊNG: Sử dụng chính xác cái tên đã có sẵn ở lần xuất hiện ĐẦU TIÊN trong văn bản, sau đó áp dụng đồng nhất cho tất cả các lần xuất hiện bị sai lệch về sau. TUYỆT ĐỐI KHÔNG tự ý chỉnh sửa tên ở lần xuất hiện đầu tiên theo bất kỳ logic nào khác (kể cả Hán Việt).
- Giữ nhất quán xưng hô theo cặp (Anh-Em, Ta-Ngươi, Thúc-Cháu, Trẫm-Khanh...) từ đầu đến cuối. 
- CHỦ ĐỘNG phân tích ngữ cảnh để chọn cặp xưng hô phù hợp nhất và áp dụng đồng nhất cho toàn bộ đoạn văn.

STEP 5: Western Term Normalization
- CHỦ ĐỘNG nhận diện và chuyển đổi TẤT CẢ các thuật ngữ tiếng Anh/phương Tây sang thuần Việt hoặc Hán Việt phù hợp với bối cảnh truyện ngôn tình.
- Các mẫu (samples) định hướng:
  + Studio -> Căn hộ/Phòng làm việc; Suite -> Âu phục; Sofa -> Ghế nghỉ/Trường kỷ; Corporate -> Tập đoàn; Tracking -> Truy vết...
  + Ngoại lệ: Bluetooth (giữ nguyên).

STEP 6: Slang & Teencode Normalization
- CHỦ ĐỘNG nhận diện và chuyển đổi các từ không đúng chuẩn ngữ pháp, "teencode", hoặc pha trộn Việt-Anh (VD: haiz, êi, iem, hichic, grừ...) sang từ đúng chuẩn ngữ pháp tiếng Việt gần sát nhất có thể.

STEP 7: Chinese Translation
- CHỦ ĐỘNG nhận diện bất kỳ đoạn văn bản, từ ngữ hoặc ký tự tiếng Trung (Hán tự) nào xuất hiện trong văn bản và dịch chúng sang tiếng Việt một cách mượt mà, phù hợp với ngữ cảnh truyện.

OUTPUT REQUIREMENTS:
- Trả về kết quả dưới dạng JSON object với 2 trường:
  1. "editedText": Văn bản truyện sạch sau quá trình thực hiện 7 steps.
  2. "editingDetails": Tóm tắt chi tiết các thay đổi đã thực hiện (VD: Đã chuẩn hóa X tên nhân vật, xóa Y tiêu đề chương, dịch Z đoạn Hán tự...).
- Tuyệt đối tuân thủ NGUYÊN TẮC BẢO TOÀN VĂN BẢN (STRICT PRESERVATION):
  1. TUYỆT ĐỐI KHÔNG tóm tắt. Số lượng câu trong "editedText" phải tương đương với Input.
  2. Nếu phát hiện văn bản quá dài, vượt khả năng xử lý, hãy thông báo lỗi.`;

      const response = await ai.models.generateContent({
        model: "gemini-3.1-pro-preview",
        contents: inputText,
        config: {
          systemInstruction,
          thinkingConfig: { thinkingLevel: ThinkingLevel.HIGH },
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              editedText: { type: Type.STRING },
              editingDetails: { type: Type.STRING }
            },
            required: ["editedText", "editingDetails"]
          }
        },
      });

      const data = JSON.parse(response.text);
      const result = data.editedText || '';
      const aiSummary = data.editingDetails || '';

      // Calculate statistics using diff
      const diffResults = diff.diffWords(inputText, result);
      let editCount = 0;
      let deleteCount = 0;

      diffResults.forEach(part => {
        if (part.added) editCount++;
        if (part.removed) deleteCount++;
      });

      const originalChars = inputText.length;
      const originalWords = inputText.trim().split(/\s+/).filter(w => w.length > 0).length;
      const editedChars = result.length;
      const editedWords = result.trim().split(/\s+/).filter(w => w.length > 0).length;

      const statsLog = `[BÁO CÁO SO SÁNH ĐỘ DÀI]
- Văn bản gốc: ${originalChars.toLocaleString()} ký tự | ${originalWords.toLocaleString()} từ
- Văn bản đã edit: ${editedChars.toLocaleString()} ký tự | ${editedWords.toLocaleString()} từ
- Chênh lệch: ${(editedChars - originalChars).toLocaleString()} ký tự | ${(editedWords - originalWords).toLocaleString()} từ

[THỐNG KÊ CHI TIẾT BIÊN TẬP]
- Tổng số lượt chỉnh sửa/thay thế: ${editCount} vị trí (Highlight vàng)
- Tổng số lượt xóa bỏ hoàn toàn: ${deleteCount} vị trí (Highlight đỏ)

[TÓM TẮT NỘI DUNG TỪ AI]
${aiSummary}`;
      
      // Simulate step progression for UX
      for (let i = 2; i <= 6; i++) {
        await new Promise(r => setTimeout(r, 800));
        setCurrentStep(i);
      }
      
      setOutputText(result);
      setEditingDetails(statsLog);
      setCurrentStep(7); // Finished
    } catch (err: any) {
      console.error("Processing error:", err);
      setError(err.message || "Đã xảy ra lỗi trong quá trình biên tập.");
      setCurrentStep(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const extractTextFromFile = async (file: File) => {
    setIsExtracting(true);
    setError(null);
    // Extract base filename without extension
    const baseName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
    setFileName(baseName + '_edited');
    
    try {
      const fileType = file.name.split('.').pop()?.toLowerCase();
      let text = '';

      if (fileType === 'txt') {
        text = await file.text();
      } else if (fileType === 'docx') {
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        text = result.value;
      } else if (fileType === 'pdf') {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        let fullText = '';
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const content = await page.getTextContent();
          const pageText = content.items.map((item: any) => item.str).join(' ');
          fullText += pageText + '\n';
        }
        text = fullText;
      } else if (fileType === 'doc') {
        throw new Error("Định dạng .doc (cũ) không được hỗ trợ trực tiếp trong trình duyệt. Vui lòng chuyển sang .docx hoặc .txt.");
      } else {
        throw new Error("Định dạng tệp không được hỗ trợ. Vui lòng sử dụng .txt, .docx, hoặc .pdf.");
      }

      if (!text.trim()) {
        throw new Error("Không tìm thấy nội dung văn bản trong tệp này.");
      }

      setInputText(text);
    } catch (err: any) {
      console.error("Extraction error:", err);
      setError(err.message || "Không thể trích xuất văn bản từ tệp.");
    } finally {
      setIsExtracting(false);
    }
  };

  const exportToDocx = async () => {
    if (!outputText) return;
    setIsExporting(true);
    try {
      // Split text by double newlines to create paragraphs
      const paragraphs = outputText.split(/\n\n+/).map(p => {
        return new Paragraph({
          children: [new TextRun(p.trim())],
          spacing: { after: 200 }
        });
      });

      const doc = new Document({
        sections: [{
          properties: {},
          children: paragraphs,
        }],
      });

      const blob = await Packer.toBlob(doc);
      saveAs(blob, `${fileName}.docx`);
    } catch (err) {
      console.error("Export DOCX error:", err);
      setError("Không thể xuất file DOCX.");
    } finally {
      setIsExporting(false);
    }
  };

  const exportToTxt = () => {
    if (!outputText) return;
    const blob = new Blob([outputText], { type: 'text/plain;charset=utf-8' });
    saveAs(blob, `${fileName}.txt`);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      extractTextFromFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      extractTextFromFile(e.target.files[0]);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(outputText);
  };

  const reset = () => {
    setInputText('');
    setCustomProcess('');
    setOutputText('');
    setEditingDetails('');
    setCurrentStep(0);
    setError(null);
    setFileName('truyen_da_edit');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen pink-gradient selection:bg-pink-200">
      {/* Header */}
      <header className="border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-300 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[57.6px] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-pink-500 rounded-lg flex items-center justify-center text-white shadow-sm">
              <PenTool size={18} />
            </div>
            <h1 className="font-serif text-lg sm:text-xl font-bold tracking-tight text-gray-900">
              Fiction Editor <span className="text-pink-600">Pro</span>
            </h1>
          </div>
          <div className="flex items-center gap-3 sm:gap-4 text-xs sm:text-sm font-medium text-gray-500">
            <span className="hidden xs:inline">Vietnamese Edition</span>
            <div className="h-4 w-px bg-pink-100 hidden xs:block" />
            <button 
              onClick={reset}
              className="flex items-center gap-1 hover:text-pink-600 transition-colors"
            >
              <RefreshCw size={14} /> <span className="hidden sm:inline">Làm mới</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-2 sm:gap-3">
          
          {/* Left Column: Input & Steps */}
          <div className="lg:col-span-3 space-y-6">
            <section className="bg-white/80 rounded-2xl border border-pink-100 editorial-shadow overflow-hidden backdrop-blur-sm">
              <div className="p-4 border-b border-pink-50 flex items-center justify-between bg-pink-50/30">
                <div className="flex items-center gap-2 text-gray-700 font-medium text-sm">
                  <FileText size={16} className="text-pink-500" />
                  Văn bản thô
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase tracking-widest text-pink-400 font-bold">
                    Input
                  </span>
                </div>
              </div>

              {/* File Upload Area */}
              <div 
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                className={`
                  relative p-6 border-b border-dashed border-pink-100 transition-all
                  ${dragActive ? 'bg-pink-50 border-pink-500' : 'bg-white/50'}
                `}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileChange}
                  accept=".txt,.docx,.pdf"
                  className="hidden"
                />
                <div className="flex flex-col items-center justify-center py-4 text-center">
                  {isExtracting ? (
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 size={24} className="animate-spin text-pink-500" />
                      <p className="text-xs font-medium text-gray-600">Đang trích xuất văn bản...</p>
                    </div>
                  ) : (
                    <>
                      <div className="w-10 h-10 bg-pink-50 rounded-full flex items-center justify-center text-pink-400 mb-2">
                        <Upload size={20} />
                      </div>
                      <p className="text-xs font-medium text-gray-600 mb-1">
                        Kéo thả file hoặc <button onClick={() => fileInputRef.current?.click()} className="text-pink-600 hover:underline font-bold">tải lên</button>
                      </p>
                      <p className="text-[10px] text-gray-400">
                        Hỗ trợ: .txt, .docx, .pdf
                      </p>
                    </>
                  )}
                </div>
              </div>

              <div className="relative">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Dán nội dung truyện hoặc tải file lên..."
                  className="w-full h-[212px] sm:h-[255px] p-1 sm:p-1.5 focus:outline-none resize-none text-gray-700 leading-relaxed font-sans text-[14px] sm:text-[15px] bg-transparent"
                  disabled={isProcessing || isExtracting}
                />
                {inputText.length > 0 && (
                  <div className={`absolute bottom-2 right-4 text-[10px] font-bold px-2 py-1 rounded-md ${inputText.length > 50000 ? 'bg-red-50 text-red-500' : 'text-gray-400'}`}>
                    {inputText.length.toLocaleString()} / 50,000
                  </div>
                )}
              </div>
              <div className="p-4 bg-pink-50/30 border-t border-pink-50 flex justify-end">
                <button
                  onClick={handleProcess}
                  disabled={isProcessing || isExtracting || !inputText.trim()}
                  className={`
                    w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3 rounded-full font-bold text-sm transition-all shadow-sm
                    ${isProcessing || isExtracting || !inputText.trim() 
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                      : 'bg-pink-600 text-white hover:bg-pink-700 hover:shadow-pink-200 hover:shadow-lg active:scale-95'}
                  `}
                >
                  {isProcessing ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      <Sparkles size={18} />
                      Bắt đầu biên tập
                    </>
                  )}
                </button>
              </div>
            </section>

            {/* Custom Process Section */}
            <section className="bg-white/80 rounded-2xl border border-pink-100 editorial-shadow overflow-hidden backdrop-blur-sm">
              <div className="p-4 border-b border-pink-50 flex items-center justify-between bg-pink-50/30">
                <div className="flex items-center gap-2 text-gray-700 font-medium text-sm">
                  <PenTool size={16} className="text-pink-500" />
                  Quy trình tùy chỉnh
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase tracking-widest text-pink-400 font-bold">
                    Custom Rules
                  </span>
                </div>
              </div>
              <div className="relative">
                <textarea
                  value={customProcess}
                  onChange={(e) => setCustomProcess(e.target.value)}
                  placeholder="Nhập các quy tắc biên tập riêng của bạn (VD: Thay đổi cách xưng hô cụ thể, giữ nguyên một số từ lóng...)"
                  className="w-full h-[120px] p-4 sm:p-6 focus:outline-none resize-none text-gray-700 leading-relaxed font-sans text-[13px] bg-transparent"
                  disabled={isProcessing || isExtracting}
                />
              </div>
            </section>

            {/* Steps Progress */}
            <section className="bg-white/80 rounded-2xl border border-pink-100 editorial-shadow p-3 sm:p-4 backdrop-blur-sm max-h-[260px] overflow-y-auto">
              <h3 className="text-xs font-bold uppercase tracking-widest text-pink-400 mb-3 flex items-center gap-2">
                <RefreshCw size={12} /> Quy trình thực thi
              </h3>
              <div className="space-y-2">
                {STEPS.map((step) => {
                  const isActive = currentStep === step.id;
                  const isCompleted = currentStep > step.id;
                  
                  return (
                    <div 
                      key={step.id}
                      className={`
                        flex items-start gap-3 p-2 rounded-xl transition-all duration-300
                        ${isActive ? 'bg-pink-50 ring-1 ring-pink-100' : ''}
                        ${isCompleted ? 'opacity-60' : ''}
                      `}
                    >
                      <div className={`
                        w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] font-bold
                        ${isCompleted ? 'bg-green-500 text-white' : isActive ? 'bg-pink-500 text-white' : 'bg-pink-50 text-pink-300'}
                      `}>
                        {isCompleted ? <CheckCircle2 size={14} /> : step.id}
                      </div>
                      <div>
                        <h4 className={`text-[10px] font-semibold ${isActive ? 'text-pink-700' : 'text-gray-700'}`}>
                          {step.title}
                        </h4>
                        <p className="text-[8.5px] text-gray-500 mt-0.5 leading-snug">
                          {step.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>

          {/* Right Column: Output */}
          <div className="lg:col-span-9">
            <section className="bg-white/90 rounded-2xl border border-pink-100 editorial-shadow flex flex-col overflow-hidden backdrop-blur-sm">
              <div className="p-4 border-b border-pink-50 flex items-center justify-between bg-pink-50/30">
                <div className="flex items-center gap-2 text-gray-700 font-medium text-sm">
                  <Eraser size={16} className="text-pink-500" />
                  Văn bản đã biên tập
                </div>
                <div className="flex items-center gap-2">
                  {outputText && (
                    <button
                      onClick={copyToClipboard}
                      className="p-1.5 text-gray-500 hover:text-pink-600 hover:bg-pink-50 rounded-md transition-all"
                      title="Sao chép"
                    >
                      <Copy size={16} />
                    </button>
                  )}
                  <span className="text-[10px] uppercase tracking-widest text-pink-400 font-bold">
                    Output
                  </span>
                </div>
              </div>

              <div className="h-[541px] sm:h-[648px] p-1 sm:p-2 overflow-y-auto font-serif text-base sm:text-lg leading-[1.8] text-gray-900">
                <AnimatePresence mode="wait">
                  {error ? (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex flex-col items-center justify-center h-full text-center space-y-3"
                    >
                      <AlertCircle size={48} className="text-red-400" />
                      <p className="text-red-500 font-sans text-sm">{error}</p>
                      <button 
                        onClick={() => setError(null)}
                        className="text-sm font-sans text-pink-600 underline underline-offset-4"
                      >
                        Đóng thông báo
                      </button>
                    </motion.div>
                  ) : isProcessing ? (
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex flex-col items-center justify-center h-full space-y-6"
                    >
                      <div className="relative">
                        <div className="w-16 h-16 border-4 border-pink-50 border-t-pink-500 rounded-full animate-spin" />
                        <Sparkles className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-pink-500 animate-pulse" size={24} />
                      </div>
                      <div className="text-center space-y-2">
                        <p className="text-sm font-sans font-medium text-gray-700">
                          Đang áp dụng trí tuệ nhân tạo chuyên sâu...
                        </p>
                        <p className="text-xs font-sans text-gray-400">
                          Quá trình này có thể mất vài giây để đảm bảo chất lượng văn phong.
                        </p>
                      </div>
                    </motion.div>
                  ) : outputText ? (
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="whitespace-pre-wrap font-serif leading-[1.8]"
                    >
                      {diff.diffWords(inputText, outputText).map((part, index, array) => {
                        if (part.added) {
                          return (
                            <span key={index} className="bg-yellow-200 px-0.5 rounded-sm">
                              {part.value}
                            </span>
                          );
                        }
                        if (part.removed) {
                          // Check if this is a replacement (followed by an addition)
                          const nextPart = array[index + 1];
                          if (nextPart && nextPart.added) {
                            return null;
                          }
                          // Pure deletion: show a highlighted space
                          return (
                            <span key={index} className="bg-red-200 px-1 rounded-sm mx-0.5 inline-block min-w-[0.5em] h-[1.2em] align-middle" title="Đã xóa nội dung">
                            </span>
                          );
                        }
                        return <span key={index}>{part.value}</span>;
                      })}
                    </motion.div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-20">
                      <PenTool size={64} className="text-pink-500" />
                      <p className="font-sans text-sm italic">
                        Kết quả biên tập sẽ hiển thị tại đây...
                      </p>
                    </div>
                  )}
                </AnimatePresence>
              </div>

              {outputText && (
                <div className="p-4 bg-pink-50/50 border-t border-pink-100 flex flex-col space-y-4">
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2 text-pink-600 text-xs font-bold uppercase tracking-wider">
                      <CheckCircle2 size={14} />
                      Hoàn tất biên tập
                    </div>
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <div className="relative flex-1 sm:flex-none">
                        <input
                          type="text"
                          value={fileName}
                          onChange={(e) => setFileName(e.target.value)}
                          placeholder="Tên file..."
                          className="w-full sm:w-48 px-3 py-2 bg-white border border-pink-100 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-pink-500"
                        />
                      </div>
                      <button
                        onClick={exportToTxt}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-white border border-pink-100 rounded-lg text-xs font-semibold text-gray-600 hover:bg-pink-50 transition-all"
                        title="Tải về file .txt"
                      >
                        <FileText size={14} />
                        .TXT
                      </button>
                      <button
                        onClick={exportToDocx}
                        disabled={isExporting}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-pink-600 rounded-lg text-xs font-semibold text-white hover:bg-pink-700 transition-all shadow-sm"
                        title="Tải về file .docx"
                      >
                        {isExporting ? <Loader2 size={14} className="animate-spin" /> : <FileDown size={14} />}
                        .DOCX
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </section>

            {/* Editing Details Section */}
            <section className="bg-white/90 rounded-2xl border border-pink-100 editorial-shadow flex flex-col overflow-hidden backdrop-blur-sm mt-6">
              <div className="p-4 border-b border-pink-50 flex items-center justify-between bg-pink-50/30">
                <div className="flex items-center gap-2 text-gray-700 font-medium text-sm">
                  <Sparkles size={16} className="text-pink-500" />
                  Chi tiết biên tập
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase tracking-widest text-pink-400 font-bold">
                    Details
                  </span>
                </div>
              </div>
              <div className="h-[268px] p-5 sm:p-8 overflow-y-auto font-sans text-sm leading-relaxed text-gray-600 bg-white/50">
                {isProcessing ? (
                  <div className="flex flex-col items-center justify-center h-full space-y-4 opacity-40">
                    <Loader2 size={24} className="animate-spin text-pink-500" />
                    <p className="text-xs italic">Đang tổng hợp chi tiết...</p>
                  </div>
                ) : editingDetails ? (
                  <div className="whitespace-pre-wrap">
                    {editingDetails}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-20">
                    <FileJson size={48} className="text-pink-500" />
                    <p className="text-xs italic">Chi tiết các thay đổi sẽ hiển thị tại đây...</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-4 sm:px-6 py-12 border-t border-pink-100 mt-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="space-y-4">
            <div className="flex items-center gap-2 opacity-50">
              <PenTool size={16} className="text-pink-600" />
              <span className="font-serif font-bold">Fiction Editor Pro</span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Công cụ hỗ trợ biên tập viên truyện ngôn tình chuyên nghiệp. Tối ưu hóa văn phong Trung - Việt bằng AI thế hệ mới.
            </p>
          </div>
          <div className="space-y-4">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-pink-400">Cam kết chất lượng</h4>
            <ul className="text-xs text-gray-500 space-y-2">
              <li className="flex items-center gap-2"><ChevronRight size={12} className="text-pink-400" /> Không tóm tắt nội dung</li>
              <li className="flex items-center gap-2"><ChevronRight size={12} className="text-pink-400" /> Không thêm lời bình cá nhân</li>
              <li className="flex items-center gap-2"><ChevronRight size={12} className="text-pink-400" /> Giữ nguyên 100% tình tiết</li>
            </ul>
          </div>
          <div className="space-y-4">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-pink-400">Công nghệ</h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              Sử dụng mô hình Gemini 3.1 Pro với chế độ High Thinking để xử lý ngữ nghĩa phức tạp và sắc thái ngôn từ lãng mạn.
            </p>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-pink-50 text-center">
          <p className="text-[10px] text-pink-300 uppercase tracking-[0.2em]">
            &copy; 2026 Professional Fiction Post-Processor
          </p>
        </div>
      </footer>
    </div>
  );
}

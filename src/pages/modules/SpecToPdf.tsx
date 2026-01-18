/**
 * Spec Source to PDF Converter
 * File: src/pages/modules/SpecToPdf.tsx
 * 
 * Accepts a ZIP containing spec_source folder(s) and generates organized PDF
 */
import { useState } from "react";
import { FileUpload } from "@/components/FileUpload";
import { LogViewer } from "@/components/LogViewer";
import { Button } from "@/components/ui/button";
import { Download, FileArchive } from "lucide-react";
import { toast } from "sonner";

const API_BASE_URL = "http://localhost:5000/api";

export default function SpecToPdf() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<Array<{ timestamp: string; message: string; type: "info" | "success" | "error" | "warning" }>>([]);
  const [outputReady, setOutputReady] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const addLog = (message: string, type: "info" | "success" | "error" | "warning" = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  const handleFileSelect = async (file: File) => {
    // Validate ZIP file
    if (!file.name.toLowerCase().endsWith('.zip')) {
      toast.error("Please upload a ZIP file");
      return;
    }

    setIsProcessing(true);
    setProgress(0);
    setOutputReady(false);
    setLogs([]);
    setSessionId(null);

    addLog(`Selected: ${file.name}`, "info");
    addLog("Starting Spec Source to PDF conversion...", "info");

    try {
      const formData = new FormData();
      formData.append('file', file);

      setProgress(10);
      addLog("Uploading ZIP file to server...", "info");

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 minutes

      const response = await fetch(`${API_BASE_URL}/spec-to-pdf/convert`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      setProgress(30);
      addLog("ZIP uploaded. Extracting contents...", "info");

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Conversion failed');
      }

      const result = await response.json();

      if (result.success) {
        setProgress(50);
        addLog(`Found ${result.ip_count} spec_source folder(s)`, "info");
        
        setProgress(70);
        addLog("Processing DITA topics and REGS files...", "info");
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setProgress(85);
        addLog("Generating organized PDF...", "info");
        
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        setProgress(100);
        
        addLog("PDF generation complete!", "success");
        if (result.stats) {
          addLog(`Total DITA topics processed: ${result.stats.total_topics || 0}`, "success");
          addLog(`Total REGS files processed: ${result.stats.total_regs || 0}`, "success");
        }
        
        setSessionId(result.session_id);
        setOutputReady(true);
        toast.success("PDF generated successfully!");
      } else {
        throw new Error(result.error || 'Conversion failed');
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        addLog("Request timeout - this may happen with large files", "error");
        toast.error("Request timeout. Please try with a smaller ZIP file.");
      } else {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        addLog(`Error: ${errorMessage}`, "error");
        toast.error(`Generation failed: ${errorMessage}`);
      }
      setProgress(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadWithRetry = async (url: string, filename: string, maxRetries = 3) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        addLog(`Download attempt ${attempt}/${maxRetries}...`, "info");
        
        const response = await fetch(url);
        
        if (!response.ok) {
          if (attempt < maxRetries) {
            addLog(`Attempt ${attempt} failed, retrying...`, "warning");
            await new Promise(resolve => setTimeout(resolve, 2000));
            continue;
          }
          throw new Error('Download failed');
        }

        const blob = await response.blob();
        
        if (blob.size === 0) {
          throw new Error('Downloaded file is empty');
        }

        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);

        addLog(`${filename} download started successfully!`, "success");
        toast.success(`${filename} download started`);
        return true;
        
      } catch (error) {
        if (attempt === maxRetries) {
          throw error;
        }
        addLog(`Attempt ${attempt} failed, retrying in 2 seconds...`, "warning");
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    return false;
  };

  const handleDownloadPdf = async () => {
    if (!sessionId) {
      toast.error("No session found");
      return;
    }

    try {
      addLog("Preparing PDF download...", "info");
      await downloadWithRetry(
        `${API_BASE_URL}/spec-to-pdf/download-pdf/${sessionId}`,
        'organized_documentation.pdf'
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';
      addLog(`Error: ${errorMessage}`, "error");
      toast.error(errorMessage);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Spec Source → PDF</h1>
        <p className="text-muted-foreground">
          Convert existing spec_source folders to organized PDF documentation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <FileUpload
            accept=".zip"
            onFileSelect={handleFileSelect}
            isProcessing={isProcessing}
            progress={progress}
            multiple={false}
          />

          {outputReady && (
            <div className="space-y-3">
              <Button
                onClick={handleDownloadPdf}
                className="w-full cyber-glow-intense"
                size="lg"
              >
                <Download className="mr-2 h-4 w-4" />
                Download PDF
              </Button>

              <div className="p-3 bg-secondary/50 rounded-lg border">
                <p className="text-xs text-muted-foreground">
                  ✅ PDF generated from your spec_source files
                </p>
              </div>
            </div>
          )}
        </div>

        <LogViewer logs={logs} />
      </div>

      <div className="mt-8 p-6 bg-secondary/50 rounded-lg border">
        <h3 className="text-lg font-semibold mb-3">How to use:</h3>
        <ul className="space-y-2 text-sm">
          <li className="flex items-start gap-2">
            <span className="text-primary">1.</span>
            <span>Upload a ZIP file containing your <strong>spec_source</strong> folder(s)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">2.</span>
            <span>The ZIP should contain folders with: <code className="text-xs bg-secondary px-1 py-0.5 rounded">dita_map/</code>, <code className="text-xs bg-secondary px-1 py-0.5 rounded">dita_topics/</code>, <code className="text-xs bg-secondary px-1 py-0.5 rounded">images/</code>, <code className="text-xs bg-secondary px-1 py-0.5 rounded">regs/</code></span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">3.</span>
            <span>The system will process all DITA topics, register specifications, and images to generate a comprehensive PDF</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">4.</span>
            <span>Download the organized PDF documentation</span>
          </li>
        </ul>
        
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <p className="text-xs text-blue-400">
            💡 <strong>Tip:</strong> You can use the spec_outputs.zip from Multi-IP Doc Generator directly as input
          </p>
        </div>
      </div>
    </div>
  );
}
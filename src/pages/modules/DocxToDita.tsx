import { useState } from "react";
import { FileUpload } from "@/components/FileUpload";
import { LogViewer } from "@/components/LogViewer";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { toast } from "sonner";

// ✅ FIXED: Removed /convert from base URL
const API_BASE_URL = "http://localhost:5000/api";

export default function DocxToDita() {
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
    setIsProcessing(true);
    setProgress(0);
    setOutputReady(false);
    setLogs([]);
    setSessionId(null);

    addLog("File selected: " + file.name, "info");
    addLog("Starting DocX to DITA conversion...", "info");

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_title', file.name.replace(/\.(docx|doc)$/, ''));

      // Upload and convert
      setProgress(20);
      addLog("Uploading file to server...", "info");

      // ✅ FIXED: Correct endpoint path
      const response = await fetch(`${API_BASE_URL}/convert/`, {
        method: 'POST',
        body: formData,
      });

      setProgress(40);
      addLog("File uploaded. Processing...", "info");

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Conversion failed');
      }

      const result = await response.json();

      if (result.success) {
        setProgress(60);
        addLog("Parsing Word document...", "info");
        
        await new Promise(resolve => setTimeout(resolve, 500));
        setProgress(75);
        addLog("Extracting styles and content...", "info");
        
        await new Promise(resolve => setTimeout(resolve, 500));
        setProgress(90);
        addLog("Generating DITA map...", "info");
        
        await new Promise(resolve => setTimeout(resolve, 500));
        setProgress(100);
        
        addLog("Conversion complete!", "success");
        addLog(`Generated ${result.stats.topics_count} topics, ${result.stats.tables_count} tables, ${result.stats.media_count} media files`, "success");
        
        setSessionId(result.session_id);
        setOutputReady(true);
        toast.success("DocX to DITA conversion completed!");
      } else {
        throw new Error(result.error || 'Conversion failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      addLog(`Error: ${errorMessage}`, "error");
      toast.error(`Conversion failed: ${errorMessage}`);
      setProgress(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!sessionId) {
      toast.error("No session found");
      return;
    }

    try {
      addLog("Preparing download...", "info");
      
      // ✅ FIXED: Correct endpoint path
      const response = await fetch(`${API_BASE_URL}/convert/download/${sessionId}`);
      
      if (!response.ok) {
        throw new Error('Download failed');
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'dita-package.zip';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      addLog("Download started successfully!", "success");
      toast.success("Download started");

      // Cleanup session after download
      // ✅ FIXED: Correct endpoint path
      // await fetch(`${API_BASE_URL}/convert/cleanup/${sessionId}`, {
      //   method: 'DELETE'
      // });
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';
      addLog(`Error: ${errorMessage}`, "error");
      toast.error(errorMessage);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">DocX → DITA Map Converter</h1>
        <p className="text-muted-foreground">
          Transform Word documents to DITA Map format with image to SVG conversion
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <FileUpload
            accept=".docx,.doc"
            onFileSelect={handleFileSelect}
            isProcessing={isProcessing}
            progress={progress}
          />

          {outputReady && (
            <Button
              onClick={handleDownload}
              className="w-full cyber-glow-intense"
              size="lg"
            >
              <Download className="mr-2 h-4 w-4" />
              Download DITA Map
            </Button>
          )}
        </div>

        <LogViewer logs={logs} />
      </div>
    </div>
  );
}
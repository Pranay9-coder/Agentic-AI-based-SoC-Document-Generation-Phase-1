import { useState } from "react";
import { FileUpload } from "@/components/FileUpload";
import { LogViewer } from "@/components/LogViewer";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { toast } from "sonner";

const API_BASE_URL = "http://localhost:5000";

export default function AnyToRegs() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<Array<{ timestamp: string; message: string; type: "info" | "success" | "error" | "warning" }>>([]);
  const [outputReady, setOutputReady] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [outputFilename, setOutputFilename] = useState<string | null>(null);

  const addLog = (message: string, type: "info" | "success" | "error" | "warning" = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  const handleFileSelect = async (file: File) => {
    setIsProcessing(true);
    setProgress(0);
    setOutputReady(false);
    setDownloadUrl(null);
    setOutputFilename(null);
    setLogs([]);

    addLog(`File selected: ${file.name}`, "info");
    addLog("Starting conversion to .REGS format...", "info");

    try {
      // Step 1: Upload file
      setProgress(25);
      addLog("Uploading file...", "info");

      const formData = new FormData();
      formData.append("file", file);

      // Step 2: Send conversion request
      setProgress(50);
      addLog("Extracting register specifications...", "info");

      const response = await fetch(`${API_BASE_URL}/api/any-to-regs/convert`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || "Conversion failed");
      }

      // Step 3: Conversion complete
      setProgress(75);
      addLog(`Successfully extracted ${result.register_count} register(s)`, "success");
      addLog("Generating .REGS file...", "info");

      // Simulate .REGS generation delay
      await new Promise(resolve => setTimeout(resolve, 500));

      setProgress(100);
      addLog(".REGS file generation complete!", "success");
      addLog(`Output file: ${result.output_filename}`, "info");

      // Set download information
      setDownloadUrl(`${API_BASE_URL}${result.download_url}`);
      setOutputFilename(result.output_filename);
      setOutputReady(true);
      
      toast.success("Conversion to .REGS completed!");

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      addLog(`Error: ${errorMessage}`, "error");
      toast.error(`Conversion failed: ${errorMessage}`);
      setProgress(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!downloadUrl) {
      toast.error("No file available for download");
      return;
    }

    try {
      addLog("Downloading .REGS file...", "info");

      // Fetch the file
      const response = await fetch(downloadUrl);
      
      if (!response.ok) {
        throw new Error("Download failed");
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = outputFilename || 'output.regs';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      addLog("Download complete!", "success");
      toast.success(".REGS file downloaded successfully!");

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Download failed";
      addLog(`Error: ${errorMessage}`, "error");
      toast.error(errorMessage);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">PDF/DocX/Excel → .REGS Converter</h1>
        <p className="text-muted-foreground">
          Convert PDF, Word, or Excel documents to .REGS register specification format
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <FileUpload
            accept=".pdf,.docx,.doc,.xlsx,.xls"
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
              Download .REGS File
            </Button>
          )}
        </div>

        <LogViewer logs={logs} />
      </div>
    </div>
  );
}
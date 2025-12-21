/**
 * Updated Multi-IP Documentation Generator with Spec Source Editor
 * File: src/pages/modules/MultiIpDocGen.tsx
 */
import { useState } from "react";
import { FileUpload } from "@/components/FileUpload";
import { LogViewer } from "@/components/LogViewer";
import { SpecSourceEditor } from "@/components/SpecSourceEditor";
import { Button } from "@/components/ui/button";
import { Download, FileArchive, Edit, FileText } from "lucide-react";
import { toast } from "sonner";

const API_BASE_URL = "http://localhost:5000/api";

export default function MultiIpDocGen() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<Array<{ timestamp: string; message: string; type: "info" | "success" | "error" | "warning" }>>([]);
  const [outputReady, setOutputReady] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [ipCount, setIpCount] = useState(0);
  const [editorOpen, setEditorOpen] = useState(false);

  const addLog = (message: string, type: "info" | "success" | "error" | "warning" = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  const handleFilesSelect = async (files: File[]) => {
    if (files.length === 0) {
      toast.error("No files selected");
      return;
    }

    setIsProcessing(true);
    setProgress(0);
    setOutputReady(false);
    setLogs([]);
    setSessionId(null);
    setIpCount(files.length);

    addLog(`Selected ${files.length} IP document(s)`, "info");
    addLog("Starting Multi-IP Documentation Generation...", "info");

    try {
      // Create FormData with multiple files
      const formData = new FormData();
      files.forEach((file, index) => {
        formData.append('files', file);
        addLog(`Added: ${file.name}`, "info");
      });

      setProgress(10);
      addLog("Uploading files to server...", "info");

      // Increased timeout for multiple IPs
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

      const response = await fetch(`${API_BASE_URL}/multi-ip/convert`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      setProgress(30);
      addLog("Files uploaded. Processing IPs...", "info");

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Conversion failed');
      }

      const result = await response.json();

      if (result.success) {
        setProgress(50);
        addLog(`Processing ${result.ip_count} IP(s)...`, "info");
        
        // Simulate progress for each IP
        const progressPerIp = 40 / result.ip_count;
        for (let i = 0; i < result.ip_count; i++) {
          await new Promise(resolve => setTimeout(resolve, 500));
          setProgress(50 + ((i + 1) * progressPerIp));
          addLog(`Processed IP ${i + 1}/${result.ip_count}`, "info");
        }
        
        setProgress(95);
        addLog("Finalizing outputs...", "info");
        
        // Wait for files to be fully written (important for multiple IPs)
        await new Promise(resolve => setTimeout(resolve, 2000));
        setProgress(100);
        
        addLog("Multi-IP documentation generation complete!", "success");
        addLog(`Generated spec folders for ${result.ip_count} IP(s)`, "success");
        addLog(`Total DITA topics: ${result.stats.total_topics}`, "success");
        addLog(`Total .REGS files: ${result.stats.total_regs}`, "success");
        
        setSessionId(result.session_id);
        setOutputReady(true);
        toast.success("Multi-IP documentation generated successfully!");
      } else {
        throw new Error(result.error || 'Conversion failed');
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        addLog("Request timeout - this may happen with large files", "error");
        toast.error("Request timeout. Please try with fewer or smaller files.");
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

  const handleDownloadZip = async () => {
    if (!sessionId) {
      toast.error("No session found");
      return;
    }

    try {
      addLog("Preparing ZIP download...", "info");
      await downloadWithRetry(
        `${API_BASE_URL}/multi-ip/download-zip/${sessionId}`,
        'spec_outputs.zip'
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';
      addLog(`Error: ${errorMessage}`, "error");
      toast.error(errorMessage);
    }
  };

  const handleDownloadPdf = async () => {
    if (!sessionId) {
      toast.error("No session found");
      return;
    }

    try {
      addLog("Preparing organized PDF download...", "info");
      await downloadWithRetry(
        `${API_BASE_URL}/multi-ip/download-pdf/${sessionId}`,
        'organized_soc_documentation.pdf'
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';
      addLog(`Error: ${errorMessage}`, "error");
      toast.error(errorMessage);
    }
  };

  const handleOpenEditor = () => {
    if (!sessionId) {
      toast.error("No session found");
      return;
    }
    setEditorOpen(true);
  };

  const handlePdfRegenerated = () => {
    addLog("PDF regenerated from edited spec source", "success");
    toast.success("PDF updated! Download the new version.");
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Multi-IP Documentation Generator</h1>
        <p className="text-muted-foreground">
          Generate comprehensive SOC documentation from multiple IP specification documents
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <FileUpload
            accept=".pdf,.docx,.doc"
            onFileSelect={(file) => handleFilesSelect([file])}
            onMultipleFilesSelect={handleFilesSelect}
            isProcessing={isProcessing}
            progress={progress}
            multiple={true}
          />

          {outputReady && (
            <div className="space-y-3">
              {/* Primary Actions */}
              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={handleDownloadZip}
                  className="cyber-glow-intense"
                  size="lg"
                >
                  <FileArchive className="mr-2 h-4 w-4" />
                  Download ZIP
                </Button>
                
                <Button
                  onClick={handleDownloadPdf}
                  className="cyber-glow-intense"
                  size="lg"
                  variant="secondary"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download PDF
                </Button>
              </div>

              {/* NEW: Edit Spec Source Button */}
              <Button
                onClick={handleOpenEditor}
                className="w-full"
                size="lg"
                variant="outline"
              >
                <Edit className="mr-2 h-4 w-4" />
                Edit Spec Source & Regenerate PDF
              </Button>

              <div className="p-3 bg-secondary/50 rounded-lg border">
                <p className="text-xs text-muted-foreground">
                  💡 Use the editor to modify DITA topics, REGS files, or images, then regenerate an updated PDF
                </p>
              </div>
            </div>
          )}

          {ipCount > 0 && (
            <div className="p-4 bg-secondary rounded-lg">
              <p className="text-sm font-medium">Processing {ipCount} IP document(s)</p>
            </div>
          )}
        </div>

        <LogViewer logs={logs} />
      </div>

      <div className="mt-8 p-6 bg-secondary/50 rounded-lg border">
        <h3 className="text-lg font-semibold mb-3">What this generates:</h3>
        <ul className="space-y-2 text-sm">
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span><strong>Spec Outputs ZIP:</strong> Individual spec_source folders for each IP containing DITA topics, maps, .REGS files, and SVG images</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span><strong>Organized PDF:</strong> Single comprehensive document with all IPs structured as chapters with hierarchical sections</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span><strong>Automatic Detection:</strong> Identifies and converts register tables to .REGS format automatically</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary text-green-500">•</span>
            <span><strong>Editable Spec Source:</strong> Edit generated files and regenerate updated PDFs on-the-fly</span>
          </li>
        </ul>
      </div>

      {/* Spec Source Editor Modal */}
      {sessionId && (
        <SpecSourceEditor
          sessionId={sessionId}
          isOpen={editorOpen}
          onClose={() => setEditorOpen(false)}
          onPdfRegenerated={handlePdfRegenerated}
        />
      )}
    </div>
  );
}
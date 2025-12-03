import { useState } from "react";
import { FileUpload } from "@/components/FileUpload";
import { LogViewer } from "@/components/LogViewer";
import { Button } from "@/components/ui/button";
import { Download, Sparkles, RefreshCw, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function ImageToSvg() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<Array<{ timestamp: string; message: string; type: "info" | "success" | "error" | "warning" }>>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [svgBlob, setSvgBlob] = useState<Blob | null>(null);
  const [svgFilename, setSvgFilename] = useState<string>("");
  const [diagramType, setDiagramType] = useState<string>("auto");
  const [hasError, setHasError] = useState(false);
  const [errorType, setErrorType] = useState<"quota" | "network" | "general" | null>(null);

  const addLog = (message: string, type: "info" | "success" | "error" | "warning" = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setSvgBlob(null);
    setLogs([]);
    setHasError(false);
    setErrorType(null);
    addLog(`File selected: ${file.name}`, "info");
    addLog(`File size: ${(file.size / 1024).toFixed(2)} KB`, "info");
  };

  const handleConvert = async () => {
    if (!selectedFile) {
      toast.error("Please select a file first");
      return;
    }

    setIsProcessing(true);
    setProgress(0);
    setSvgBlob(null);
    setHasError(false);
    setErrorType(null);

    addLog("Starting Image to SVG conversion...", "info");
    setProgress(10);

    try {
      // Prepare form data
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("diagram_type", diagramType);

      addLog(`Diagram type: ${diagramType === 'auto' ? 'Auto-detect' : diagramType}`, "info");
      setProgress(25);

      addLog("Uploading image to server...", "info");
      setProgress(40);

      // Call API
      const response = await fetch("http://localhost:5000/api/convert/image-to-svg", {
        method: "POST",
        body: formData,
      });

      setProgress(70);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Conversion failed");
      }

      addLog("Processing with AI...", "info");
      setProgress(85);

      // Get blob from response
      const blob = await response.blob();
      const filename = response.headers.get("content-disposition")
        ?.split("filename=")[1]
        ?.replace(/"/g, "") || `${selectedFile.name.split('.')[0]}_converted.svg`;

      setSvgBlob(blob);
      setSvgFilename(filename);

      setProgress(100);
      addLog("SVG conversion complete!", "success");
      toast.success("Image successfully converted to SVG!");
      setHasError(false);
      setErrorType(null);

    } catch (error: any) {
      const errorMessage = error.message || "Conversion failed";
      setHasError(true);
      
      addLog(`Error: ${errorMessage}`, "error");
      
      // Determine error type and show appropriate message
      if (errorMessage.includes("quota") || errorMessage.includes("429") || errorMessage.includes("resource_exhausted")) {
        setErrorType("quota");
        addLog("⚠️ API quota exceeded. Wait 1-2 minutes or check your API key.", "warning");
        toast.error("API Quota Exceeded", {
          description: "Please wait a moment and try again, or check your Gemini API quota.",
          duration: 5000,
        });
      } else if (errorMessage.includes("timeout") || errorMessage.includes("network") || errorMessage.includes("fetch")) {
        setErrorType("network");
        addLog("🔄 Network issue detected. Click 'Retry' to try again.", "warning");
        toast.error("Network Error", {
          description: "Connection issue detected. Please try again.",
          duration: 5000,
        });
      } else {
        setErrorType("general");
        toast.error(errorMessage, {
          duration: 5000,
        });
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRetry = () => {
    addLog("🔄 Retrying conversion...", "info");
    handleConvert();
  };

  const handleDownload = () => {
    if (!svgBlob) return;

    const url = window.URL.createObjectURL(svgBlob);
    const a = document.createElement("a");
    a.href = url;
    a.download = svgFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast.success("SVG file downloaded!");
    addLog("SVG file downloaded successfully", "success");
  };

  const openQuotaPage = () => {
    window.open("https://aistudio.google.com/", "_blank");
    addLog("Opened Gemini API quota page", "info");
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Image → SVG Converter</h1>
        <p className="text-muted-foreground">
          Convert raster images to scalable vector graphics using AI-powered analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <FileUpload
            accept=".jpg,.jpeg,.png,.gif,.bmp,.webp"
            onFileSelect={handleFileSelect}
            isProcessing={isProcessing}
            progress={progress}
          />

          {selectedFile && !isProcessing && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Diagram Type
                </label>
                <Select value={diagramType} onValueChange={setDiagramType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select diagram type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">
                      <span className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4" />
                        Auto-detect
                      </span>
                    </SelectItem>
                    <SelectItem value="flowchart">Flowchart</SelectItem>
                    <SelectItem value="waveform">Waveform</SelectItem>
                    <SelectItem value="block_diagram">Block Diagram</SelectItem>
                    <SelectItem value="power_architecture">Power Architecture</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {!hasError && (
                <Button
                  onClick={handleConvert}
                  className="w-full cyber-glow-intense"
                  size="lg"
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Convert to SVG
                </Button>
              )}
            </div>
          )}

          {/* Error Alert with Retry Button */}
          {hasError && selectedFile && !isProcessing && (
            <Alert variant="destructive" className="border-red-500/50 bg-red-500/10">
              <AlertDescription className="space-y-3">
                <div className="flex flex-col gap-2">
                  {errorType === "quota" && (
                    <>
                      <p className="font-medium">API Quota Exceeded</p>
                      <p className="text-sm">
                        Your Gemini API quota has been reached. Please wait a few minutes or check your quota limits.
                      </p>
                      <div className="flex gap-2 mt-2">
                        <Button
                          onClick={handleRetry}
                          className="flex-1 cyber-glow-intense bg-orange-600 hover:bg-orange-700"
                          size="sm"
                        >
                          <RefreshCw className="mr-2 h-4 w-4" />
                          Retry
                        </Button>
                        <Button
                          onClick={openQuotaPage}
                          variant="outline"
                          className="flex-1 border-orange-500/50 hover:bg-orange-500/10"
                          size="sm"
                        >
                          <ExternalLink className="mr-2 h-4 w-4" />
                          Check Quota
                        </Button>
                      </div>
                    </>
                  )}
                  
                  {errorType === "network" && (
                    <>
                      <p className="font-medium">Network Error</p>
                      <p className="text-sm">
                        Unable to connect to the server. Please check your connection and try again.
                      </p>
                      <Button
                        onClick={handleRetry}
                        className="w-full cyber-glow-intense bg-blue-600 hover:bg-blue-700 mt-2"
                        size="sm"
                      >
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Retry Connection
                      </Button>
                    </>
                  )}
                  
                  {errorType === "general" && (
                    <>
                      <p className="font-medium">Conversion Failed</p>
                      <p className="text-sm">
                        An error occurred during conversion. Please try again.
                      </p>
                      <Button
                        onClick={handleRetry}
                        className="w-full cyber-glow-intense bg-red-600 hover:bg-red-700 mt-2"
                        size="sm"
                      >
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Try Again
                      </Button>
                    </>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {svgBlob && (
            <Button
              onClick={handleDownload}
              className="w-full cyber-glow-intense bg-green-600 hover:bg-green-700"
              size="lg"
            >
              <Download className="mr-2 h-4 w-4" />
              Download SVG
            </Button>
          )}
        </div>

        <LogViewer logs={logs} />
      </div>

      {svgBlob && (
        <div className="border rounded-lg p-6 bg-card">
          <h3 className="text-lg font-semibold mb-4">Preview</h3>
          <div className="border rounded p-4 bg-white flex items-center justify-center min-h-[300px]">
            <img 
              src={URL.createObjectURL(svgBlob)} 
              alt="SVG Preview" 
              className="max-w-full max-h-[400px]"
            />
          </div>
        </div>
      )}
    </div>
  );
}
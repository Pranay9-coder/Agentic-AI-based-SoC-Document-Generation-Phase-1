/**
 * Spec Source Editor Component
 * File: src/components/SpecSourceEditor.tsx
 * 
 * Allows editing DITA topics, REGS files, ditamaps, and managing images
 */
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
  FileText,
  Image as ImageIcon,
  Save,
  Download,
  RefreshCw,
  Folder,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";

const API_BASE_URL = "http://localhost:5000/api";

interface FileInfo {
  name: string;
  size: number;
  extension: string;
  path: string;
}

interface IPStructure {
  ip_name: string;
  folders: {
    dita_topics?: FileInfo[];
    dita_map?: FileInfo[];
    regs?: FileInfo[];
    images?: FileInfo[];
  };
}

interface SpecSourceEditorProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
  onPdfRegenerated: () => void;
}

export function SpecSourceEditor({
  sessionId,
  isOpen,
  onClose,
  onPdfRegenerated,
}: SpecSourceEditorProps) {
  const [structure, setStructure] = useState<IPStructure[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [fileContent, setFileContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [isModified, setIsModified] = useState(false);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [selectedIP, setSelectedIP] = useState<string | null>(null);
  const [selectedFolder, setSelectedFolder] = useState<string>("dita_topics");

  useEffect(() => {
    if (isOpen && sessionId) {
      loadStructure();
    }
  }, [isOpen, sessionId]);

  const loadStructure = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/spec-editor/structure/${sessionId}`
      );

      if (!response.ok) {
        throw new Error("Failed to load structure");
      }

      const data = await response.json();

      if (data.success) {
        setStructure(data.ips);
        if (data.ips.length > 0) {
          setSelectedIP(data.ips[0].ip_name);
        }
        toast.success("Spec source loaded");
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to load structure";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const loadFile = async (file: FileInfo) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/spec-editor/file/${sessionId}?path=${encodeURIComponent(
          file.path
        )}`
      );

      if (!response.ok) {
        throw new Error("Failed to load file");
      }

      const data = await response.json();

      if (data.success) {
        if (data.type === "text") {
          setSelectedFile(file);
          setFileContent(data.content);
          setOriginalContent(data.content);
          setIsModified(false);
          toast.success(`Loaded ${file.name}`);
        } else if (data.type === "image") {
          toast.info("Image preview not yet implemented");
        }
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to load file";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const saveFile = async () => {
    if (!selectedFile) return;

    setSaving(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/spec-editor/file/${sessionId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            path: selectedFile.path,
            content: fileContent,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to save file");
      }

      const data = await response.json();

      if (data.success) {
        setOriginalContent(fileContent);
        setIsModified(false);
        toast.success(`Saved ${selectedFile.name}`);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to save file";
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleContentChange = (value: string) => {
    setFileContent(value);
    setIsModified(value !== originalContent);
  };

  const regeneratePDF = async () => {
    if (isModified) {
      toast.error("Please save all changes before regenerating PDF");
      return;
    }

    setRegenerating(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/spec-editor/regenerate-pdf/${sessionId}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to regenerate PDF");
      }

      const data = await response.json();

      if (data.success) {
        toast.success("PDF regenerated successfully!");
        onPdfRegenerated();
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to regenerate PDF";
      toast.error(errorMessage);
    } finally {
      setRegenerating(false);
    }
  };

  const currentIP = structure.find((ip) => ip.ip_name === selectedIP);
  const currentFiles =
    currentIP?.folders[selectedFolder as keyof typeof currentIP.folders] || [];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[85vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Spec Source Editor
          </DialogTitle>
          <DialogDescription>
            Edit DITA topics, REGS files, and manage images. Changes are saved
            immediately.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 h-full">
          {/* IP Selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">IP:</span>
            <select
              value={selectedIP || ""}
              onChange={(e) => setSelectedIP(e.target.value)}
              className="px-3 py-1 border rounded-md bg-background"
            >
              {structure.map((ip) => (
                <option key={ip.ip_name} value={ip.ip_name}>
                  {ip.ip_name}
                </option>
              ))}
            </select>

            <div className="flex-1" />

            <Button
              onClick={regeneratePDF}
              disabled={regenerating || isModified}
              variant="default"
              className="cyber-glow-intense"
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${regenerating ? "animate-spin" : ""}`}
              />
              Regenerate PDF
            </Button>
          </div>

          {isModified && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                You have unsaved changes. Save before regenerating PDF.
              </AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-12 gap-4 flex-1 min-h-0">
            {/* File Browser */}
            <div className="col-span-3 border rounded-lg p-3">
              <Tabs value={selectedFolder} onValueChange={setSelectedFolder}>
                <TabsList className="grid grid-cols-2 mb-3">
                  <TabsTrigger value="dita_topics">
                    <FileText className="h-3 w-3 mr-1" />
                    Topics
                  </TabsTrigger>
                  <TabsTrigger value="dita_map">
                    <Folder className="h-3 w-3 mr-1" />
                    Maps
                  </TabsTrigger>
                </TabsList>

                <TabsList className="grid grid-cols-2 mb-3">
                  <TabsTrigger value="regs">
                    <FileText className="h-3 w-3 mr-1" />
                    REGS
                  </TabsTrigger>
                  <TabsTrigger value="images">
                    <ImageIcon className="h-3 w-3 mr-1" />
                    Images
                  </TabsTrigger>
                </TabsList>
              </Tabs>

              <ScrollArea className="h-[calc(100%-80px)]">
                <div className="space-y-1">
                  {currentFiles.length === 0 ? (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      No files
                    </p>
                  ) : (
                    currentFiles.map((file) => (
                      <button
                        key={file.path}
                        onClick={() => loadFile(file)}
                        className={`w-full text-left px-2 py-1.5 text-xs rounded hover:bg-secondary transition-colors ${
                          selectedFile?.path === file.path
                            ? "bg-secondary"
                            : ""
                        }`}
                      >
                        <div className="font-medium truncate">{file.name}</div>
                        <div className="text-muted-foreground text-[10px]">
                          {(file.size / 1024).toFixed(1)} KB
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </ScrollArea>
            </div>

            {/* Editor */}
            <div className="col-span-9 border rounded-lg p-4 flex flex-col">
              {selectedFile ? (
                <>
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-sm">
                        {selectedFile.name}
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        {selectedFile.extension} file • {(selectedFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {isModified && (
                        <span className="text-xs text-orange-500 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          Modified
                        </span>
                      )}
                      {!isModified && fileContent && (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Saved
                        </span>
                      )}

                      <Button
                        onClick={saveFile}
                        disabled={!isModified || saving}
                        size="sm"
                      >
                        <Save className="h-3 w-3 mr-1" />
                        {saving ? "Saving..." : "Save"}
                      </Button>
                    </div>
                  </div>

                  <Textarea
                    value={fileContent}
                    onChange={(e) => handleContentChange(e.target.value)}
                    className="flex-1 font-mono text-xs resize-none"
                    placeholder="File content..."
                  />

                  <div className="mt-3 text-xs text-muted-foreground">
                    <p>
                      💡 Tip: Edit carefully to maintain XML structure validity
                    </p>
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <FileText className="h-12 w-12 mx-auto mb-3 opacity-20" />
                    <p className="text-sm">Select a file to edit</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
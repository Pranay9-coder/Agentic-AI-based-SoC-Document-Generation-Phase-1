import { useState, useRef } from "react";
import { Upload, FileUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface FileUploadProps {
  accept: string;
  onFileSelect: (file: File) => void | Promise<void>;
  onMultipleFilesSelect?: (files: File[]) => void | Promise<void>;
  isProcessing: boolean;
  progress: number;
  multiple?: boolean;
}

export function FileUpload({
  accept,
  onFileSelect,
  onMultipleFilesSelect,
  isProcessing,
  progress,
  multiple = false
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleFiles(files);
    }
  };

  const handleFiles = (files: File[]) => {
    if (files.length === 0) return;

    setSelectedFiles(files);

    if (multiple && onMultipleFilesSelect) {
      onMultipleFilesSelect(files);
    } else {
      onFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Card 
      className={`cursor-pointer transition-all duration-300 ${
        isDragging ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
      } ${isProcessing ? 'pointer-events-none opacity-70' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <CardContent className="p-8">
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInput}
          className="hidden"
          disabled={isProcessing}
          multiple={multiple}
        />
        
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="p-4 rounded-full bg-secondary">
            {selectedFiles.length > 0 ? (
              <FileUp className="h-8 w-8 text-primary" />
            ) : (
              <Upload className="h-8 w-8 text-muted-foreground" />
            )}
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-1">
              {selectedFiles.length > 0 
                ? `${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''} selected` 
                : multiple 
                  ? 'Drop files here or click to browse'
                  : 'Drop file here or click to browse'}
            </h3>
            <p className="text-sm text-muted-foreground">
              {multiple 
                ? 'You can select multiple files'
                : 'Maximum file size: 50MB'}
            </p>
            
            {selectedFiles.length > 0 && (
              <div className="mt-3 text-xs text-muted-foreground">
                {selectedFiles.map((file, index) => (
                  <div key={index}>• {file.name}</div>
                ))}
              </div>
            )}
          </div>
          
          {isProcessing && (
            <div className="w-full">
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-muted-foreground mt-2">
                Processing... {progress}%
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
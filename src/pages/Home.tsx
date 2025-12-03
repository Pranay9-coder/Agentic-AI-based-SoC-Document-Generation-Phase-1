import { FileText, FileCode, FileImage } from "lucide-react";
import { ModuleCard } from "@/components/ModuleCard";

const modules = [
  {
    title: "PDF → DITA Map",
    description: "Convert PDF documents to DITA Map format with automatic image to SVG conversion",
    icon: FileText,
    route: "/pdf-to-dita",
  },
  {
    title: "DocX → DITA Map",
    description: "Transform Word documents to DITA Map format with image to SVG conversion",
    icon: FileCode,
    route: "/docx-to-dita",
  },
  {
    title: ".REGS → PDF",
    description: "Convert regulatory files to PDF format for easy distribution and viewing",
    icon: FileText,
    route: "/regs-to-pdf",
  },
  {
    title: "Image → SVG",
    description: "Convert raster images to scalable vector graphics for better quality",
    icon: FileImage,
    route: "/image-to-svg",
  },
];

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          Welcome to TransformX AI
        </h1>
        <p className="text-muted-foreground text-lg">
          Choose a module to start transforming your documents
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {modules.map((module) => (
          <ModuleCard key={module.title} {...module} />
        ))}
      </div>
    </div>
  );
}

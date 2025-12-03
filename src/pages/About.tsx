import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Mail, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function About() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">About TransformX AI</h1>
        <p className="text-muted-foreground text-lg">
          Advanced document transformation powered by AI
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Our Platform</CardTitle>
          <CardDescription>
            Building the future of document conversion
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-foreground leading-relaxed">
            TransformX AI is a unified platform that simplifies complex document
            transformations. Built for UST, our platform leverages advanced AI
            algorithms to provide seamless conversion between various document
            formats while maintaining quality and structure.
          </p>
          <p className="text-foreground leading-relaxed">
            Whether you're converting PDFs to DITA Maps, transforming Word
            documents, processing regulatory files, or vectorizing images,
            TransformX AI handles it all with precision and speed.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Our Modules</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="font-semibold text-primary">PDF → DITA Map</h3>
              <p className="text-sm text-muted-foreground">
                Convert PDF documents to structured DITA format with automatic
                image processing
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-primary">DocX → DITA Map</h3>
              <p className="text-sm text-muted-foreground">
                Transform Word documents to DITA while preserving styles and
                structure
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-primary">.REGS → PDF</h3>
              <p className="text-sm text-muted-foreground">
                Convert regulatory files to universal PDF format for easy
                distribution
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-primary">Image → SVG</h3>
              <p className="text-sm text-muted-foreground">
                Vectorize raster images for scalable, high-quality graphics
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Contact Us</CardTitle>
          <CardDescription>Get in touch with our team</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <Mail className="h-5 w-5 text-primary" />
            <span>cs@ust.com</span>
          </div>
          <Button variant="default" className="cyber-glow-intense" asChild>
            <a
              href="https://www.ust.com/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Visit UST Website
            </a>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

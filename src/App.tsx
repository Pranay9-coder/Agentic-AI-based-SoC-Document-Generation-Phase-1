import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import Home from "./pages/Home";
import PdfToDita from "./pages/modules/PdfToDita";
import DocxToDita from "./pages/modules/DocxToDita";
import RegsToPdf from "./pages/modules/RegsToPdf";
import ImageToSvg from "./pages/modules/ImageToSvg";
import History from "./pages/History";
import Settings from "./pages/Settings";
import About from "./pages/About";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/pdf-to-dita" element={<PdfToDita />} />
            <Route path="/docx-to-dita" element={<DocxToDita />} />
            <Route path="/regs-to-pdf" element={<RegsToPdf />} />
            <Route path="/image-to-svg" element={<ImageToSvg />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

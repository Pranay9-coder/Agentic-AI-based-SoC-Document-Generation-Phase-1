import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Trash2, FileText, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";

// API base URL - adjust this to match your backend
const API_BASE_URL = "http://localhost:5000/api";

interface Conversion {
  id: string;
  filename: string;
  original_name: string;
  type: string;
  conversion_type: 'dita' | 'regs' | 'any-to-regs' | 'svg';
  date: string;
  status: string;
  download_url: string;
  topic_count?: number;
  size?: number;
}

export default function History() {
  const [conversions, setConversions] = useState<Conversion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());

  // Fetch conversion history
  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/history/list`);
      const data = await response.json();
      
      if (data.success) {
        setConversions(data.conversions);
        console.log(`✅ Loaded ${data.count} conversions`);
      } else {
        setError(data.error || 'Failed to load history');
      }
    } catch (err) {
      console.error('Error fetching history:', err);
      setError('Unable to connect to server. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  // Load history on component mount
  useEffect(() => {
    fetchHistory();
  }, []);

  // Handle download
  const handleDownload = async (conversion: Conversion) => {
    try {
      // Construct the download URL
      const downloadUrl = `${API_BASE_URL}${conversion.download_url.replace('/api', '')}`;
      
      // Open download in new window/tab
      window.open(downloadUrl, '_blank');
      
      // Show brief success message
      toast.success(`Download started: ${conversion.filename}`, {
        duration: 2000,
      });
    } catch (err) {
      toast.error('Download failed. Please try again.');
      console.error('Download error:', err);
    }
  };

  // Handle delete
  const handleDelete = async (conversion: Conversion) => {
    // Confirm deletion
    if (!confirm(`Are you sure you want to delete "${conversion.filename}"? This action cannot be undone.`)) {
      return;
    }

    try {
      // Add to deleting set
      setDeletingIds(prev => new Set(prev).add(conversion.id));
      
      const loadingToast = toast.loading('Deleting...');
      
      const response = await fetch(
        `${API_BASE_URL}/history/delete/${conversion.conversion_type}/${conversion.id}`,
        { method: 'DELETE' }
      );
      
      const data = await response.json();
      
      toast.dismiss(loadingToast);
      
      if (data.success) {
        toast.success('File deleted successfully');
        // Remove from local state
        setConversions(prev => prev.filter(c => c.id !== conversion.id));
      } else {
        toast.error(data.error || 'Failed to delete file');
      }
    } catch (err) {
      toast.error('Delete failed. Please try again.');
      console.error('Delete error:', err);
    } finally {
      // Remove from deleting set
      setDeletingIds(prev => {
        const next = new Set(prev);
        next.delete(conversion.id);
        return next;
      });
    }
  };

  // Format file size
  const formatSize = (bytes?: number) => {
    if (!bytes) return '';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    const mb = kb / 1024;
    return `${mb.toFixed(1)} MB`;
  };

  // Get icon color based on conversion type
  const getIconColor = (type: string) => {
    if (type.includes('DITA')) return 'text-blue-500';
    if (type.includes('PDF')) return 'text-red-500';
    if (type.includes('REGS')) return 'text-purple-500';
    if (type.includes('SVG')) return 'text-green-500';
    return 'text-primary';
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Conversion History</h1>
          <p className="text-muted-foreground">
            View and manage your conversion outputs
          </p>
        </div>
        <Button
          variant="outline"
          onClick={fetchHistory}
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading...
            </>
          ) : (
            'Refresh'
          )}
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {loading && conversions.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {/* Empty State */}
      {!loading && conversions.length === 0 && !error && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No conversions yet</h3>
            <p className="text-muted-foreground text-center">
              Your conversion history will appear here after you process files.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Conversion List */}
      <div className="space-y-4">
        {conversions.map((item) => (
          <Card key={item.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-secondary">
                    <FileText className={`h-5 w-5 ${getIconColor(item.type)}`} />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{item.filename}</CardTitle>
                    <CardDescription>
                      {item.type} • {item.date}
                      {item.size && ` • ${formatSize(item.size)}`}
                      {item.topic_count && ` • ${item.topic_count} topics`}
                    </CardDescription>
                  </div>
                </div>
                <span className="text-sm text-green-500 font-medium">
                  {item.status}
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => handleDownload(item)}
                  disabled={deletingIds.has(item.id)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(item)}
                  disabled={deletingIds.has(item.id)}
                >
                  {deletingIds.has(item.id) ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Statistics */}
      {conversions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold">{conversions.length}</div>
                <div className="text-sm text-muted-foreground">Total</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {conversions.filter(c => c.conversion_type === 'dita').length}
                </div>
                <div className="text-sm text-muted-foreground">DITA</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {conversions.filter(c => c.conversion_type === 'regs').length}
                </div>
                <div className="text-sm text-muted-foreground">REGS→PDF</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {conversions.filter(c => c.conversion_type === 'any-to-regs').length}
                </div>
                <div className="text-sm text-muted-foreground">ANY→REGS</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
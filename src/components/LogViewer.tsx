import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface LogEntry {
  timestamp: string;
  message: string;
  type: "info" | "success" | "error" | "warning";
}

interface LogViewerProps {
  logs: LogEntry[];
}

export function LogViewer({ logs }: LogViewerProps) {
  const getLogColor = (type: LogEntry["type"]) => {
    switch (type) {
      case "success":
        return "text-neon-green";
      case "error":
        return "text-destructive";
      case "warning":
        return "text-yellow-500";
      default:
        return "text-muted-foreground";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Process Logs</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64 w-full rounded border border-border bg-secondary/50 p-4">
          <div className="space-y-2 font-mono text-sm">
            {logs.length === 0 ? (
              <p className="text-muted-foreground">No logs yet...</p>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="flex gap-2">
                  <span className="text-muted-foreground">[{log.timestamp}]</span>
                  <span className={getLogColor(log.type)}>{log.message}</span>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

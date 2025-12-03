import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { useState } from "react";

export default function Settings() {
  const [autoConvert, setAutoConvert] = useState(false);
  const [notifications, setNotifications] = useState(true);

  const handleSave = () => {
    toast.success("Settings saved successfully");
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Manage your application preferences
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
          <CardDescription>Configure how the application behaves</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="auto-convert">Auto-convert on upload</Label>
              <p className="text-sm text-muted-foreground">
                Automatically start conversion when file is uploaded
              </p>
            </div>
            <Switch
              id="auto-convert"
              checked={autoConvert}
              onCheckedChange={setAutoConvert}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="notifications">Enable notifications</Label>
              <p className="text-sm text-muted-foreground">
                Show toast notifications for conversion status
              </p>
            </div>
            <Switch
              id="notifications"
              checked={notifications}
              onCheckedChange={setNotifications}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Output Settings</CardTitle>
          <CardDescription>Configure output file preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="output-folder">Default output folder</Label>
            <Input
              id="output-folder"
              placeholder="/downloads/transformx"
              defaultValue="/downloads/transformx"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="filename-pattern">Filename pattern</Label>
            <Input
              id="filename-pattern"
              placeholder="{original}_converted_{date}"
              defaultValue="{original}_converted_{date}"
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave} size="lg" className="cyber-glow-intense">
          Save Settings
        </Button>
      </div>
    </div>
  );
}

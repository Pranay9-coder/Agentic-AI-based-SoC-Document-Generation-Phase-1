import { LucideIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

interface ModuleCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  route: string;
}

export function ModuleCard({ title, description, icon: Icon, route }: ModuleCardProps) {
  const navigate = useNavigate();

  return (
    <Card className="group hover:border-primary transition-all duration-300 cursor-pointer dark:cyber-glow" onClick={() => navigate(route)}>
      <CardHeader>
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-secondary group-hover:bg-primary/10 transition-colors">
            <Icon className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-xl">{title}</CardTitle>
        </div>
        <CardDescription className="text-base">{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button 
          variant="default" 
          className="w-full group-hover:cyber-glow-intense"
          onClick={(e) => {
            e.stopPropagation();
            navigate(route);
          }}
        >
          Open Module
        </Button>
      </CardContent>
    </Card>
  );
}

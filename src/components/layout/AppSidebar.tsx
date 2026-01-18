import { Home, FileText, FileCode, FileImage, FileSpreadsheet, History, Info, Layers, FolderArchive } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

const menuItems = [
  { title: "Home", url: "/", icon: Home },
  { title: "Multi-IP Doc Generator", url: "/multi-ip-doc-gen", icon: Layers },
  { title: "Spec Source → PDF", url: "/spec-to-pdf", icon: FolderArchive },
  { title: "PDF → DITA Map", url: "/pdf-to-dita", icon: FileText },
  { title: "DocX → DITA Map", url: "/docx-to-dita", icon: FileCode },
  { title: ".REGS → PDF", url: "/regs-to-pdf", icon: FileText },
  { title: "PDF/DocX/Excel → .REGS", url: "/any-to-regs", icon: FileSpreadsheet },
  { title: "Image → SVG", url: "/image-to-svg", icon: FileImage },
  { title: "Upload History", url: "/history", icon: History },
  { title: "About", url: "/about", icon: Info },
];

export function AppSidebar() {
  const { open } = useSidebar();

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs uppercase tracking-wider">
            Navigation
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end
                      className="flex items-center gap-3 hover:bg-sidebar-accent"
                      activeClassName="bg-sidebar-accent text-sidebar-primary font-medium"
                    >
                      <item.icon className="h-4 w-4" />
                      {open && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
  FolderOpen,
  Library,
  Users,
  Settings,
  LogOut,
  Palette,
  BookText,
  ChevronDown,
  Database,
} from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<{ nickname: string; role: string } | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    // Decode JWT payload (not verification, just display)
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      setUser({ nickname: payload.nickname, role: payload.role });
    } catch {
      router.push("/login");
    }
  }, [router]);

  function handleLogout() {
    localStorage.removeItem("token");
    router.push("/login");
  }

  if (!user) return null;

  const isAssetsActive = pathname.startsWith("/assets");

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-56 bg-[var(--card)] border-r border-[var(--border)] flex flex-col shrink-0">
        {/* Logo */}
        <div className="p-4 border-b border-[var(--border)]">
          <h1 className="text-lg font-bold">画宗制片中枢</h1>
          <p className="text-xs text-[var(--muted-foreground)] mt-0.5">
            Production Hub
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1">
          <NavItem href="/projects" icon={<FolderOpen className="h-4 w-4" />} active={pathname.startsWith("/projects")}>
            项目中心
          </NavItem>

          {/* Assets with sub-menu */}
          <div>
            <NavItem href="/assets" icon={<Library className="h-4 w-4" />} active={isAssetsActive}>
              <span className="flex-1">资产库</span>
              <ChevronDown className={`h-3 w-3 transition-transform ${isAssetsActive ? "rotate-0" : "-rotate-90"}`} />
            </NavItem>
            {isAssetsActive && (
              <div className="ml-6 mt-0.5 space-y-0.5">
                <SubNavItem href="/assets/style-templates" icon={<Palette className="h-3.5 w-3.5" />} active={pathname === "/assets/style-templates"}>
                  风格模板
                </SubNavItem>
                <SubNavItem href="/assets/prompts" icon={<BookText className="h-3.5 w-3.5" />} active={pathname === "/assets/prompts"}>
                  提示词库
                </SubNavItem>
                <SubNavItem href="/assets/archives" icon={<Database className="h-3.5 w-3.5" />} active={pathname === "/assets/archives"}>
                  全局档案
                </SubNavItem>
              </div>
            )}
          </div>

          <NavItem href="/team" icon={<Users className="h-4 w-4" />} active={pathname.startsWith("/team")}>
            团队管理
          </NavItem>
          <NavItem href="/settings" icon={<Settings className="h-4 w-4" />} active={pathname.startsWith("/settings")}>
            设置
          </NavItem>
        </nav>

        {/* User */}
        <div className="p-3 border-t border-[var(--border)]">
          <div className="flex items-center justify-between">
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{user.nickname}</p>
              <p className="text-xs text-[var(--muted-foreground)]">
                {user.role === "admin" ? "管理员" : user.role === "director" ? "导演" : "美术"}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-md hover:bg-[var(--accent)] text-[var(--muted-foreground)]"
              title="退出登录"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}

function NavItem({
  href,
  icon,
  active,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-2.5 px-3 py-2 text-sm rounded-lg transition-colors ${
        active
          ? "bg-[var(--accent)] text-[var(--foreground)] font-medium"
          : "hover:bg-[var(--accent)] text-[var(--muted-foreground)]"
      }`}
    >
      {icon}
      {children}
    </Link>
  );
}

function SubNavItem({
  href,
  icon,
  active,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-2 px-2.5 py-1.5 text-xs rounded-md transition-colors ${
        active
          ? "bg-[var(--accent)] text-[var(--foreground)] font-medium"
          : "hover:bg-[var(--accent)] text-[var(--muted-foreground)]"
      }`}
    >
      {icon}
      {children}
    </Link>
  );
}

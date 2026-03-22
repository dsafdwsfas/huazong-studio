"use client";

import Link from "next/link";
import { Sparkles, BookText, Palette } from "lucide-react";

const ASSET_SECTIONS = [
  {
    title: "风格模板库",
    description: "跨项目复用的风格定调模板，从参考图提取或手动创建",
    href: "/assets/style-templates",
    icon: Palette,
    color: "text-violet-500",
    bgColor: "bg-violet-50",
  },
  {
    title: "提示词资产库",
    description: "团队共享的 AI 生成提示词，支持标签分类和一键复制",
    href: "/assets/prompts",
    icon: BookText,
    color: "text-sky-500",
    bgColor: "bg-sky-50",
  },
];

export default function AssetsPage() {
  return (
    <div className="p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[var(--primary)]" />
          资产库
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] mt-1">
          管理团队共享的风格模板和提示词资产
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {ASSET_SECTIONS.map((section) => (
          <Link
            key={section.href}
            href={section.href}
            className="group bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 hover:border-[var(--primary)] hover:shadow-md transition-all"
          >
            <div className={`inline-flex p-2.5 rounded-lg ${section.bgColor} mb-3`}>
              <section.icon className={`h-5 w-5 ${section.color}`} />
            </div>
            <h2 className="font-semibold text-sm mb-1 group-hover:text-[var(--primary)] transition-colors">
              {section.title}
            </h2>
            <p className="text-xs text-[var(--muted-foreground)] leading-relaxed">
              {section.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogIn, UserPlus } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [inviteCode, setInviteCode] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
      const body = isRegister
        ? { phone, password, nickname, inviteCode }
        : { phone, password };

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "操作失败");
        return;
      }

      // Store token
      localStorage.setItem("token", data.token);
      router.push("/projects");
    } catch {
      setError("网络错误，请重试");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">画宗制片中枢</h1>
          <p className="text-[var(--muted-foreground)] mt-2 text-sm">
            AI 影视制片管理平台
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">
            {isRegister ? "注册账号" : "登录"}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <>
                <div>
                  <label className="text-sm font-medium text-[var(--foreground)]">
                    昵称
                  </label>
                  <input
                    type="text"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    placeholder="你的名字"
                    required
                    className="mt-1 w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-[var(--foreground)]">
                    邀请码
                  </label>
                  <input
                    type="text"
                    value={inviteCode}
                    onChange={(e) => setInviteCode(e.target.value)}
                    placeholder="请输入邀请码"
                    required
                    className="mt-1 w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  />
                </div>
              </>
            )}

            <div>
              <label className="text-sm font-medium text-[var(--foreground)]">
                手机号
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="输入手机号"
                required
                className="mt-1 w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-[var(--foreground)]">
                密码
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="输入密码"
                required
                minLength={6}
                className="mt-1 w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
              />
            </div>

            {error && (
              <p className="text-sm text-[var(--destructive)]">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-lg font-medium text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? (
                <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
              ) : isRegister ? (
                <UserPlus className="h-4 w-4" />
              ) : (
                <LogIn className="h-4 w-4" />
              )}
              {isRegister ? "注册" : "登录"}
            </button>
          </form>

          <div className="mt-4 text-center">
            <button
              onClick={() => {
                setIsRegister(!isRegister);
                setError("");
              }}
              className="text-sm text-[var(--primary)] hover:underline"
            >
              {isRegister ? "已有账号？去登录" : "没有账号？注册"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

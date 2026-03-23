"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { LogIn, Mail, KeyRound, Send } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<"email" | "code">("email");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [nickname, setNickname] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [isNewUser, setIsNewUser] = useState(false);
  const [countdown, setCountdown] = useState(0);

  // Countdown timer for resend
  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  async function handleSendCode(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/send-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "发送失败");
        return;
      }

      setIsNewUser(data.isNewUser);
      setStep("code");
      setCountdown(60);
    } catch {
      setError("网络错误，请重试");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyCode(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const body: Record<string, string> = { email, code };
      if (isNewUser) {
        body.nickname = nickname;
        body.inviteCode = inviteCode;
      }

      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "登录失败");
        return;
      }

      localStorage.setItem("token", data.token);
      router.push("/projects");
    } catch {
      setError("网络错误，请重试");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    if (countdown > 0) return;
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/send-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "发送失败");
        return;
      }

      setCountdown(60);
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
          {step === "email" ? (
            <>
              <h2 className="text-lg font-semibold mb-4">登录</h2>
              <form onSubmit={handleSendCode} className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-[var(--foreground)]">
                    邮箱
                  </label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="输入你的邮箱"
                      required
                      className="w-full pl-10 pr-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                    />
                  </div>
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
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                  发送验证码
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">
                  {isNewUser ? "注册新账号" : "输入验证码"}
                </h2>
                <button
                  onClick={() => {
                    setStep("email");
                    setError("");
                    setCode("");
                  }}
                  className="text-sm text-[var(--primary)] hover:underline"
                >
                  换个邮箱
                </button>
              </div>

              <p className="text-sm text-[var(--muted-foreground)] mb-4">
                验证码已发送到 <span className="font-medium text-[var(--foreground)]">{email}</span>
              </p>

              <form onSubmit={handleVerifyCode} className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-[var(--foreground)]">
                    验证码
                  </label>
                  <div className="relative mt-1">
                    <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
                    <input
                      type="text"
                      value={code}
                      onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      placeholder="6 位数字验证码"
                      required
                      maxLength={6}
                      inputMode="numeric"
                      autoFocus
                      className="w-full pl-10 pr-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm tracking-widest focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                    />
                  </div>
                  <div className="mt-2 text-right">
                    <button
                      type="button"
                      onClick={handleResend}
                      disabled={countdown > 0 || loading}
                      className="text-xs text-[var(--primary)] hover:underline disabled:text-[var(--muted-foreground)] disabled:no-underline"
                    >
                      {countdown > 0 ? `${countdown}s 后可重新发送` : "重新发送验证码"}
                    </button>
                  </div>
                </div>

                {isNewUser && (
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

                {error && (
                  <p className="text-sm text-[var(--destructive)]">{error}</p>
                )}

                <button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-lg font-medium text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {loading ? (
                    <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                  ) : (
                    <LogIn className="h-4 w-4" />
                  )}
                  {isNewUser ? "注册并登录" : "登录"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

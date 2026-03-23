import { NextRequest, NextResponse } from "next/server";
import { getDb } from "@/lib/db-store";
import { sendVerificationCode, generateCode } from "@/lib/email";
import { generateId } from "@/lib/id";

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    if (!email || typeof email !== "string") {
      return NextResponse.json({ error: "请输入邮箱地址" }, { status: 400 });
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json({ error: "邮箱格式不正确" }, { status: 400 });
    }

    const db = getDb();
    const now = new Date();
    const oneMinuteAgo = new Date(now.getTime() - 60_000).toISOString();

    // Rate limit
    const recent = db.get<{ id: string }>(
      `SELECT id FROM verification_codes WHERE email = ? AND used = 0 AND created_at > ?`,
      email, oneMinuteAgo,
    );

    if (recent) {
      return NextResponse.json({ error: "验证码已发送，请 60 秒后重试" }, { status: 429 });
    }

    const code = generateCode();
    const expiresAt = new Date(now.getTime() + 5 * 60_000).toISOString();

    db.run(
      `INSERT INTO verification_codes (id, email, code, expires_at) VALUES (?, ?, ?, ?)`,
      generateId("vc"), email, code, expiresAt,
    );

    const result = await sendVerificationCode(email, code);
    if (!result.success) {
      return NextResponse.json({ error: result.error || "发送失败，请重试" }, { status: 500 });
    }

    const existingUser = db.get<{ id: string }>("SELECT id FROM users WHERE email = ?", email);

    return NextResponse.json({ message: "验证码已发送", isNewUser: !existingUser });
  } catch (error) {
    console.error("Send code error:", error);
    return NextResponse.json({ error: "发送失败，请重试" }, { status: 500 });
  }
}

import { NextRequest, NextResponse } from "next/server";
import { getDb } from "@/lib/db-store";
import { sendVerificationCode, generateCode } from "@/lib/email";
import { generateId } from "@/lib/id";

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    if (!email || typeof email !== "string") {
      return NextResponse.json(
        { error: "请输入邮箱地址" },
        { status: 400 },
      );
    }

    // Basic email format check
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json(
        { error: "邮箱格式不正确" },
        { status: 400 },
      );
    }

    const db = getDb();
    const now = new Date();

    // Rate limit: same email cannot request within 60 seconds
    const recentCode = db.verificationCodes.find(
      (c) =>
        c.email === email &&
        !c.used &&
        new Date(c.createdAt).getTime() > now.getTime() - 60_000,
    );

    if (recentCode) {
      return NextResponse.json(
        { error: "验证码已发送，请 60 秒后重试" },
        { status: 429 },
      );
    }

    const code = generateCode();
    const expiresAt = new Date(now.getTime() + 5 * 60_000).toISOString();

    // Store verification code
    db.verificationCodes.push({
      id: generateId("vc"),
      email,
      code,
      expiresAt,
      used: false,
      createdAt: now.toISOString(),
    });

    // Send email
    const result = await sendVerificationCode(email, code);

    if (!result.success) {
      return NextResponse.json(
        { error: result.error || "发送失败，请重试" },
        { status: 500 },
      );
    }

    // Check if user exists (for frontend to show invite code field)
    const existingUser = db.users.find((u) => u.email === email);

    return NextResponse.json({
      message: "验证码已发送",
      isNewUser: !existingUser,
    });
  } catch (error) {
    console.error("Send code error:", error);
    return NextResponse.json(
      { error: "发送失败，请重试" },
      { status: 500 },
    );
  }
}

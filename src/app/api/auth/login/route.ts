import { NextRequest, NextResponse } from "next/server";
import { createToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

export async function POST(request: NextRequest) {
  try {
    const { email, code, nickname, inviteCode } = await request.json();

    if (!email || !code) {
      return NextResponse.json(
        { error: "请输入邮箱和验证码" },
        { status: 400 },
      );
    }

    const db = getDb();
    const now = new Date();

    // Find valid verification code
    const vc = db.verificationCodes.find(
      (c) =>
        c.email === email &&
        c.code === code &&
        !c.used &&
        new Date(c.expiresAt).getTime() > now.getTime(),
    );

    if (!vc) {
      return NextResponse.json(
        { error: "验证码无效或已过期" },
        { status: 401 },
      );
    }

    // Mark code as used
    vc.used = true;

    // Find or create user
    let user = db.users.find((u) => u.email === email);

    if (!user) {
      // New user — require invite code and nickname
      if (!inviteCode) {
        return NextResponse.json(
          { error: "首次登录请输入邀请码" },
          { status: 400 },
        );
      }

      if (!nickname || !nickname.trim()) {
        return NextResponse.json(
          { error: "请输入你的昵称" },
          { status: 400 },
        );
      }

      // Verify invite code
      const invite = db.inviteCodes.find(
        (c) => c.code === inviteCode && !c.usedBy,
      );
      if (!invite) {
        return NextResponse.json(
          { error: "邀请码无效或已使用" },
          { status: 400 },
        );
      }

      const userId = generateId("usr");
      const nowStr = now.toISOString();

      user = {
        id: userId,
        email,
        phone: null,
        nickname: nickname.trim(),
        avatarUrl: null,
        role: "artist" as const,
        inviteCodeUsed: inviteCode,
        createdAt: nowStr,
        updatedAt: nowStr,
      };

      db.users.push(user);

      // Mark invite code as used
      invite.usedBy = userId;
      invite.usedAt = nowStr;
    }

    // Generate JWT
    const token = await createToken({
      sub: user.id,
      role: user.role,
      nickname: user.nickname,
    });

    return NextResponse.json({
      token,
      user: {
        id: user.id,
        email: user.email,
        nickname: user.nickname,
        role: user.role,
      },
    });
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json(
      { error: "登录失败，请重试" },
      { status: 500 },
    );
  }
}

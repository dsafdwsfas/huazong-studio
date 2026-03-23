import { NextRequest, NextResponse } from "next/server";
import { createToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

export async function POST(request: NextRequest) {
  try {
    const { email, code, nickname, inviteCode } = await request.json();

    if (!email || !code) {
      return NextResponse.json({ error: "请输入邮箱和验证码" }, { status: 400 });
    }

    const db = getDb();
    const now = new Date().toISOString();

    // Find valid verification code
    const vc = db.get<{ id: string; email: string; code: string }>(
      `SELECT id, email, code FROM verification_codes
       WHERE email = ? AND code = ? AND used = 0 AND expires_at > ?`,
      email, code, now,
    );

    if (!vc) {
      return NextResponse.json({ error: "验证码无效或已过期" }, { status: 401 });
    }

    // Mark code as used
    db.run("UPDATE verification_codes SET used = 1 WHERE id = ?", vc.id);

    // Find or create user
    let user = db.get<{ id: string; email: string; nickname: string; role: string }>(
      "SELECT id, email, nickname, role FROM users WHERE email = ?", email,
    );

    if (!user) {
      if (!inviteCode) {
        return NextResponse.json({ error: "首次登录请输入邀请码" }, { status: 400 });
      }
      if (!nickname || !nickname.trim()) {
        return NextResponse.json({ error: "请输入你的昵称" }, { status: 400 });
      }

      const invite = db.get<{ id: string; code: string }>(
        "SELECT id, code FROM invite_codes WHERE code = ? AND used_by IS NULL", inviteCode,
      );
      if (!invite) {
        return NextResponse.json({ error: "邀请码无效或已使用" }, { status: 400 });
      }

      const userId = generateId("usr");
      db.run(
        `INSERT INTO users (id, email, nickname, role, invite_code_used) VALUES (?, ?, ?, 'artist', ?)`,
        userId, email, nickname.trim(), inviteCode,
      );
      db.run("UPDATE invite_codes SET used_by = ?, used_at = ? WHERE id = ?", userId, now, invite.id);

      user = { id: userId, email, nickname: nickname.trim(), role: "artist" };
    }

    const token = await createToken({ sub: user.id, role: user.role, nickname: user.nickname });

    return NextResponse.json({
      token,
      user: { id: user.id, email: user.email, nickname: user.nickname, role: user.role },
    });
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json({ error: "登录失败，请重试" }, { status: 500 });
  }
}

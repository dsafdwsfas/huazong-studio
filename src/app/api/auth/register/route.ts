import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { createToken } from "@/lib/auth";
import { generateId } from "@/lib/id";

// In-memory store for development (replace with D1 in production)
// This will be replaced when we integrate the actual D1 database
import { getDb } from "@/lib/db-store";

export async function POST(request: NextRequest) {
  try {
    const { phone, password, nickname, inviteCode } = await request.json();

    if (!phone || !password || !nickname || !inviteCode) {
      return NextResponse.json(
        { error: "请填写所有字段" },
        { status: 400 }
      );
    }

    if (password.length < 6) {
      return NextResponse.json(
        { error: "密码至少 6 位" },
        { status: 400 }
      );
    }

    const db = getDb();

    // Verify invite code
    const invite = db.inviteCodes.find(
      (c) => c.code === inviteCode && !c.usedBy
    );
    if (!invite) {
      return NextResponse.json(
        { error: "邀请码无效或已使用" },
        { status: 400 }
      );
    }

    // Check if phone already registered
    const existingUser = db.users.find((u) => u.phone === phone);
    if (existingUser) {
      return NextResponse.json(
        { error: "该手机号已注册" },
        { status: 400 }
      );
    }

    // Create user
    const passwordHash = await bcrypt.hash(password, 10);
    const userId = generateId("usr");
    const now = new Date().toISOString();

    const user = {
      id: userId,
      phone,
      passwordHash,
      nickname,
      avatarUrl: null,
      role: "artist" as const,
      inviteCodeUsed: inviteCode,
      createdAt: now,
      updatedAt: now,
    };

    db.users.push(user);

    // Mark invite code as used
    invite.usedBy = userId;
    invite.usedAt = now;

    // Generate JWT
    const token = await createToken({
      sub: userId,
      role: user.role,
      nickname: user.nickname,
    });

    return NextResponse.json({
      token,
      user: {
        id: user.id,
        phone: user.phone,
        nickname: user.nickname,
        role: user.role,
      },
    });
  } catch (error) {
    console.error("Register error:", error);
    return NextResponse.json(
      { error: "注册失败，请重试" },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { createToken } from "@/lib/auth";
import { getDb } from "@/lib/db-store";

export async function POST(request: NextRequest) {
  try {
    const { phone, password } = await request.json();

    if (!phone || !password) {
      return NextResponse.json(
        { error: "请输入手机号和密码" },
        { status: 400 }
      );
    }

    const db = getDb();

    // Find user
    const user = db.users.find((u) => u.phone === phone);
    if (!user) {
      return NextResponse.json(
        { error: "手机号或密码错误" },
        { status: 401 }
      );
    }

    // Verify password
    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) {
      return NextResponse.json(
        { error: "手机号或密码错误" },
        { status: 401 }
      );
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
        phone: user.phone,
        nickname: user.nickname,
        role: user.role,
      },
    });
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json(
      { error: "登录失败，请重试" },
      { status: 500 }
    );
  }
}

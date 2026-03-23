import { NextResponse } from "next/server";

// Registration is now handled by the login route.
// When a new user logs in with a valid verification code + invite code,
// their account is created automatically.

export async function POST() {
  return NextResponse.json(
    { error: "请使用邮箱验证码登录，新用户会自动注册" },
    { status: 410 },
  );
}

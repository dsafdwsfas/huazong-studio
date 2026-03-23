import { Resend } from "resend";

let _resend: Resend | null = null;

function getResend(): Resend {
  if (!_resend) {
    const apiKey = process.env.RESEND_API_KEY;
    if (!apiKey) {
      throw new Error("RESEND_API_KEY environment variable must be set");
    }
    _resend = new Resend(apiKey);
  }
  return _resend;
}

const FROM_EMAIL = process.env.FROM_EMAIL || "onboarding@resend.dev";
const APP_NAME = "画宗制片中枢";

export async function sendVerificationCode(
  to: string,
  code: string,
): Promise<{ success: boolean; error?: string }> {
  try {
    const { error } = await getResend().emails.send({
      from: `${APP_NAME} <${FROM_EMAIL}>`,
      to,
      subject: `${code} — 你的登录验证码`,
      html: `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 400px; margin: 0 auto; padding: 32px;">
          <h2 style="font-size: 20px; font-weight: 600; margin: 0 0 24px;">画宗制片中枢</h2>
          <p style="color: #374151; font-size: 14px; line-height: 1.6; margin: 0 0 16px;">你的登录验证码是：</p>
          <div style="background: #f3f4f6; border-radius: 8px; padding: 16px; text-align: center; margin: 0 0 16px;">
            <span style="font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #111827;">${code}</span>
          </div>
          <p style="color: #6b7280; font-size: 13px; line-height: 1.5; margin: 0;">验证码 5 分钟内有效，请勿泄露给他人。</p>
        </div>
      `,
    });

    if (error) {
      console.error("Resend error:", error);
      return { success: false, error: error.message };
    }

    return { success: true };
  } catch (err) {
    console.error("Email send failed:", err);
    return { success: false, error: "邮件发送失败" };
  }
}

export function generateCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

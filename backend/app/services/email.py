import asyncio
import logging

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)

_resend_configured = False


def _init_resend() -> bool:
    """Configure Resend API key. Returns True if ready to send."""
    global _resend_configured
    if _resend_configured:
        return True
    if settings.resend_api_key:
        resend.api_key = settings.resend_api_key
        _resend_configured = True
        return True
    return False


def _send_sync(params: resend.Emails.SendParams) -> None:
    """Synchronous Resend call — run via asyncio.to_thread to avoid blocking."""
    resend.Emails.send(params)


async def _send(params: resend.Emails.SendParams, fallback_log: str) -> None:
    if not _init_resend():
        logger.info("[EMAIL] %s", fallback_log)
        return
    try:
        await asyncio.to_thread(_send_sync, params)
    except Exception:
        logger.exception("[EMAIL] Send failed: %s", fallback_log)


async def send_verification_otp_email(email: str, code: str) -> None:
    await _send(
        {
            "from": settings.email_from,
            "to": email,
            "subject": "Your MMAi Coach verification code",
            "html": _verification_otp_html(code),
            "text": f"Your verification code is: {code}\n\nIt expires in 10 minutes.",
        },
        fallback_log=f"Verification OTP for {email}: {code}",
    )


async def send_welcome_email(email: str, display_name: str) -> None:
    await _send(
        {
            "from": settings.email_from,
            "to": email,
            "subject": "Welcome to MMAi Coach!",
            "html": _welcome_html(display_name),
            "text": f"Welcome to MMAi Coach, {display_name}! Start training smarter: {settings.app_url}",
        },
        fallback_log=f"Welcome email for {email}",
    )


async def send_password_reset_email(email: str, token: str) -> None:
    url = f"{settings.app_url}/reset-password?token={token}"
    await _send(
        {
            "from": settings.email_from,
            "to": email,
            "subject": "Reset your MMAi Coach password",
            "html": _reset_html(url),
            "text": f"Reset your password: {url}\n\nLink expires in 30 minutes.",
        },
        fallback_log=f"Password reset link for {email}: {url}",
    )


# ── HTML Templates ────────────────────────────────────────────────────────────

_BASE = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F5F0E8;font-family:Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F0E8;padding:40px 0">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#0A1628;border-radius:12px;overflow:hidden">
        <tr><td style="padding:32px 40px;text-align:center;border-bottom:1px solid #1E3A5F">
          <span style="color:#FF6B35;font-size:26px;font-weight:bold;letter-spacing:2px">MMAi Coach</span>
        </td></tr>
        <tr><td style="padding:36px 40px;color:#F5F0E8">{body}</td></tr>
        <tr><td style="padding:20px 40px;text-align:center;border-top:1px solid #1E3A5F">
          <p style="color:#D4CFC7;font-size:12px;margin:0">© 2026 MMAi Coach. Train smarter with AI.</p>
          <p style="color:#D4CFC7;font-size:12px;margin:4px 0 0">Questions? <a href="mailto:mmai.coach@gmail.com" style="color:#FF6B35">mmai.coach@gmail.com</a></p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

_BTN = '<a href="{url}" style="display:inline-block;margin:24px 0;padding:14px 32px;background:#FF6B35;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;font-size:15px">{label}</a>'


def _verification_otp_html(code: str) -> str:
    spaced = " &nbsp; ".join(code)
    body = f"""
      <h2 style="color:#F5F0E8;margin:0 0 16px">Verify your email</h2>
      <p style="color:#D4CFC7;line-height:1.6">Enter this code in the app to verify your MMAi Coach account. It expires in <strong style="color:#F5F0E8">10 minutes</strong>.</p>
      <div style="text-align:center;margin:24px 0">
        <span style="display:inline-block;padding:16px 32px;background:#1E3A5F;border-radius:8px;color:#F5F0E8;font-size:32px;font-family:'Courier New',monospace;letter-spacing:8px;font-weight:bold">{spaced}</span>
      </div>
      <p style="color:#D4CFC7;font-size:13px">If you didn't create an account, you can ignore this email.</p>
    """
    return _BASE.format(body=body)


def _welcome_html(display_name: str) -> str:
    body = f"""
      <h2 style="color:#F5F0E8;margin:0 0 16px">Welcome, {display_name}!</h2>
      <p style="color:#D4CFC7;line-height:1.6">Your email is verified. You're ready to train smarter with AI coaching.</p>
      <ul style="color:#D4CFC7;line-height:2;padding-left:20px">
        <li>AI Coach — ask anything about training, technique, or recovery</li>
        <li>Training Journal — log sessions, track RPE and volume</li>
        <li>Recovery Logs — monitor your daily wellness</li>
        <li>Stats &amp; Charts — visualise your progress over time</li>
      </ul>
      <div style="text-align:center">{_BTN.format(url=settings.app_url, label="Start Training")}</div>
    """
    return _BASE.format(body=body)


def _reset_html(url: str) -> str:
    body = f"""
      <h2 style="color:#F5F0E8;margin:0 0 16px">Reset your password</h2>
      <p style="color:#D4CFC7;line-height:1.6">We received a request to reset your MMAi Coach password. Click the button below — the link expires in <strong style="color:#F5F0E8">30 minutes</strong>.</p>
      <div style="text-align:center">{_BTN.format(url=url, label="Reset Password")}</div>
      <p style="color:#D4CFC7;font-size:13px">Or copy this link:<br><span style="color:#FF6B35;word-break:break-all">{url}</span></p>
      <p style="color:#D4CFC7;font-size:13px">If you didn't request this, you can safely ignore this email. Your password won't change.</p>
    """
    return _BASE.format(body=body)

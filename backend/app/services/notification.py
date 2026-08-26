"""
Service de notifications email pour SIRP.

Envoie des emails lors des changements de statut des incidents.
En mode développement (EMAILS_ENABLED=False), les emails sont loggés.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service d'envoi de notifications par email"""

    @staticmethod
    def _create_message(
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str
    ) -> MIMEMultipart:
        """Crée un message email multipart (HTML + texte)"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = to_email

        part1 = MIMEText(body_text, "plain")
        part2 = MIMEText(body_html, "html")

        message.attach(part1)
        message.attach(part2)

        return message

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str
    ) -> bool:
        """
        Envoie un email.
        Retourne True si succès, False sinon.
        """
        if not settings.EMAILS_ENABLED:
            logger.info(f"[EMAIL MOCK] To: {to_email}")
            logger.info(f"[EMAIL MOCK] Subject: {subject}")
            logger.info(f"[EMAIL MOCK] Body: {body_text[:200]}...")
            return True

        try:
            message = NotificationService._create_message(
                to_email, subject, body_html, body_text
            )

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(
                    settings.EMAILS_FROM_EMAIL,
                    to_email,
                    message.as_string()
                )

            logger.info(f"Email envoyé à {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email à {to_email}: {str(e)}")
            return False

    @staticmethod
    def notify_status_change(
        incident_id: int,
        incident_title: str,
        old_status: str,
        new_status: str,
        changed_by: str,
        recipient_email: str,
        recipient_name: str
    ) -> bool:
        """Notifie un utilisateur d'un changement de statut"""

        subject = f"[SIRP] Incident #{incident_id} - Statut changé: {new_status}"

        body_text = f"""
Bonjour {recipient_name},

Le statut de l'incident #{incident_id} a été modifié.

Incident: {incident_title}
Ancien statut: {old_status}
Nouveau statut: {new_status}
Modifié par: {changed_by}

Connectez-vous à SIRP pour plus de détails.

---
SIRP - Secure Incident Reporting Platform
Ceci est un message automatique, merci de ne pas répondre.
        """

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .status {{ display: inline-block; padding: 5px 10px; border-radius: 4px; font-weight: bold; }}
        .status-open {{ background-color: #3498db; color: white; }}
        .status-in_progress {{ background-color: #f39c12; color: white; }}
        .status-resolved {{ background-color: #27ae60; color: white; }}
        .status-closed {{ background-color: #95a5a6; color: white; }}
        .footer {{ padding: 10px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SIRP Notification</h1>
        </div>
        <div class="content">
            <p>Bonjour <strong>{recipient_name}</strong>,</p>
            <p>Le statut de l'incident <strong>#{incident_id}</strong> a été modifié.</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Incident</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{incident_title}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Ancien statut</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <span class="status status-{old_status}">{old_status.upper()}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Nouveau statut</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <span class="status status-{new_status}">{new_status.upper()}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Modifié par</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{changed_by}</td>
                </tr>
            </table>

            <p>Connectez-vous à SIRP pour plus de détails.</p>
        </div>
        <div class="footer">
            <p>SIRP - Secure Incident Reporting Platform<br>
            Ceci est un message automatique, merci de ne pas répondre.</p>
        </div>
    </div>
</body>
</html>
        """

        return NotificationService.send_email(
            to_email=recipient_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text
        )

    @staticmethod
    def notify_incident_assigned(
        incident_id: int,
        incident_title: str,
        assigned_by: str,
        recipient_email: str,
        recipient_name: str
    ) -> bool:
        """Notifie un utilisateur qu'un incident lui a été assigné"""

        subject = f"[SIRP] Incident #{incident_id} vous a été assigné"

        body_text = f"""
Bonjour {recipient_name},

L'incident #{incident_id} vous a été assigné.

Incident: {incident_title}
Assigné par: {assigned_by}

Connectez-vous à SIRP pour prendre en charge cet incident.

---
SIRP - Secure Incident Reporting Platform
        """

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .alert {{ background-color: #3498db; color: white; padding: 15px; border-radius: 4px; margin: 20px 0; }}
        .footer {{ padding: 10px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SIRP Notification</h1>
        </div>
        <div class="content">
            <p>Bonjour <strong>{recipient_name}</strong>,</p>

            <div class="alert">
                L'incident <strong>#{incident_id}</strong> vous a été assigné.
            </div>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Incident</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{incident_title}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Assigné par</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{assigned_by}</td>
                </tr>
            </table>

            <p>Connectez-vous à SIRP pour prendre en charge cet incident.</p>
        </div>
        <div class="footer">
            <p>SIRP - Secure Incident Reporting Platform<br>
            Ceci est un message automatique, merci de ne pas répondre.</p>
        </div>
    </div>
</body>
</html>
        """

        return NotificationService.send_email(
            to_email=recipient_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text
        )

    @staticmethod
    def notify_incident_created(
        incident_id: int,
        incident_title: str,
        severity: str,
        created_by: str,
        recipient_emails: List[str]
    ) -> int:
        """
        Notifie les analystes de la création d'un incident critique/high.
        Retourne le nombre d'emails envoyés avec succès.
        """
        if severity not in ["critical", "high"]:
            return 0

        subject = f"[SIRP] ⚠️ Nouvel incident {severity.upper()}: #{incident_id}"

        body_text = f"""
ALERTE - Nouvel incident {severity.upper()}

Incident #{incident_id}: {incident_title}
Sévérité: {severity}
Créé par: {created_by}

Connectez-vous à SIRP pour prendre en charge cet incident.

---
SIRP - Secure Incident Reporting Platform
        """

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #c0392b; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .severity-critical {{ background-color: #c0392b; color: white; padding: 10px; border-radius: 4px; }}
        .severity-high {{ background-color: #e74c3c; color: white; padding: 10px; border-radius: 4px; }}
        .footer {{ padding: 10px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ ALERTE SIRP</h1>
        </div>
        <div class="content">
            <div class="severity-{severity}">
                <strong>Nouvel incident {severity.upper()}</strong>
            </div>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>ID</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">#{incident_id}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Titre</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{incident_title}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Créé par</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{created_by}</td>
                </tr>
            </table>

            <p><strong>Connectez-vous à SIRP pour prendre en charge cet incident.</strong></p>
        </div>
        <div class="footer">
            <p>SIRP - Secure Incident Reporting Platform</p>
        </div>
    </div>
</body>
</html>
        """

        success_count = 0
        for email in recipient_emails:
            if NotificationService.send_email(email, subject, body_html, body_text):
                success_count += 1

        return success_count

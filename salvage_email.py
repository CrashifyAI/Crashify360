"""
Crashify360 - Enhanced Salvage Email Module
Send salvage requests with proper templates based on loss type
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional, Any
from datetime import datetime
import config
from logger import get_logger

logger = get_logger()

class EmailError(Exception):
    """Custom email error"""
    pass

def generate_salvage_email_body(vehicle_info: Dict[str, Any],
                                policy_value: float,
                                loss_type: str = "client",
                                additional_info: Optional[str] = None) -> str:
    """
    Generate salvage request email body
    
    Args:
        vehicle_info: Dictionary with vehicle details
        policy_value: Vehicle policy value
        loss_type: 'client' or 'third_party'
        additional_info: Optional additional information
    
    Returns:
        Formatted email body
    """
    tender_type = "Firm Buy Tender (Third Party)" if loss_type == "third_party" else "Standard Salvage (Client)"
    
    email_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #FF4B4B; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .info-table th {{ background-color: #f4f4f4; text-align: left; padding: 10px; border: 1px solid #ddd; }}
        .info-table td {{ padding: 10px; border: 1px solid #ddd; }}
        .tender-type {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚗 Crashify360 Salvage Request</h1>
    </div>
    
    <div class="content">
        <p>Dear Salvage Partner,</p>
        
        <p>We are requesting a salvage valuation for the following vehicle that has been declared a total loss:</p>
        
        <div class="tender-type">
            <strong>Tender Type:</strong> {tender_type}
        </div>
        
        <table class="info-table">
            <tr>
                <th>Field</th>
                <th>Value</th>
            </tr>
            <tr>
                <td><strong>VIN</strong></td>
                <td>{vehicle_info.get('vin', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Year</strong></td>
                <td>{vehicle_info.get('year', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Make</strong></td>
                <td>{vehicle_info.get('make', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Model</strong></td>
                <td>{vehicle_info.get('model', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Variant</strong></td>
                <td>{vehicle_info.get('variant', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Odometer</strong></td>
                <td>{vehicle_info.get('odometer', 'N/A')} km</td>
            </tr>
            <tr>
                <td><strong>Policy Value</strong></td>
                <td>${policy_value:,.2f}</td>
            </tr>
            <tr>
                <td><strong>Location</strong></td>
                <td>{vehicle_info.get('location', 'TBA')}</td>
            </tr>
        </table>
        
        <h3>Request Details</h3>
        <p><strong>Loss Type:</strong> {config.LOSS_TYPES.get(loss_type, loss_type)}</p>
        <p><strong>Date Requested:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        {f'<p><strong>Additional Information:</strong><br>{additional_info}</p>' if additional_info else ''}
        
        <h3>Required Information</h3>
        <p>Please provide your salvage offer including:</p>
        <ul>
            <li>Salvage value offer</li>
            <li>Collection arrangements</li>
            <li>Payment terms</li>
            <li>Any conditions or exclusions</li>
        </ul>
        
        <p>Photos are attached for your assessment.</p>
        
        <h3>Response Required</h3>
        <p>Please respond within <strong>48 hours</strong> with your offer.</p>
        
        <p>Thank you for your prompt attention to this matter.</p>
        
        <p>Best regards,<br>
        <strong>Crashify360 Team</strong></p>
    </div>
    
    <div class="footer">
        <p>This is an automated message from Crashify360 Total Loss Evaluation System</p>
        <p>For queries, please contact your claims handler</p>
    </div>
</body>
</html>
"""
    
    return email_body

def send_salvage_request(to_email: str,
                        vehicle_info: Dict[str, Any],
                        policy_value: float,
                        loss_type: str = "client",
                        photos: Optional[List[str]] = None,
                        additional_info: Optional[str] = None,
                        cc_emails: Optional[List[str]] = None) -> bool:
    """
    Send salvage request email
    
    Args:
        to_email: Recipient email address
        vehicle_info: Dictionary with vehicle details
        policy_value: Vehicle policy value
        loss_type: 'client' or 'third_party'
        photos: List of photo file paths to attach
        additional_info: Optional additional information
        cc_emails: Optional list of CC email addresses
    
    Returns:
        True if email sent successfully
    
    Raises:
        EmailError: If email fails to send
    """
    try:
        # Validate configuration
        if not config.EMAIL_CONFIG['user'] or not config.EMAIL_CONFIG['password']:
            raise EmailError("Email credentials not configured")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = config.EMAIL_CONFIG['user']
        msg['To'] = to_email
        msg['Subject'] = f"Salvage Request - {vehicle_info.get('year', '')} {vehicle_info.get('make', '')} {vehicle_info.get('model', '')} - VIN: {vehicle_info.get('vin', '')}"
        
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        
        # Generate email body
        html_body = generate_salvage_email_body(
            vehicle_info=vehicle_info,
            policy_value=policy_value,
            loss_type=loss_type,
            additional_info=additional_info
        )
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach photos if provided
        if photos:
            for photo_path in photos:
                try:
                    with open(photo_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {photo_path.split("/")[-1]}'
                        )
                        msg.attach(part)
                except FileNotFoundError:
                    logger.warning(f"Photo not found: {photo_path}")
        
        # Send email
        with smtplib.SMTP(config.EMAIL_CONFIG['smtp_server'], 
                         config.EMAIL_CONFIG['smtp_port']) as server:
            if config.EMAIL_CONFIG['use_tls']:
                server.starttls()
            
            server.login(config.EMAIL_CONFIG['user'], 
                        config.EMAIL_CONFIG['password'])
            
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            
            server.sendmail(
                config.EMAIL_CONFIG['user'],
                recipients,
                msg.as_string()
            )
        
        # Log success
        logger.log_salvage_request(
            vin=vehicle_info.get('vin', 'UNKNOWN'),
            email_to=to_email,
            loss_type=loss_type
        )
        
        logger.info(f"Salvage request email sent successfully to {to_email}",
                   vin=vehicle_info.get('vin'))
        
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error("Email authentication failed", error=e)
        raise EmailError("Email authentication failed. Check credentials.")
    
    except smtplib.SMTPException as e:
        logger.error("SMTP error occurred", error=e)
        raise EmailError(f"Failed to send email: {str(e)}")
    
    except Exception as e:
        logger.error("Unexpected error sending email", error=e)
        raise EmailError(f"Unexpected error: {str(e)}")

def send_bulk_salvage_requests(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Send multiple salvage requests
    
    Args:
        requests: List of salvage request dictionaries
    
    Returns:
        Dictionary with success/failure counts and details
    """
    results = {
        "total": len(requests),
        "successful": 0,
        "failed": 0,
        "details": []
    }
    
    for request in requests:
        try:
            success = send_salvage_request(**request)
            if success:
                results["successful"] += 1
                results["details"].append({
                    "vin": request.get('vehicle_info', {}).get('vin'),
                    "status": "success"
                })
        except EmailError as e:
            results["failed"] += 1
            results["details"].append({
                "vin": request.get('vehicle_info', {}).get('vin'),
                "status": "failed",
                "error": str(e)
            })
    
    logger.info(f"Bulk salvage requests completed",
               total=results["total"],
               successful=results["successful"],
               failed=results["failed"])
    
    return results

if __name__ == "__main__":
    # Test email generation
    print("Testing Salvage Email Module...")
    
    test_vehicle = {
        "vin": "1HGBH41JXMN109186",
        "year": 2020,
        "make": "Toyota",
        "model": "Camry",
        "variant": "Ascent Sport",
        "odometer": 45000,
        "location": "Sydney, NSW"
    }
    
    print("\n--- Client Loss Email ---")
    client_email = generate_salvage_email_body(test_vehicle, 25000, "client")
    print("Email generated successfully (client)")
    
    print("\n--- Third Party Loss Email ---")
    tp_email = generate_salvage_email_body(test_vehicle, 25000, "third_party")
    print("Email generated successfully (third party)")
    
    print("\n✅ Email template tests complete")


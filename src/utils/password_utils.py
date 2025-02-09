import re
import hashlib
from typing import Tuple

def check_password_complexity(password: str) -> Tuple[bool, str]:
    """
    Check if password meets complexity requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 8:
        return False, "كلمة المرور يجب أن تكون 8 أحرف على الأقل"
        
    if not re.search(r"[A-Z]", password):
        return False, "كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل"
        
    if not re.search(r"[a-z]", password):
        return False, "كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل"
        
    if not re.search(r"\d", password):
        return False, "كلمة المرور يجب أن تحتوي على رقم واحد على الأقل"
        
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل"
        
    return True, "كلمة المرور صالحة"

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify if provided password matches stored hash"""
    return stored_hash == hash_password(provided_password) 
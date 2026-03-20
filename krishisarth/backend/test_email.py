from pydantic import EmailStr, BaseModel

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

try:
    LoginRequest(email='ramesh@krishisarth.test', password='password')
    print("VALID")
except Exception as e:
    print(f"INVALID: {e}")

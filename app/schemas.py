from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field 

class UserCreate(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class NotificationCreate(BaseModel):
    recipient: str = Field(min_length=1)
    message: str = Field(min_length=1)

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int  
    recipient: str
    message: str
    status: str
    created_at: datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import time
import uuid

class PricePoint(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    price: float

class IndicatorValues(BaseModel):
    rsi: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    sma_short: Optional[float] = None
    sma_long: Optional[float] = None

class SentimentData(BaseModel):
    text: str
    sentiment_score: float
    sentiment_label: str # "Positive", "Negative", "Neutral"

class MarketDataResponse(BaseModel):
    asset: str = "BTC/USD"
    current_price: float
    price_history: List[PricePoint]
    trend: str
    indicators: IndicatorValues
    sentiment: SentimentData

class TradeIdea(BaseModel):
    asset: str = "BTC/USD"
    action: str # "BUY", "SELL", "HOLD"
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: str # "High", "Medium", "Low", "None"
    reason: str

class AlertBase(BaseModel):
    price_level: float
    direction: str # "above" or "below"

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset: str = "BTC/USD"
    triggered: bool = False
    created_at: float = Field(default_factory=time.time)
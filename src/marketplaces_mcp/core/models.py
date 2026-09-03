from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ProductResult(BaseModel):
    marketplace: str
    title: str
    url: str
    price: float | None = None
    old_price: float | None = None
    currency: str = Field(default="RUB")
    rating: float | None = None
    reviews_count: int | None = None
    image_url: str | None = None
    availability: str | None = None
    delivery_hint: str | None = None
    seller: str | None = None
    seller_type: str | None = None
    seller_rating: float | None = None
    seller_reviews_count: int | None = None
    condition: str | None = None
    location: str | None = None
    published_at: str | None = None
    views_count: int | None = None
    delivery_available: bool | None = None
    unit_price: float | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float | None = None
    raw: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    query: str
    marketplaces: list[str]
    results: list[ProductResult]
    warnings: list[str] = Field(default_factory=list)
    artifact_id: str | None = None
    tokens_estimate: int | None = None


class ReviewResult(BaseModel):
    marketplace: str
    author: str | None = None
    published_at: str | None = None
    rating: float | None = None
    text: str
    variant: str | None = None
    confidence: float = 0.7


class ReviewsResponse(BaseModel):
    url: str
    marketplace: str
    total_reviews: int | None = None
    rating: float | None = None
    reviews: list[ReviewResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_id: str | None = None


class OfferGroup(BaseModel):
    canonical_title: str
    offers: list[ProductResult]
    confidence: float = 0.0


class CompareResponse(BaseModel):
    query: str
    groups: list[OfferGroup]
    best_offers: list[ProductResult]
    warnings: list[str] = Field(default_factory=list)
    artifact_id: str | None = None


class FlightSegment(BaseModel):
    origin: str | None = None
    destination: str | None = None
    departure_at: str | None = None
    arrival_at: str | None = None
    airline: str | None = None
    flight_number: str | None = None
    duration_minutes: int | None = None
    cabin_class: str | None = None
    baggage: str | None = None


class FlightOffer(BaseModel):
    provider: str = "ozon_travel"
    url: str
    origin: str
    destination: str
    departure_date: date
    return_date: date | None = None
    price: float | None = None
    currency: str = "RUB"
    airlines: list[str] = Field(default_factory=list)
    segments: list[FlightSegment] = Field(default_factory=list)
    stops: int | None = None
    duration_minutes: int | None = None
    baggage: str | None = None
    refundable: bool | None = None
    exchangeable: bool | None = None
    availability: str | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float | None = None
    raw: dict[str, Any] | None = None


class FlightSearchResponse(BaseModel):
    origin: str
    destination: str
    departure_date: date | None = None
    return_date: date | None = None
    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin_class: str = "economy"
    results: list[FlightOffer] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_url: str
    artifact_id: str | None = None


class HotelRate(BaseModel):
    room_name: str | None = None
    price: float | None = None
    price_per_night: float | None = None
    currency: str = "RUB"
    meal_plan: str | None = None
    cancellation_policy: str | None = None
    payment_terms: str | None = None
    refundable: bool | None = None
    availability: str | None = None


class HotelOffer(BaseModel):
    provider: str = "ozon_travel"
    title: str
    url: str
    destination: str
    check_in: date
    check_out: date
    nights: int
    total_price: float | None = None
    nightly_price: float | None = None
    currency: str = "RUB"
    stars: int | None = None
    rating: float | None = None
    reviews_count: int | None = None
    address: str | None = None
    distance_to_center: str | None = None
    amenities: list[str] = Field(default_factory=list)
    rates: list[HotelRate] = Field(default_factory=list)
    availability: str | None = None
    image_url: str | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float | None = None
    raw: dict[str, Any] | None = None


class HotelSearchResponse(BaseModel):
    destination: str
    check_in: date | None = None
    check_out: date | None = None
    nights: int | None = None
    adults: int = 2
    rooms: int = 1
    results: list[HotelOffer] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_url: str
    artifact_id: str | None = None

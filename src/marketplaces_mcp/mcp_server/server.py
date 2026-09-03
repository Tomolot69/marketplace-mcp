from __future__ import annotations

from datetime import date

from mcp.server.fastmcp import FastMCP

from marketplaces_mcp.adapters import (
    AvitoAdapter,
    OzonAdapter,
    OzonTravelAdapter,
    WildberriesAdapter,
    YandexMarketAdapter,
)
from marketplaces_mcp.core.artifacts import create_artifact, read_artifact
from marketplaces_mcp.core.config import get_settings
from marketplaces_mcp.core.matching import group_product_results
from marketplaces_mcp.core.models import (
    CompareResponse,
    FlightSearchResponse,
    HotelSearchResponse,
    OfferGroup,
    ProductResult,
    ReviewsResponse,
    SearchResponse,
)
from marketplaces_mcp.core.reviews import fetch_reviews

REQUIRED_TOOLS = [
    "marketplaces_search",
    "ozon_search",
    "wildberries_search",
    "yandex_market_search",
    "avito_search",
    "marketplaces_compare",
    "marketplaces_product_details",
    "marketplaces_product_reviews",
    "marketplaces_get_artifact",
    "ozon_travel_flights_search",
    "ozon_travel_hotels_search",
    "ozon_travel_hotel_details",
]


mcp = FastMCP("marketplaces-mcp")
_settings = get_settings()
_adapters = {
    "ozon": OzonAdapter(_settings),
    "wildberries": WildberriesAdapter(_settings),
    "yandex_market": YandexMarketAdapter(_settings),
    "avito": AvitoAdapter(_settings),
}
_default_marketplaces = ["ozon", "wildberries", "yandex_market"]
_travel_adapter = OzonTravelAdapter(_settings)


def _as_marketplace_list(raw: list[str] | None) -> list[str]:
    if raw is None:
        return list(_default_marketplaces)
    result = []
    for item in raw:
        if item in _adapters:
            result.append(item)
    return result


@mcp.tool()
async def marketplaces_search(
    query: str,
    marketplaces: list[str] | None = None,
    limit: int = 10,
    strategy: str = "auto",
):
    marketplaces = _as_marketplace_list(marketplaces)
    warnings: list[str] = []
    all_results: list[ProductResult] = []
    used_urls: list[str] = []

    for key in marketplaces:
        adapter = _adapters[key]
        results, adapter_warnings, search_url = await adapter.search(
            query=query,
            limit=limit,
            strategy=strategy,
        )
        warnings.extend(adapter_warnings)
        used_urls.append(search_url)
        all_results.extend(results)

    all_results.sort(key=lambda item: (item.price is None, item.price or 0.0))
    all_results = all_results[:limit]

    response = SearchResponse(
        query=query,
        marketplaces=marketplaces,
        results=all_results,
        warnings=sorted(set(warnings)),
        tokens_estimate=_estimate_tokens(query, len(all_results)),
    )
    response.artifact_id = create_artifact(
        {
            "type": "search",
            "query": query,
            "marketplaces": marketplaces,
            "search_urls": used_urls,
            "strategy": strategy,
            "results": [item.model_dump() for item in response.results],
        }
    )

    return response


@mcp.tool()
async def ozon_search(query: str, limit: int = 10, strategy: str = "auto"):
    results, warnings, search_url = await _adapters["ozon"].search(
        query=query, limit=limit, strategy=strategy
    )
    response = SearchResponse(
        query=query,
        marketplaces=["ozon"],
        results=results[:limit],
        warnings=warnings,
    )
    response.artifact_id = create_artifact(
        {
            "type": "search",
            "query": query,
            "marketplaces": ["ozon"],
            "search_urls": [search_url],
            "strategy": strategy,
            "results": [item.model_dump() for item in response.results],
        }
    )
    return response


@mcp.tool()
async def wildberries_search(query: str, limit: int = 10, strategy: str = "auto"):
    results, warnings, search_url = await _adapters["wildberries"].search(
        query=query,
        limit=limit,
        strategy=strategy,
    )
    response = SearchResponse(
        query=query,
        marketplaces=["wildberries"],
        results=results[:limit],
        warnings=sorted(set(warnings)),
    )
    response.artifact_id = create_artifact(
        {
            "type": "search",
            "query": query,
            "marketplaces": ["wildberries"],
            "search_urls": [search_url],
            "strategy": strategy,
            "results": [item.model_dump() for item in response.results],
        }
    )
    return response


@mcp.tool()
async def yandex_market_search(query: str, limit: int = 10, strategy: str = "auto"):
    results, warnings, search_url = await _adapters["yandex_market"].search(
        query=query,
        limit=limit,
        strategy=strategy,
    )
    response = SearchResponse(
        query=query,
        marketplaces=["yandex_market"],
        results=results[:limit],
        warnings=warnings,
    )
    response.artifact_id = create_artifact(
        {
            "type": "search",
            "query": query,
            "marketplaces": ["yandex_market"],
            "search_urls": [search_url],
            "strategy": strategy,
            "results": [item.model_dump() for item in response.results],
        }
    )
    return response


@mcp.tool()
async def avito_search(query: str, limit: int = 10, strategy: str = "auto"):
    results, warnings, search_url = await _adapters["avito"].search(
        query=query,
        limit=limit,
        strategy=strategy,
    )
    response = SearchResponse(
        query=query,
        marketplaces=["avito"],
        results=results[:limit],
        warnings=sorted(set(warnings)),
    )
    response.artifact_id = create_artifact(
        {
            "type": "search",
            "query": query,
            "marketplaces": ["avito"],
            "search_urls": [search_url],
            "strategy": strategy,
            "results": [item.model_dump() for item in response.results],
        }
    )
    return response


@mcp.tool()
async def ozon_travel_flights_search(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    cabin_class: str = "economy",
    direct_only: bool = False,
    sort: str = "price",
    limit: int = 10,
    strategy: str = "auto",
):
    """Search public Ozon Travel flight offers without booking or account actions."""
    results, warnings, source_url = await _travel_adapter.search_flights(
        origin,
        destination,
        departure_date,
        return_date,
        adults=adults,
        children=children,
        infants=infants,
        cabin_class=cabin_class,
        direct_only=direct_only,
        sort=sort,
        limit=limit,
        strategy=strategy,
    )
    response = FlightSearchResponse(
        origin=origin,
        destination=destination,
        departure_date=_safe_date(departure_date),
        return_date=_safe_date(return_date),
        adults=adults,
        children=children,
        infants=infants,
        cabin_class=cabin_class,
        results=results,
        warnings=warnings,
        source_url=source_url,
    )
    response.artifact_id = create_artifact(
        {
            "type": "ozon_travel_flight_search",
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "passengers": {"adults": adults, "children": children, "infants": infants},
            "cabin_class": cabin_class,
            "direct_only": direct_only,
            "sort": sort,
            "strategy": strategy,
            "source_url": source_url,
            "warnings": warnings,
            "results": [item.model_dump(mode="json") for item in results],
        }
    )
    return response


@mcp.tool()
async def ozon_travel_hotels_search(
    destination: str,
    check_in: str,
    check_out: str,
    adults: int = 2,
    rooms: int = 1,
    min_rating: float | None = None,
    stars: list[int] | None = None,
    max_total_price: float | None = None,
    sort: str = "price",
    include_rates: bool = True,
    limit: int = 10,
    strategy: str = "auto",
):
    """Search public Ozon Travel hotels for exact stay dates and guest count."""
    results, warnings, source_url = await _travel_adapter.search_hotels(
        destination,
        check_in,
        check_out,
        adults=adults,
        rooms=rooms,
        min_rating=min_rating,
        stars=stars,
        max_total_price=max_total_price,
        sort=sort,
        include_rates=include_rates,
        limit=limit,
        strategy=strategy,
    )
    parsed_check_in = _safe_date(check_in)
    parsed_check_out = _safe_date(check_out)
    response = HotelSearchResponse(
        destination=destination,
        check_in=parsed_check_in,
        check_out=parsed_check_out,
        nights=_stay_nights(parsed_check_in, parsed_check_out),
        adults=adults,
        rooms=rooms,
        results=results,
        warnings=warnings,
        source_url=source_url,
    )
    response.artifact_id = create_artifact(
        {
            "type": "ozon_travel_hotel_search",
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "adults": adults,
            "rooms": rooms,
            "filters": {
                "min_rating": min_rating,
                "stars": stars,
                "max_total_price": max_total_price,
                "sort": sort,
            },
            "strategy": strategy,
            "source_url": source_url,
            "warnings": warnings,
            "results": [item.model_dump(mode="json") for item in results],
        }
    )
    return response


@mcp.tool()
async def ozon_travel_hotel_details(
    url: str,
    destination: str,
    check_in: str,
    check_out: str,
    adults: int = 2,
    rooms: int = 1,
    strategy: str = "auto",
):
    """Read one public Ozon Travel hotel page with rates for exact dates."""
    hotel, warnings = await _travel_adapter.hotel_details(
        url,
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        rooms=rooms,
        strategy=strategy,
    )
    parsed_check_in = _safe_date(check_in)
    parsed_check_out = _safe_date(check_out)
    response = HotelSearchResponse(
        destination=destination,
        check_in=parsed_check_in,
        check_out=parsed_check_out,
        nights=_stay_nights(parsed_check_in, parsed_check_out),
        adults=adults,
        rooms=rooms,
        results=[hotel] if hotel else [],
        warnings=warnings,
        source_url=url,
    )
    response.artifact_id = create_artifact(
        {
            "type": "ozon_travel_hotel_details",
            "url": url,
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "adults": adults,
            "rooms": rooms,
            "strategy": strategy,
            "warnings": warnings,
            "result": hotel.model_dump(mode="json") if hotel else None,
        }
    )
    return response


@mcp.tool()
async def marketplaces_compare(
    query: str,
    limit_per_marketplace: int = 10,
    strategy: str = "auto",
    include_avito: bool = False,
):
    warnings: list[str] = []
    all_results: list[ProductResult] = []
    search_urls: list[str] = []
    adapter_keys = list(_default_marketplaces)
    if include_avito:
        adapter_keys.append("avito")
    for key in adapter_keys:
        adapter = _adapters[key]
        results, adapter_warnings, search_url = await adapter.search(
            query=query,
            limit=limit_per_marketplace,
            strategy=strategy,
        )
        warnings.extend(adapter_warnings)
        search_urls.append(search_url)
        all_results.extend(results)

    groups_internal = group_product_results(all_results, similarity_threshold=0.4)
    groups_for_response: list[OfferGroup] = []
    low_confidence_warnings: list[str] = []

    for index, group in enumerate(groups_internal, start=1):
        offers = sorted(
            group.offers,
            key=lambda item: (item.price is None, item.price or 0.0),
        )
        groups_for_response.append(
            OfferGroup(
                canonical_title=group.canonical_title,
                offers=offers,
                confidence=group.confidence,
            )
        )
        if group.confidence < 0.35 and len(group.offers) > 1:
            low_confidence_warnings.append(f"LOW_CONFIDENCE_GROUP_{index}")

    best_offers = [group.offers[0] for group in groups_for_response if group.offers]
    best_offers.sort(key=lambda item: (item.price is None, item.price or 0.0))

    response = CompareResponse(
        query=query,
        groups=groups_for_response,
        best_offers=best_offers,
        warnings=sorted(set(warnings + low_confidence_warnings)),
    )
    response.artifact_id = create_artifact(
        {
            "type": "compare",
            "query": query,
            "limit_per_marketplace": limit_per_marketplace,
            "strategy": strategy,
            "search_urls": search_urls,
            "groups": [group.model_dump() for group in response.groups],
            "best_offers": [offer.model_dump() for offer in response.best_offers],
        }
    )
    return response


@mcp.tool()
async def marketplaces_product_details(url: str, strategy: str = "auto"):
    marketplace = _detect_marketplace(url)
    if marketplace not in _adapters:
        response = SearchResponse(
            query=url,
            marketplaces=["unknown"],
            results=[],
            warnings=["UNKNOWN_MARKETPLACE"],
        )
        response.artifact_id = create_artifact(
            {
                "type": "product_details",
                "url": url,
                "strategy": strategy,
                "status": "unsupported",
                "warnings": response.warnings,
            }
        )
        return response

    adapter = _adapters[marketplace]
    product, warnings, _ = await adapter.product_details(url=url, strategy=strategy)
    response = SearchResponse(
        query=url,
        marketplaces=[marketplace],
        results=[product] if product else [],
        warnings=warnings or [],
    )
    response.artifact_id = create_artifact(
        {
            "type": "product_details",
            "url": url,
            "marketplace": marketplace,
            "strategy": strategy,
            "result": product.model_dump() if product else None,
        }
    )
    return response


@mcp.tool()
async def marketplaces_product_reviews(url: str, limit: int = 20):
    marketplace = _detect_marketplace(url)
    if marketplace not in _adapters:
        return ReviewsResponse(
            url=url,
            marketplace="unknown",
            warnings=["UNKNOWN_MARKETPLACE"],
        )
    reviews, warnings, review_url, total, rating = await fetch_reviews(
        _adapters[marketplace],
        url,
        max(1, min(limit, 30)),
    )
    response = ReviewsResponse(
        url=review_url,
        marketplace=marketplace,
        total_reviews=total,
        rating=rating,
        reviews=reviews,
        warnings=warnings,
    )
    response.artifact_id = create_artifact(
        {
            "type": "product_reviews",
            "url": review_url,
            "marketplace": marketplace,
            "total_reviews": total,
            "rating": rating,
            "warnings": warnings,
            "reviews": [review.model_dump() for review in reviews],
        }
    )
    return response


@mcp.tool()
async def marketplaces_get_artifact(artifact_id: str, name: str = "content.json"):
    return read_artifact(artifact_id, name=name)


def _detect_marketplace(url: str) -> str:
    lower = url.lower()
    if "ozon.ru" in lower:
        return "ozon"
    if "wildberries.ru" in lower:
        return "wildberries"
    if "market.yandex.ru" in lower or "yandex" in lower:
        return "yandex_market"
    if "avito.ru" in lower:
        return "avito"
    return "unknown"


def _estimate_tokens(query: str, results_count: int) -> int:
    return len(query) + results_count * 15


def _safe_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _stay_nights(check_in: date | None, check_out: date | None) -> int | None:
    if check_in is None or check_out is None:
        return None
    nights = (check_out - check_in).days
    return nights if nights > 0 else None


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

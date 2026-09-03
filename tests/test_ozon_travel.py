from __future__ import annotations

import asyncio
from datetime import date

from marketplaces_mcp.adapters import OzonTravelAdapter

FLIGHT_RESULTS_HTML = """
<html><body>
  <article>
    <div>Победа</div>
    <div>07:35 — 09:05</div>
    <div>Прямой 1ч 30м</div>
    <div>Внуково, Москва — Пулково, Санкт-Петербург</div>
    <div>Без багажа</div>
    <a href="/travel/flight/search/mowled/d2030-05-10">от 2 679 ₽</a>
  </article>
  <article>
    <div>Аэрофлот</div>
    <div>10:20 — 12:00</div>
    <div>Прямой 1ч 40м</div>
    <div>Шереметьево, Москва — Пулково, Санкт-Петербург</div>
    <div>Багаж 23 кг</div>
    <a href="/travel/flight/search/mowled/d2030-05-10">от 4 120 ₽</a>
  </article>
</body></html>
"""


FLIGHT_RESULTS_SNAPSHOT = """
- article:
  - list:
    - listitem: Самый дешёвый
  - text: S7 Airlines В пути 1ч 35м 09:30 – 11:05 Прямой Москва, DME – Санкт-Петербург, LED
  - button "Детали перелета" [e47]
  - text: 23 + 1 959 ₽
  - text: + 52 5 168 ₽ 5 441 ₽
  - button "Выбрать" [e48]
- article:
  - text: Аэрофлот, рейс выполняет Россия В пути 1ч 30м 11:30 – 13:00 Прямой Москва, VKO – Санкт-Петербург, LED
  - button "Детали перелета" [e53]
  - text: Без багажа
  - text: + 61 6 131 ₽ 6 191 ₽
  - button "Выбрать" [e54]
"""


HOTEL_RESULTS_HTML = """
<html><body>
  <article>
    <a href="/travel/hotels/product/hotel-volna-1001/"><h2>Отель Волна, 4*</h2></a>
    <div>Сочи, улица Морская, 1 • 900 м до центра</div>
    <div>4.8 250 отзывов Wi-Fi Парковка Бассейн</div>
    <div>от 5 000 ₽</div>
  </article>
  <article>
    <a href="/travel/hotels/product/hotel-bereg-1002/"><h2>Отель Берег, 3*</h2></a>
    <div>Сочи, улица Южная, 7 • 2.1 км до центра</div>
    <div>4.6 90 отзывов Wi-Fi Кондиционер</div>
    <div>от 3 200 ₽</div>
  </article>
</body></html>
"""


HOTEL_DETAILS_SNAPSHOT = """
- heading "Отель Волна, 4*" [level=1]
- text: 4.8 250 отзывов
- text: Сочи, улица Морская, 1 • 900 м до центра
- text: Wi-Fi Парковка Бассейн Ресторан
- heading "Стандарт с двуспальной кроватью" [level=2]
- text: 9 200 ₽
- text: Завтрак включён Бесплатная отмена до 8 мая Оплата сейчас Остался 1 вариант
- text: Другой тариф: нет мест
- heading "Люкс с видом на море" [level=2]
- text: 14 000 ₽
- text: Без питания Невозвратный тариф Оплата сейчас
"""


HOTEL_DETAILS_WITH_NEARBY_PRICES = """
- heading "Отель Гарден Хиллс by Provence, 3*" [level=1]
- text: Ближайшие доступные даты 3 – 5 октября от 3 100 ₽ Ваши даты 10 – 12 октября от 4 840 ₽
- heading "Эконом двухместный" [level=2]
- text: Двуспальная кровать
- text: от 4 142 ₽ 10 – 12 октября, 2 ночи
- text: 2 гостя
Похожие отели и квартиры рядом на 10 – 12 октября
- text: 2 000 ₽
- link "Чужой соседний отель"
"""


def test_flight_fixture_parsing_and_sorting():
    async def run():
        return await OzonTravelAdapter().search_flights(
            "MOW",
            "LED",
            "2030-05-10",
            adults=2,
            direct_only=True,
            strategy="fixture",
            fixture_html=FLIGHT_RESULTS_HTML,
        )

    results, warnings, source_url = asyncio.run(run())

    assert warnings == []
    assert source_url == (
        "https://www.ozon.ru/travel/flight/search?Children=0&Dlts=2&Infants=0"
        "&ServiceClass=ECONOMY&dates=d2030-05-10&route=mowled"
    )
    assert [item.price for item in results] == [2679.0, 4120.0]
    assert results[0].origin == "MOW"
    assert results[0].destination == "LED"
    assert results[0].stops == 0
    assert results[0].duration_minutes == 90
    assert results[0].baggage == "not_included"
    assert results[1].baggage == "Багаж 23 кг"


def test_flight_snapshot_keeps_offer_boundaries_and_public_price():
    results = OzonTravelAdapter().parse_flight_results(
        FLIGHT_RESULTS_SNAPSHOT,
        source_url="https://www.ozon.ru/travel/flight/search?route=mowled",
        origin="MOW",
        destination="LED",
        departure_date=date(2030, 5, 10),
        return_date=None,
    )

    assert [item.price for item in results] == [5441.0, 6191.0]
    assert results[0].airlines == ["S7 Airlines"]
    assert results[0].duration_minutes == 95
    assert results[0].stops == 0
    assert results[1].airlines == ["Аэрофлот"]
    assert results[1].baggage == "not_included"


def test_flight_camofox_loading_marker_is_polled():
    adapter = OzonTravelAdapter()

    assert adapter.camofox_snapshot_attempts == 6
    assert adapter._camofox_snapshot_pending("- paragraph: Получаем расписание рейсов")
    assert not adapter._camofox_snapshot_pending("- article:\n  - text: S7 Airlines")


def test_hotel_search_keeps_nightly_and_total_prices_separate():
    async def run():
        return await OzonTravelAdapter().search_hotels(
            "Сочи",
            "2030-05-10",
            "2030-05-12",
            sort="price",
            include_rates=False,
            strategy="fixture",
            fixture_html=HOTEL_RESULTS_HTML,
        )

    results, warnings, source_url = asyncio.run(run())

    assert warnings == []
    assert "checkIn=2030-05-10" in source_url
    assert [item.title for item in results] == ["Отель Берег, 3*", "Отель Волна, 4*"]
    assert results[0].total_price is None
    assert results[0].nightly_price == 3200.0
    assert results[0].nights == 2
    assert results[0].stars == 3
    assert results[0].rating == 4.6
    assert results[0].reviews_count == 90


def test_hotel_details_extracts_dated_rates_and_lowest_total():
    async def run():
        return await OzonTravelAdapter().hotel_details(
            "https://www.ozon.ru/travel/hotels/product/hotel-volna-1001/",
            destination="Сочи",
            check_in="2030-05-10",
            check_out="2030-05-12",
            strategy="fixture",
            fixture_html=HOTEL_DETAILS_SNAPSHOT,
        )

    hotel, warnings = asyncio.run(run())

    assert warnings == []
    assert hotel is not None
    assert hotel.title == "Отель Волна, 4*"
    assert hotel.check_in == date(2030, 5, 10)
    assert hotel.check_out == date(2030, 5, 12)
    assert hotel.nights == 2
    assert hotel.total_price == 9200.0
    assert hotel.nightly_price == 4600.0
    assert hotel.availability == "available"
    assert len(hotel.rates) == 2
    assert hotel.rates[0].price_per_night == 4600.0
    assert hotel.rates[0].meal_plan is not None
    assert hotel.rates[0].meal_plan.startswith("Завтрак включён")
    assert hotel.rates[0].refundable is True
    assert hotel.rates[1].refundable is False


def test_hotel_details_excludes_nearby_hotels_and_date_carousel_prices():
    hotel = OzonTravelAdapter().parse_hotel_details(
        HOTEL_DETAILS_WITH_NEARBY_PRICES,
        url="https://www.ozon.ru/travel/hotels/product/garden-hills-1001/",
        destination="Сочи",
        check_in=date(2030, 10, 10),
        check_out=date(2030, 10, 12),
    )

    assert hotel is not None
    assert hotel.total_price == 4142.0
    assert len(hotel.rates) == 1
    assert hotel.rates[0].room_name == "Эконом двухместный"


def test_travel_request_validation_is_structured():
    async def run():
        adapter = OzonTravelAdapter()
        bad_flight = await adapter.search_flights(
            "MOW", "LED", "not-a-date", strategy="fixture"
        )
        bad_hotel = await adapter.search_hotels(
            "Сочи", "2030-05-12", "2030-05-10", strategy="fixture"
        )
        return bad_flight, bad_hotel

    bad_flight, bad_hotel = asyncio.run(run())
    assert bad_flight[1] == ["INVALID_DATE_FORMAT"]
    assert bad_hotel[1] == ["CHECK_OUT_NOT_AFTER_CHECK_IN"]


def test_hotel_details_rejects_non_ozon_url_without_loading(monkeypatch):
    async def fail_if_loaded(*_args, **_kwargs):
        raise AssertionError("non-Ozon URL must not be loaded")

    adapter = OzonTravelAdapter()
    monkeypatch.setattr(adapter, "_load_travel_page", fail_if_loaded)

    hotel, warnings = asyncio.run(
        adapter.hotel_details(
            "https://example.com/travel/hotels/product/fake/",
            destination="Сочи",
            check_in="2030-05-10",
            check_out="2030-05-12",
        )
    )

    assert hotel is None
    assert warnings == ["UNSUPPORTED_URL"]


def test_hotel_filter_does_not_treat_missing_dated_price_as_cheap():
    async def run():
        return await OzonTravelAdapter().search_hotels(
            "Сочи",
            "2030-05-10",
            "2030-05-12",
            max_total_price=10000,
            include_rates=False,
            strategy="fixture",
            fixture_html=HOTEL_RESULTS_HTML,
        )

    results, warnings, _ = asyncio.run(run())
    assert results == []
    assert "NO_RESULTS" in warnings

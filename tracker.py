import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from serpapi import GoogleSearch

# Configuration & Credentials
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "YOUR_SERPAPI_KEY_HERE")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "your_email@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "your_app_password")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "recipient@gmail.com")

# Flight Search Parameters
DEPARTURE_AIRPORT = "YYZ"
ARRIVAL_AIRPORT = "YVR"
OUTBOUND_DATE = "2026-10-10"
RETURN_DATE = "2026-10-17"
PRICE_THRESHOLD = 450.00  # Trigger email alert if price drops below this amount (CAD/USD)


def fetch_flight_prices():
    """Queries SerpApi Google Flights engine for updated pricing."""
    params = {
        "engine": "google_flights",
        "departure_id": DEPARTURE_AIRPORT,
        "arrival_id": ARRIVAL_AIRPORT,
        "outbound_date": OUTBOUND_DATE,
        "return_date": RETURN_DATE,
        "currency": "CAD",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    flights_data = []

    # Parse best flights
    best_flights = results.get("best_flights", [])
    for flight in best_flights:
        price = flight.get("price")
        airline = flight["flights"][0].get("airline", "Unknown Airline")
        flights_data.append(
            {
                "type": "Best Flight",
                "price": price,
                "airline": airline,
            }
        )

    # Parse other flights
    other_flights = results.get("other_flights", [])
    for flight in other_flights:
        price = flight.get("price")
        airline = flight["flights"][0].get("airline", "Unknown Airline")
        flights_data.append(
            {
                "type": "Other Flight",
                "price": price,
                "airline": airline,
            }
        )

    return flights_data


def send_email_alert(lowest_price, flight_details):
    """Sends an SMTP email notification when a price drop is detected."""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = (
        f"✈️ Price Alert: Flight to {ARRIVAL_AIRPORT} is down to ${lowest_price}!"
    )

    body = f"""
    Great news! 
    
    A flight matching your criteria ({DEPARTURE_AIRPORT} to {ARRIVAL_AIRPORT}) for dates {OUTBOUND_DATE} to {RETURN_DATE} has dropped below your threshold of ${PRICE_THRESHOLD:.2f}.
    
    Lowest Price Found: ${lowest_price}
    Airline: {flight_details.get('airline', 'N/A')}
    
    Check Google Flights now to secure this rate.
    """

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email alert sent successfully.")
    except Exception as e:
        print(f"Failed to send email alert: {e}")


def main():
    print(
        f"Checking flights from {DEPARTURE_AIRPORT} to {ARRIVAL_AIRPORT} ({OUTBOUND_DATE} to {RETURN_DATE})..."
    )
    flights = fetch_flight_prices()

    if not flights:
        print("No flight results found.")
        return

    # Find minimum price flight
    valid_flights = [f for f in flights if f["price"] is not None]
    if not valid_flights:
        print("No priced flights available.")
        return

    cheapest_flight = min(valid_flights, key=lambda x: x["price"])
    lowest_price = cheapest_flight["price"]

    print(f"Cheapest option found: ${lowest_price} ({cheapest_flight['airline']})")

    if lowest_price <= PRICE_THRESHOLD:
        print(
            f"Price (${lowest_price}) is below threshold (${PRICE_THRESHOLD}). Triggering alert..."
        )
        send_email_alert(lowest_price, cheapest_flight)
    else:
        print(
            f"Price (${lowest_price}) is still above threshold (${PRICE_THRESHOLD}). No alert sent."
        )


if __name__ == "__main__":
    main()

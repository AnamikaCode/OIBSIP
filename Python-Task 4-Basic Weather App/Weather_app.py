
import tkinter as tk
from tkinter import messagebox
import requests
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = "20f41b90327d339b974de993dc40436c"

CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


# ============================================================
# GLOBAL VARIABLES
# ============================================================

current_unit = "C"
current_weather_data = None


# ============================================================
# TEMPERATURE CONVERSION
# ============================================================

def celsius_to_fahrenheit(celsius):
    return (celsius * 9 / 5) + 32


# ============================================================
# GET WEATHER ICON
# ============================================================

def get_weather_icon(icon_code):
    try:
        icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"


        response = requests.get(icon_url, timeout=0.2)
        response.raise_for_status()

        image_data = BytesIO(response.content)

        image = Image.open(image_data)
        image = image.resize((80, 80))

        return ImageTk.PhotoImage(image)

    except requests.exceptions.RequestException:
        return None


# ============================================================
# DISPLAY ERROR
# ============================================================

def show_error(message):
    error_label.config(
        text=message,
        fg="red"
    )


# ============================================================
# CLEAR ERROR
# ============================================================

def clear_error():
    error_label.config(text="")


# ============================================================
# GET WEATHER
# ============================================================

def get_weather():
    global current_weather_data

    clear_error()

    city = city_entry.get().strip()

    # Input validation
    if not city:
        show_error("Please enter a city name.")
        return

    try:

        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(
            CURRENT_WEATHER_URL,
            params=params,
            timeout=0.2
        )

        # Invalid API key
        if response.status_code == 401:
            show_error("Invalid API key.")
            return

        # City not found
        if response.status_code == 404:
            show_error("City not found. Please check the city name.")
            return

        response.raise_for_status()

        current_weather_data = response.json()

        # Get data
        city_name = current_weather_data["name"]
        country = current_weather_data["sys"]["country"]

        temperature = current_weather_data["main"]["temp"]
        feels_like = current_weather_data["main"]["feels_like"]

        humidity = current_weather_data["main"]["humidity"]

        weather_description = (
            current_weather_data["weather"][0]["description"]
            .title()
        )

        wind_speed = current_weather_data["wind"]["speed"]

        icon_code = current_weather_data["weather"][0]["icon"]

        # Update city
        city_label.config(
            text=f"{city_name}, {country}"
        )

        # Temperature
        if current_unit == "C":

            temperature_text = f"{temperature:.1f} °C"
            feels_like_text = f"Feels like {feels_like:.1f} °C"

        else:

            fahrenheit = celsius_to_fahrenheit(temperature)
            feels_like_f = celsius_to_fahrenheit(feels_like)

            temperature_text = f"{fahrenheit:.1f} °F"
            feels_like_text = f"Feels like {feels_like_f:.1f} °F"

        temperature_label.config(
            text=temperature_text
        )

        feels_like_label.config(
            text=feels_like_text
        )

        condition_label.config(
            text=f"Condition: {weather_description}"
        )

        humidity_label.config(
            text=f"Humidity: {humidity}%"
        )

        wind_label.config(
            text=f"Wind Speed: {wind_speed} m/s"
        )

        # Weather icon
        icon = get_weather_icon(icon_code)

        if icon:
            weather_icon_label.config(image=icon)
            weather_icon_label.image = icon

        # Forecast
        get_forecast(city)

    except requests.exceptions.Timeout:

        show_error(
            "Request timed out. Please check your internet connection."
        )

    except requests.exceptions.ConnectionError:

        show_error(
            "Network error. Please check your internet connection."
        )

    except requests.exceptions.RequestException as e:

        show_error(
            f"API error: {str(e)}"
        )

    except KeyError:

        show_error(
            "Unexpected response from weather API."
        )

    except Exception as e:

        show_error(
            f"Something went wrong: {str(e)}"
        )


# ============================================================
# GET FORECAST
# ============================================================

def get_forecast(city):

    try:

        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=0.2
        )

        if response.status_code != 200:
            return

        data = response.json()

        forecast_list = data["list"]

        # Clear previous forecast
        for widget in forecast_frame.winfo_children():
            widget.destroy()

        # --------------------------------------------------------
        # CREATE 5 DAY FORECAST
        # --------------------------------------------------------

        daily_data = {}

        for item in forecast_list:

            date = datetime.fromtimestamp(
                item["dt"]
            ).strftime("%Y-%m-%d")

            if date not in daily_data:
                daily_data[date] = item

        # Skip today's date
        dates = list(daily_data.keys())[1:6]

        for date in dates:

            item = daily_data[date]

            temp = item["main"]["temp"]

            description = item["weather"][0]["description"].title()

            icon_code = item["weather"][0]["icon"]

            formatted_date = datetime.strptime(
                date,
                "%Y-%m-%d"
            ).strftime("%a, %d %b")

            # ----------------------------------------------------
            # FORECAST CARD
            # ----------------------------------------------------

            card = tk.Frame(
                forecast_frame,
                bg="white",
                bd=1,
                relief="solid",
                padx=10,
                pady=10
            )

            card.pack(
                side="left",
                padx=5,
                pady=5
            )

            date_label = tk.Label(
                card,
                text=formatted_date,
                bg="white",
                font=("Arial", 10, "bold")
            )

            date_label.pack()

            icon = get_weather_icon(icon_code)

            if icon:

                icon_label = tk.Label(
                    card,
                    image=icon,
                    bg="white"
                )

                icon_label.image = icon

                icon_label.pack()

            if current_unit == "C":

                temp_text = f"{temp:.1f} °C"

            else:

                temp_f = celsius_to_fahrenheit(temp)

                temp_text = f"{temp_f:.1f} °F"

            temp_label = tk.Label(
                card,
                text=temp_text,
                bg="white",
                font=("Arial", 11, "bold")
            )

            temp_label.pack()

            condition = tk.Label(
                card,
                text=description,
                bg="white",
                wraplength=100
            )

            condition.pack()

    except requests.exceptions.RequestException:

        show_error(
            "Unable to load forecast data."
        )

    except Exception:

        show_error(
            "Unable to display forecast."
        )


# ============================================================
# TOGGLE CELSIUS / FAHRENHEIT
# ============================================================

def toggle_unit():

    global current_unit

    if current_unit == "C":

        current_unit = "F"
        unit_button.config(
            text="Switch to °C"
        )

    else:

        current_unit = "C"
        unit_button.config(
            text="Switch to °F"
        )

    # Refresh weather
    if current_weather_data:

        temperature = current_weather_data["main"]["temp"]
        feels_like = current_weather_data["main"]["feels_like"]

        if current_unit == "C":

            temperature_label.config(
                text=f"{temperature:.1f} °C"
            )

            feels_like_label.config(
                text=f"Feels like {feels_like:.1f} °C"
            )

        else:

            temperature_f = celsius_to_fahrenheit(
                temperature
            )

            feels_like_f = celsius_to_fahrenheit(
                feels_like
            )

            temperature_label.config(
                text=f"{temperature_f:.1f} °F"
            )

            feels_like_label.config(
                text=f"Feels like {feels_like_f:.1f} °F"
            )

        # Refresh forecast
        city = city_entry.get().strip()

        if city:
            get_forecast(city)


# ============================================================
# ENTER KEY SUPPORT
# ============================================================

def enter_pressed(event):
    get_weather()


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title("Weather App")

root.geometry("750x700")

root.configure(
    bg="#e8f4f8"
)

root.resizable(
    False,
    False
)


# ============================================================
# TITLE
# ============================================================

title_label = tk.Label(
    root,
    text="Weather App",
    font=("Arial", 28, "bold"),
    bg="#e8f4f8"
)

title_label.pack(
    pady=20
)


# ============================================================
# SEARCH FRAME
# ============================================================

search_frame = tk.Frame(
    root,
    bg="#e8f4f8"
)

search_frame.pack(
    pady=10
)


city_entry = tk.Entry(
    search_frame,
    width=30,
    font=("Arial", 14)
)

city_entry.pack(
    side="left",
    padx=5
)

city_entry.bind(
    "<Return>",
    enter_pressed
)


get_button = tk.Button(
    search_frame,
    text="Get Weather",
    font=("Arial", 12, "bold"),
    command=get_weather
)

get_button.pack(
    side="left",
    padx=5
)


unit_button = tk.Button(
    search_frame,
    text="Switch to °F",
    font=("Arial", 11),
    command=toggle_unit
)

unit_button.pack(
    side="left",
    padx=5
)


# ============================================================
# ERROR LABEL
# ============================================================

error_label = tk.Label(
    root,
    text="",
    bg="#f2f2f2",
    font=("Arial", 11)
)

error_label.pack(
    pady=5
)


# ============================================================
# CURRENT WEATHER FRAME
# ============================================================

weather_frame = tk.Frame(
    root,
    bg="white",
    bd=1,
    relief="solid",
    padx=30,
    pady=20
)

weather_frame.pack(
    padx=30,
    pady=10,
    fill="x"
)


city_label = tk.Label(
    weather_frame,
    text="Enter a city",
    font=("Arial", 22, "bold"),
    bg="white"
)

city_label.pack(
    pady=5
)


weather_icon_label = tk.Label(
    weather_frame,
    bg="white"
)

weather_icon_label.pack()


temperature_label = tk.Label(
    weather_frame,
    text="-- °C",
    font=("Arial", 32, "bold"),
    bg="white"
)

temperature_label.pack()


feels_like_label = tk.Label(
    weather_frame,
    text="",
    font=("Arial", 11),
    bg="white"
)

feels_like_label.pack(
    pady=5
)


condition_label = tk.Label(
    weather_frame,
    text="Condition: --",
    font=("Arial", 13),
    bg="white"
)

condition_label.pack(
    pady=5
)


humidity_label = tk.Label(
    weather_frame,
    text="Humidity: --",
    font=("Arial", 13),
    bg="white"
)

humidity_label.pack(
    pady=5
)


wind_label = tk.Label(
    weather_frame,
    text="Wind Speed: --",
    font=("Arial", 13),
    bg="white"
)

wind_label.pack(
    pady=5
)


# ============================================================
# FORECAST TITLE
# ============================================================

forecast_title = tk.Label(
    root,
    text="5-Day Forecast",
    font=("Arial", 18, "bold"),
    bg="#e8f4f8"
)

forecast_title.pack(
    pady=10
)


# ============================================================
# FORECAST FRAME
# ============================================================

forecast_frame = tk.Frame(
    root,
    bg="#e8f4f8"
)

forecast_frame.pack()


# ============================================================
# START APPLICATION
# ============================================================

root.mainloop()

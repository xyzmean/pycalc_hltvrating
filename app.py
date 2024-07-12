import numpy as np
import json
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, static_url_path='/static', static_folder='templates/static')

# Путь к файлу с данными
DATA_FILE = "data.json"

# Загрузка матриц (замените на ваши файлы)
data_matrix = np.loadtxt("player_stats_matrix.txt", delimiter=",")
ratings_matrix = np.loadtxt("player_ratings_matrix.txt", delimiter=",")
weights = np.loadtxt("player_weights_matrix.txt", delimiter=",")

# Функция для расчета рейтинга
def calculate_rating(player_stats, weights):
    return np.dot(player_stats, weights[:-1]) + weights[-1]

# Функция для конвертации статистики
def convert_stats(kdr, total_kills, total_deaths, damage_per_round, rounds, headshot_percent):
    kills_per_round = total_kills / rounds
    assists_per_round = (total_kills / kdr - total_deaths) / rounds
    headshot_percent = headshot_percent / 100
    return np.array([kdr, damage_per_round, kills_per_round, assists_per_round, headshot_percent])

# Загрузка данных из JSON файла
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение данных в JSON файл
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Главная страница
@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()
    current_username = request.cookies.get("username")

    if request.method == "POST":
        # Обработка формы
        username = request.form["username"] if "username" in request.form else current_username
        kdr = float(request.form["kdr"])
        total_kills = int(request.form["total_kills"])
        total_deaths = int(request.form["total_deaths"])
        damage_per_round = float(request.form["damage_per_round"])
        rounds = int(request.form["rounds"])
        headshot_percent = float(request.form["headshot_percent"])

        # Расчет рейтинга
        user_stats_array = convert_stats(kdr, total_kills, total_deaths, damage_per_round, rounds, headshot_percent)
        rating = calculate_rating(user_stats_array, weights)

        # Сохранение данных пользователя
        if username not in data:
            data[username] = {
                "kdr": [],
                "total_kills": [],
                "total_deaths": [],
                "damage_per_round": [],
                "rounds": [],
                "headshot_percent": [],
                "rating": []
            }
        data[username]["kdr"].append(kdr)
        data[username]["total_kills"].append(total_kills)
        data[username]["total_deaths"].append(total_deaths)
        data[username]["damage_per_round"].append(damage_per_round)
        data[username]["rounds"].append(rounds)
        data[username]["headshot_percent"].append(headshot_percent)
        data[username]["rating"].append(rating)
        save_data(data)

        response = redirect(url_for("index"))
        response.set_cookie("username", username)
        return response

    user_stats = {}
    average_rating = 0
    chart_data = {}

    if current_username and current_username in data:
        user_stats = {
            "Текущий рейтинг": f"{data[current_username]['rating'][-1]:.2f}" if data[current_username]["rating"] else 0,
            "K/D Ratio": data[current_username]["kdr"][-1] if data[current_username]["kdr"] else 0,
            "Всего убийств": data[current_username]["total_kills"][-1] if data[current_username]["total_kills"] else 0,
            "Всего смертей": data[current_username]["total_deaths"][-1] if data[current_username]["total_deaths"] else 0,
            "Урон за раунд": data[current_username]["damage_per_round"][-1] if data[current_username]["damage_per_round"] else 0,
            "Всего раундов": data[current_username]["rounds"][-1] if data[current_username]["rounds"] else 0,
            "Процент хедшотов": data[current_username]["headshot_percent"][-1] if data[current_username]["headshot_percent"] else 0,
        }
        average_rating = f"{np.mean(data[current_username]['rating']):.2f}" if data[current_username]["rating"] else 0
        chart_data = {current_username: data[current_username]}

    return render_template("index.html",
                           chart_data=chart_data,
                           user_stats=user_stats,
                           average_rating=average_rating,
                           current_username=current_username)


@app.route("/change_user", methods=["POST"])
def change_user():
    username = request.form["username"]
    response = redirect(url_for("index"))
    response.set_cookie("username", username)
    return response

if __name__ == "__main__":
    app.run(debug=True)

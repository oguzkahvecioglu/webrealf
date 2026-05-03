import os
import pytz
from flask import Flask, request, jsonify, make_response
from datetime import datetime, timedelta
from flask_cors import CORS
from database_cr import (
    init_db, get_poll, save_poll,
    add_checkin, add_rating,
    get_active_checkins, get_all_active_checkins, get_active_ratings,
    get_recent_poll_vote, add_poll_vote
)

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://69f7a6126e74e0f993bda711--celadon-pastelito-a8822f.netlify.app"
])
init_db()

# ---------------------------------------------------------------------------
# Spot configuration
# ---------------------------------------------------------------------------

SPOTS = {
    "med_a": {
        "capacity": 60, "stay_minutes": 25, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 10, "default": 15
        }
    },
    "med_b": {
        "capacity": 80, "stay_minutes": 25, "rating_minutes": 45,
        "schedule": {
            (8, 9): 20, (9, 11): 30, (11, 13): 65,
            (13, 15): 45, (15, 17): 25, (17, 20): 35, "default": 20
        }
    },
    "med_c": {
        "capacity": 50, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 10, (9, 11): 20, (11, 13): 40,
            (13, 15): 30, (15, 17): 15, (17, 20): 20, "default": 10
        }
    },
    "k_e": {
        "capacity": 120, "stay_minutes": 35, "rating_minutes": 45,
        "schedule": {
            (8, 9): 30, (9, 11): 50, (11, 13): 90,
            (13, 15): 70, (15, 17): 40, (17, 20): 55, "default": 30
        }
    },
    "cajun_corner": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
    "itu_sofra_borek": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
    "seyri_restaurant": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
    "big_slice": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
    "mekansal": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
    "tost_akademisi": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
    "fanfan": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
    "bluff": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
    "selfis_sutis": {
        "capacity": 30, "stay_minutes": 20, "rating_minutes": 45,
        "schedule": {
            (8, 9): 15, (9, 11): 25, (11, 13): 50,
            (13, 15): 35, (15, 17): 20, (17, 20): 30, "default": 15
        }
    },
}

TOTAL_CAMPUS_CAPACITY = 1000
COOLDOWN_MINUTES = 5
FOOD_BAD_MULTIPLIER = 1.2
BAYESIAN_K = 10

# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def get_local_time():
    turkey = pytz.timezone("Europe/Istanbul")
    return datetime.now(turkey)

def get_local_hour():
    return get_local_time().hour

def now_naive():
    """Naive datetime for checkin/rating timestamps."""
    return datetime.utcnow()

# ---------------------------------------------------------------------------
# Poll helpers
# ---------------------------------------------------------------------------

def check_poll_reset():
    now = get_local_time()
    today = now.strftime("%Y-%m-%d")
    hour = now.hour
    poll = get_poll()

    if poll.date != today:
        save_poll({
            "date": today, "last_reset": None,
            "lunch": None, "dinner": None,
            "lunch_good": 0, "lunch_bad": 0,
            "dinner_good": 0, "dinner_bad": 0
        })
        return

    if hour >= 8 and poll.last_reset != "morning":
        save_poll({
            "last_reset": "morning",
            "lunch": None, "dinner": None,
            "lunch_good": 0, "lunch_bad": 0,
            "dinner_good": 0, "dinner_bad": 0
        })

    elif hour >= 15 and poll.last_reset == "morning":
        save_poll({
            "last_reset": "afternoon",
            "dinner": None,
            "dinner_good": 0, "dinner_bad": 0
        })

def get_food_multiplier():
    hour = get_local_hour()
    if hour >= 21:
        return 1.0
    poll = get_poll()
    if 11 <= hour < 21 and poll.lunch == False:
        return FOOD_BAD_MULTIPLIER
    if 17 <= hour < 21 and poll.dinner == False:
        return FOOD_BAD_MULTIPLIER
    return 1.0

# ---------------------------------------------------------------------------
# Schedule baseline
# ---------------------------------------------------------------------------

def get_baseline(schedule):
    hour = get_local_hour()
    for key, value in schedule.items():
        if isinstance(key, tuple):
            start, end = key
            if start <= hour < end:
                return value
    return schedule["default"]

# ---------------------------------------------------------------------------
# Bayesian crowd estimator
#
# conf = c / (c + k)  ->  0 when no data, approaches 1 as checkins grow
# result blends: conf * (observed estimate) + (1 - conf) * baseline
# k=10 means ~10 checkins shifts weight from baseline toward real data
# ---------------------------------------------------------------------------

def crowd_rate(count, adoption, capacity, baseline, k=BAYESIAN_K):
    adoption = max(adoption, 0.05)              # floor: never assume <5% adoption
    estimated = count / adoption                # scale checkins to real people
    estimated = min(estimated, capacity * 1.5)  # cap at 150% to prevent explosion

    conf = count / (count + k)                  # confidence weight 0..1
    crowd = conf * estimated + (1 - conf) * baseline  # bayesian blend
    return round(min(crowd / capacity, 1.0), 2)

def get_label(crowding):
    if crowding < 0.3:
        return "quiet"
    elif crowding < 0.6:
        return "moderate"
    elif crowding < 0.85:
        return "busy"
    else:
        return "almost full"

# ---------------------------------------------------------------------------
# Cooldown helpers — shared between /checkin and /rate
# ---------------------------------------------------------------------------

def check_cooldown():
    """Returns (blocked, seconds_left). blocked=True means reject the request."""
    last_action = request.cookies.get("last_action")
    if not last_action:
        return False, 0
    try:
        last_time = datetime.fromisoformat(last_action)
        diff = timedelta(minutes=COOLDOWN_MINUTES) - (now_naive() - last_time)
        if diff.total_seconds() > 0:
            return True, int(diff.total_seconds())
    except ValueError:
        pass  # corrupted cookie — let them through
    return False, 0

def make_cooldown_response(data):
    """Builds a response and stamps the cooldown cookie."""
    response = make_response(jsonify(data))
    response.set_cookie(
        "last_action",
        now_naive().isoformat(),
        max_age=COOLDOWN_MINUTES * 60,
        samesite="None",
        secure=False
    )
    return response

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/checkin", methods=["POST"])
def checkin():
    spot = request.json.get("spot")
    if spot not in SPOTS:
        return jsonify({"error": "unknown spot"}), 400

    blocked, seconds_left = check_cooldown()
    if blocked:
        return jsonify({"error": "cooldown", "wait_seconds": seconds_left}), 429

    add_checkin(spot)
    return make_cooldown_response({"status": "ok"})


@app.route("/rate", methods=["POST"])
def rate():
    spot = request.json.get("spot")
    score = request.json.get("score")

    if spot not in SPOTS:
        return jsonify({"error": "unknown spot"}), 400
    if not isinstance(score, (int, float)) or not (1 <= score <= 10):
        return jsonify({"error": "score must be between 1 and 10"}), 400

    blocked, seconds_left = check_cooldown()
    if blocked:
        return jsonify({"error": "cooldown", "wait_seconds": seconds_left}), 429

    add_rating(spot, score)
    return make_cooldown_response({"status": "ok"})


@app.route("/poll/vote", methods=["POST"])
def poll_vote():
    check_poll_reset()
    meal = request.json.get("meal")
    vote = request.json.get("vote")

    if meal not in ("lunch", "dinner"):
        return jsonify({"error": "meal must be lunch or dinner"}), 400
    if vote not in ("good", "bad"):
        return jsonify({"error": "vote must be good or bad"}), 400

    hour = get_local_hour()
    if meal == "lunch" and not (8 <= hour < 14):
        return jsonify({"error": "lunch voting closed"}), 400
    if meal == "dinner" and not (15 <= hour < 20):
        return jsonify({"error": "dinner voting closed"}), 400

    poll = get_poll()
    voter_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if voter_ip:
        voter_ip = voter_ip.split(",")[0].strip()

    if get_recent_poll_vote(meal, voter_ip):
        return jsonify({"error": "voted recently", "wait": True}), 429

    good = getattr(poll, f"{meal}_good")
    bad  = getattr(poll, f"{meal}_bad")

    if vote == "good":
        good += 1
    else:
        bad += 1

    total = good + bad
    # good food if less than 40% of votes say bad
    outcome = (bad / total) < 0.4 if total > 0 else None

    save_poll({
        f"{meal}_good": good,
        f"{meal}_bad":  bad,
        meal: outcome
    })

    add_poll_vote(meal, voter_ip)

    response = make_response(jsonify({"status": "ok", "outcome": outcome}))
    return response


def calc_percentages(good, bad):
    total = good + bad
    if total == 0:
        return None
    return {
        "good_pct": round((good / total) * 100),
        "bad_pct":  round((bad  / total) * 100),
        "total":    total
    }

@app.route("/poll/status", methods=["GET"])
def poll_status():
    check_poll_reset()
    poll = get_poll()
    hour = get_local_hour()

    voter_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if voter_ip:
        voter_ip = voter_ip.split(",")[0].strip()

    return jsonify({
        "lunch":              poll.lunch,
        "dinner":             poll.dinner,
        "lunch_stats":        calc_percentages(poll.lunch_good,  poll.lunch_bad),
        "dinner_stats":       calc_percentages(poll.dinner_good, poll.dinner_bad),
        "lunch_open":         8  <= hour < 14,
        "dinner_open":        15 <= hour < 20,
        "food_effect_active": get_food_multiplier() > 1.0,
        "voted_lunch":        get_recent_poll_vote("lunch",  voter_ip),
        "voted_dinner":       get_recent_poll_vote("dinner", voter_ip)
    })


@app.route("/status", methods=["GET"])
def status():
    now = now_naive()
    result = {}

    # Campus-wide adoption rate: sum all active checkins / total campus capacity
    earliest_cutoff = now - timedelta(minutes=max(
        cfg["stay_minutes"] for cfg in SPOTS.values()
    ))
    all_active = get_all_active_checkins(earliest_cutoff)
    adoption = max(len(all_active) / TOTAL_CAMPUS_CAPACITY, 1e-6)
    adoption = min(adoption, 1.0)

    for spot_id, config in SPOTS.items():
        cutoff = now - timedelta(minutes=config["stay_minutes"])
        active = get_active_checkins(spot_id, cutoff)
        count  = len(active)

        baseline = get_baseline(config["schedule"]) * get_food_multiplier()
        crowding = crowd_rate(count, adoption, config["capacity"], baseline)

        rating_cutoff  = now - timedelta(minutes=config["rating_minutes"])
        active_ratings = get_active_ratings(spot_id, rating_cutoff)

        if active_ratings:
            avg_rating   = round(sum(r.score for r in active_ratings) / len(active_ratings), 1)
            rating_count = len(active_ratings)
        else:
            avg_rating   = None
            rating_count = 0

        result[spot_id] = {
            "count":        count,
            "capacity":     config["capacity"],
            "crowding":     crowding,
            "label":        get_label(crowding),
            "avg_rating":   avg_rating,
            "rating_count": rating_count
        }

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)









#to run the code 
#python app.py

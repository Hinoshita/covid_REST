from flask import render_template, request, jsonify, redirect, url_for
from covid import app, db, bcrypt
import json
import requests
from covid.forms import RegistrationForm, LoginForm
from covid.models import Favorite, User
from flask_login import login_user, logout_user, current_user, login_required


def create_country_summary(x, summary_json):
	countries_summary = summary_json["Countries"]
	for country in countries_summary:
		if country["Slug"] == x.slug:
			country_summary = {"Country":country["Country"],
								"Date":country["Date"],
								"NewConfirmed":country["NewConfirmed"],
								"NewDeaths":country["NewDeaths"],
								"NewRecovered":country["NewRecovered"],
								"Slug":country["Slug"],
								"TotalConfirmed":country["TotalConfirmed"],
								"TotalDeaths":country["TotalDeaths"],
								"TotalRecovered":country["TotalRecovered"],
								"WatchLevel":x.watchlevel}
			break
	return country_summary


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET"])
def register():
	if current_user.is_authenticated:
		return redirect(url_for("home"))

	form = RegistrationForm()
	return render_template("register.html", form=form)


@app.route("/register", methods=["POST"])
def create_user():
	form = RegistrationForm()
	print("test")
	hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
	user = User(username=form.username.data, password=hashed_password)
	db.session.add(user)
	db.session.commit()
	return redirect(url_for("login"))


@app.route("/login", methods=["GET"])
def login():
	if current_user.is_authenticated:
		return redirect(url_for("home"))
	form = LoginForm()
	return render_template("login.html", form=form)


@app.route("/login", methods=["POST"])
def login_post():
	form = LoginForm()
	user = User.query.filter_by(username=form.username.data).first()
	if user and bcrypt.check_password_hash(user.password, form.password.data):
		login_user(user)
		return redirect(url_for("home"))
	else:
		return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))    


@app.route('/global', methods=['GET'])
def get_global():
	resp = requests.get("https://api.covid19api.com/summary")
	if resp.ok:
		summary_json = resp.json()
		global_summary = summary_json["Global"]
		return global_summary
	else:
		return resp.reason


@app.route('/all', methods=['GET'])
def get_all():
	resp = requests.get("https://api.covid19api.com/summary")
	if resp.ok:
		summary_json = resp.json()
		countries_summary = summary_json["Countries"]
		
		for country_summary in countries_summary:
			del country_summary["CountryCode"], country_summary["ID"], country_summary["Premium"]
		return jsonify(countries_summary)
	else:
		return resp.reason


@app.route('/favorite', methods=['GET'])
@login_required
def get_favorite():
	favorite_countries = Favorite.query.filter_by(favorite_user=current_user).all()
	print(favorite_countries)
	if len(favorite_countries) == 0:
		return jsonify({"message": "no favorite country registered"})

	resp = requests.get("https://api.covid19api.com/summary")
	if resp.ok:
		summary_json = resp.json()
		favorite_summary = []
		for favorite_country in favorite_countries:
			favorite_country_summary = create_country_summary(favorite_country, summary_json)
			favorite_summary.append(favorite_country_summary)
		return jsonify(favorite_summary)
	else:
		return resp.reason


@app.route('/favorite', methods=['POST'])
@login_required
def create_favorite():
	if not request.json or not 'Slug' in request.json:
		return jsonify({'error':'the slug of the country is needed'}), 400

	resp = requests.get("https://api.covid19api.com/summary")
	if resp.ok:
		summary_json = resp.json()
		countries_summary = summary_json["Countries"]
		slug_list = [country["Slug"] for country in countries_summary]
		if request.json["Slug"] not in slug_list:
			return jsonify({'error':'invalid slug'}), 400
		elif request.json["Slug"] in [favorite.slug for favorite in Favorite.query.filter_by(favorite_user=current_user).all()]:
			return jsonify({'error':'this country is already registered'}), 400	
		elif request.json["WatchLevel"] not in ["high", "middle", "low"]:
			return jsonify({'error':'WatchList must be "high", "middle" or "low"'}), 400		
		else: 
			new_favorite = Favorite(slug=request.json["Slug"], watchlevel=request.json["WatchLevel"], favorite_user=current_user)
			db.session.add(new_favorite)
			db.session.commit()
			return jsonify({'message': '{} is added to your favorite countries'.format(request.json["Slug"])}), 201

	else:
		return resp.reason


@app.route('/favorite/<country>', methods=['GET'])
@login_required
def get_favorite_country(country):
	if country not in [favorite.slug for favorite in Favorite.query.filter_by(favorite_user=current_user).all()]:
		return jsonify({'error':'no such country in your favorite countries'}), 400

	resp = requests.get("https://api.covid19api.com/summary")
	if resp.ok:
		summary_json = resp.json()
		favorite_country = Favorite.query.filter_by(favorite_user=current_user).filter_by(slug=country).first()
		favorite_country_summary = create_country_summary(favorite_country, summary_json)
		return jsonify(favorite_country_summary)
	else:
		return resp.reason


@app.route('/favorite/<country>', methods=['PUT'])
@login_required
def change_watchlevel(country):
	if not request.json or not 'WatchLevel' in request.json:
		return jsonify({'error':'new WatchLevel is needed'}), 400
	if request.json["WatchLevel"] not in ["high", "middle", "low"]:
		return jsonify({'error':'WatchList must be "high", "middle" or "low"'}), 400

	favorite_country = Favorite.query.filter_by(favorite_user=current_user).filter_by(slug=country).first()
	favorite_country.watchlevel = request.json["WatchLevel"]
	db.session.commit()
	return jsonify({'message': 'the WatchLevel of {} is updated to {}'.format(country, request.json["WatchLevel"])}), 200


@app.route('/favorite/<country>', methods=['DELETE'])
@login_required
def delete_favorite_country(country):
	if country not in [favorite.slug for favorite in Favorite.query.filter_by(favorite_user=current_user).all()]:
		return jsonify({'error':'no such country in your favorite countries'}), 400
	Favorite.query.filter_by(favorite_user=current_user).filter_by(slug=country).delete()
	db.session.commit()
	return jsonify({'success': True})


if __name__=="__main__":
    app.run(debug=True)




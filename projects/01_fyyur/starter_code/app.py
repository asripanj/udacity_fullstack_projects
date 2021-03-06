#--------------------------------------------------------------
# Imports.
#--------------------------------------------------------------

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_wtf.csrf import CSRFProtect
from forms import *

#-------------------------------------------------------------
# App Config.
#-------------------------------------------------------------

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# TODO: connect to a local postgresql database DONE 

#--------------------------------------------------------------
# Models.
#--------------------------------------------------------------

class Shows(db.Model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)

  def __repr__(self):
    return f'<Show ID: {self.id}, Venue ID: {self.venue_id}, Artist ID:{self.artist_id}>'

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default = False)
    seeking_description = db.Column(db.String(), nullable=False)
    shows = db.relationship('Shows', backref='venue', lazy="joined") #venue is parent and shows are child

    def __repr__(self):
      return f'<Venue ID: {self.id}, name: {self.name}>'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate DONE
    
class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default = False)
    seeking_description = db.Column(db.String(), nullable=False)
    shows = db.relationship('Shows', backref='artist', lazy="joined") #artist is parent and shows are child

    def __repr__(self):
      return f'<Artist ID: {self.id}, name: {self.name}>'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate DONE

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration. DONE

#------------------------------------------------------------------
# Filters.
#------------------------------------------------------------------

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

# -----------------------------------------------------------------
# Controllers.
# -----------------------------------------------------------------

@app.route('/')
def index():
  return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data. 
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  current_time = datetime.now().strftime('%Y-%m-%d%H:%M:%S')
  data = []
  city_and_state = ''
  venue_query = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()

  for venue in venue_query:
    if city_and_state == venue.city + venue.state:
      data[len(data)-1]["venues"].append({
        "id": venue.id,
        "name": venue.name,
      })
    else:
      city_and_state = venue.city + venue.state
      data.append({
        "city": venue.city,
        "state": venue.state,
        "venues": [{
          "id": venue.id,
          "name": venue.name,
        }]
      })
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.  DONE
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  current_time = datetime.now()
  search = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike("%"+ search + "%")).all()
  data = []

  for venue in venues:
    count = Shows.query.filter_by(venue_id = venue.id).filter(Shows.start_time > current_time).count()
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": count
    })
    response = {
      "count": len(venues),
      "data": data
    }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id DONE
  
  past_shows = db.session.query(Artist, Shows).join(Shows).join(Venue).\
    filter(
      Shows.venue_id == venue_id,
      Shows.artist_id == Artist.id,
      Shows.start_time < datetime.now()
    ).\
    all()

  upcoming_shows = db.session.query(Artist, Shows).join(Shows).join(Venue).\
    filter(
      Shows.venue_id == venue_id,
      Shows.artist_id == Artist.id,
      Shows.start_time > datetime.now()
    ).\
    all()

  venue = Venue.query.filter_by(id=venue_id).first_or_404()

  data = {
    'id': venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    'past_shows': [{
      'artist_id': artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist, show in past_shows],
    'upcoming_shows': [{
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist, show in upcoming_shows],
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead DONEE
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        genres = form.genres.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website = form.website.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )    
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except():
      db.session.rollback()
      flash('An error has occured. Venue' + request.form['name'] + 'could not be listed')
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  # TODO: modify data to be the data object returned from db insertion DONE

  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  # TODO: on unsuccessful db insert, flash an error instead. DONE
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE']) #BONUS NOT NEEDED
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using 
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database DONE
  
  data = []
  artist_query = Artist.query.all()

  for artist in artist_query:
    data.append({
        "id": artist.id,
        "name": artist.name,
      })
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive. DONE
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  current_time = datetime.now()
  search = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike("%"+ search + "%")).all()
  data = []

  for artist in artists:
    count = Shows.query.filter_by(artist_id = artist.id).filter(Shows.start_time > current_time).count()
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": count
    })
    response = {
      "count": len(artists),
      "data": data
    }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id DONE
  # TODO: replace with real venue data from the venues table, using venue_id

  past_shows = db.session.query(Artist, Shows).join(Shows).join(Venue).\
    filter(
      Shows.artist_id == artist_id,
      Shows.venue_id == Venue.id,
      Shows.start_time < datetime.now()
    ).\
    all()

  upcoming_shows = db.session.query(Artist, Shows).join(Shows).join(Venue).\
    filter(
      Shows.artist_id == artist_id,
      Shows.venue_id == Venue.id,
      Shows.start_time > datetime.now()
    ).\
    all()

  artist = Artist.query.filter_by(id=artist_id).first_or_404()

  data = {
    'id': artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "seeking_venue": artist.seeking_venue,
    "image_link": artist.image_link,
    "website": artist.name,
    "facebook_link": artist.facebook_link,
    "seeking_description": artist.seeking_description,
    
    #add
    'past_shows': [{
      'venue_id': venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for venue, show in past_shows],
    'upcoming_shows': [{
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist, show in upcoming_shows],
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET']) #BONUS NOT NEEDED
def edit_artist(artist_id):
  form = ArtistForm()
  
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  
  # TODO: populate form with fields from artist with ID <artist_id> 
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST']) #BONUS NOT NEEDED
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing 
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET']) #BONUS NOT NEEDED
def edit_venue(venue_id):
  form = VenueForm()

  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id> 
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST']) #BONUS NOT NEEDED
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing 
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead DONE
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      artist = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = form.genres.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website = form.website.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except():
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))
  

  # TODO: modify data to be the data object returned from db insertion DONE

  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead. DONE
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data. DONE
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  data = []

  show_query = Shows.query.all()

  for show in show_query:
    artist_query = Artist.query.filter_by(id=show.artist_id).first()
    venue_query = Venue.query.filter_by(id=show.venue_id).first()

    data.append({
        "venue_id": show.venue_id,
        "venue_name": venue_query.name,
        "artist_id": show.artist_id,
        "artist_name": artist_query.name,
        "artist_image_link": artist_query.image_link,
        "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
      })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead DONE
  form = ShowForm(request.form, meta={'csrf': False})
  if form.validate():
    try: 
      show = Shows(
        venue_id = form.venue_id.data,
        artist_id = form.artist_id.data,
        start_time = form.start_time.data
      )
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')

    except():
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead. DONE
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#  ----------------------------------------------------------------
#  Launch.
#  ----------------------------------------------------------------

# Default port:
if __name__ == '__main__':
    app.run()
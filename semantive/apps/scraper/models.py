from semantive.libs.extensions import db


class Picture(db.Model):
    __tablename__ = 'picture'
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('url.id'))
    path = db.Column(db.String(300))


class Text(db.Model):
    __tablename__ = 'text'
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('url.id'))
    text = db.Column(db.String(4294000000))


class Url(db.Model):
    __tablename__ = 'url'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(300))
    images = db.relationship('Picture', backref=db.backref('url'), cascade="save-update, merge, delete")
    text = db.relationship('Text', backref=db.backref('url'), cascade="save-update, merge, delete")

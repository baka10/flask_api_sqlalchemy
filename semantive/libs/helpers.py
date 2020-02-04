import os
import re
import urllib
import urllib.parse
from dataclasses import dataclass
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from flask import current_app as app
from sqlalchemy import exc

from semantive.apps.scraper.models import Picture, Url, Text
from semantive.libs.extensions import db


@dataclass
class ParsedUrlData:
    text: Text
    picture: List[Picture]

    def save_to_db(self, database):
        database.session.add_all(self.picture)
        database.session.add(self.text)
        save_orm_to_db()


def parse_data_from_url(url_object: Url) -> ParsedUrlData:
    url = url_object.url
    user_agent = app.config.get("USER_AGENT")
    headers = {'User-Agent': user_agent}
    req = urllib.request.Request(url=url, headers=headers)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
    soup = BeautifulSoup(the_page, 'html.parser')
    return ParsedUrlData(text=parse_text_from_soup(soup), picture=get_list_of_pictures(soup))


def save_orm_to_db():
    try:
        db.session.commit()
    except exc.SQLAlchemyError as exception:
        db.session.rollback()
        raise exception


def parse_text_from_soup(soup: BeautifulSoup) -> Text:
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return Text(text='\n'.join(chunk for chunk in chunks if chunk))


def get_list_of_pictures(soup: BeautifulSoup, url_object: Url) -> List[Picture]:
    picture_list = find_picture_address_in_soup(soup)
    orm_list_of_pictures: List[Picture] = []

    for pic_link, pic_name in create_links_from_pictures(picture_list, url_object):
        img_raw = requests.get(pic_link, stream=True)
        with open(os.path.join(app.config.get("PICTURE_FOLDER"), url_object.url, pic_name), 'wb') as file:
            for part in img_raw.iter_content(chunk_size=1024):
                file.write(part)
            orm_list_of_pictures.append(
                Picture(path=os.path.relpath(file.name, app.config.get("")).encode("utf-8"), url=url_object))
    return orm_list_of_pictures


def find_picture_address_in_soup(soup: BeautifulSoup) -> List[str]:
    list_of_pictures: List[str] = []
    for link in soup.find_all('img'):
        if link.get('src'):
            list_of_pictures.append(link.get('src'))
        elif link.get('data-src'):
            list_of_pictures.append(link.get('data-src'))
    return list_of_pictures


def create_links_from_pictures(picture_list, url_object: Url) -> Tuple:
    picture_links = []
    for picture in picture_list:
        try:
            if img_src.startswith('//'):
                link = urllib.parse.urljoin("https:", img_src)
            elif img_src.startswith("http"):
                link = img_src
            else:
                link = urllib.parse.urljoin(url_object.url.rsplit('/', 1)[0], img_src)
            img_src, pic_name = re.match(r"(.*)?\/(.*\.(?:gif|png|jpg|jpeg))", picture).groups()
            picture_links.append((link, pic_name))
        except AttributeError:
            # We want to continue on fail
            continue
    return picture_links
